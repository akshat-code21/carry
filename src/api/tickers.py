"""Tickers API endpoints."""

from datetime import date, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from src.services.etf_mapping_service import ETFMappingService

from src.analytics.service import analytics
from src.api.deps import (
    get_aggregation_service,
    get_market_data,
    get_social_context_service,
)
from src.database import get_db
from src.models.performance import PerformanceRecord
from src.models.prediction import Prediction
from src.models.speaker_ticker import SpeakerTickerAggregation
from src.models.theme import ThemeHierarchy, ThemeTickerMapping
from src.models.video import Video
from src.schemas import (
    PerformanceResponse,
    PredictionWithPerformance,
    PricePointResponse,
    ThemeResponse,
    TickerDetailResponse,
    TickerResponse,
    TickerSentimentDailyPoint,
)
from src.services.aggregation_service import AggregationService
from src.services.interfaces import MarketDataSource
from src.services.social_context_service import SocialContextService

router = APIRouter(prefix="/api/tickers", tags=["Tickers"])

# Weighting for the blended YouTube + social sentiment score (-1..1 both).
YOUTUBE_SENTIMENT_WEIGHT = 0.6
SOCIAL_SENTIMENT_WEIGHT = 0.4


async def _attach_social(
    detail: TickerDetailResponse,
    social_service: SocialContextService | None,
) -> TickerDetailResponse:
    """Attach TickerFlow social-sentiment data and blended headline stats."""
    if social_service is None:
        return detail

    social = await social_service.get_ticker(detail.ticker)
    if social is None or not social.sources:
        return detail.model_copy(
            update={
                "social": social,
                "combined_avg_sentiment": detail.avg_sentiment,
                "social_mentions": 0,
            }
        )

    social_mentions_values = [s.mentions for s in social.sources if s.mentions is not None]
    social_mentions = sum(social_mentions_values) if social_mentions_values else 0
    social_sentiment = None
    if social.signal and social.signal.sentiment is not None:
        social_sentiment = social.signal.sentiment / 100.0

    if detail.avg_sentiment is not None and social_sentiment is not None:
        combined = (
            YOUTUBE_SENTIMENT_WEIGHT * detail.avg_sentiment
            + SOCIAL_SENTIMENT_WEIGHT * social_sentiment
        )
    elif social_sentiment is not None:
        combined = social_sentiment
    else:
        combined = detail.avg_sentiment

    return detail.model_copy(
        update={
            "social": social,
            "combined_avg_sentiment": round(combined, 4) if combined is not None else None,
            "social_mentions": social_mentions,
        }
    )


@router.get("", response_model=list[TickerResponse])
async def list_tickers(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TickerResponse]:
    """List all tracked tickers with aggregate stats.

    Aggregates across all channels so each ticker appears only once,
    with summed mentions and weighted average sentiment.
    """
    from sqlalchemy import func as sqlfunc

    from src.services.etf_mapping_service import ETFMappingService

    etf_service = ETFMappingService()

    # Group by ticker across all channels to produce one row per ticker
    stmt = (
        select(
            SpeakerTickerAggregation.ticker,
            sqlfunc.sum(SpeakerTickerAggregation.total_mentions).label("total_mentions"),
            sqlfunc.sum(SpeakerTickerAggregation.explicit_mentions).label("explicit_mentions"),
            sqlfunc.sum(SpeakerTickerAggregation.implicit_mentions).label("implicit_mentions"),
            sqlfunc.avg(SpeakerTickerAggregation.avg_sentiment).label("avg_sentiment"),
            sqlfunc.avg(SpeakerTickerAggregation.weighted_relevance).label("weighted_relevance"),
            sqlfunc.max(SpeakerTickerAggregation.last_mentioned_at).label("last_mentioned_at"),
        )
        .group_by(SpeakerTickerAggregation.ticker)
        .order_by(sqlfunc.sum(SpeakerTickerAggregation.total_mentions).desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        TickerResponse(
            ticker=row.ticker,
            total_mentions=row.total_mentions or 0,
            explicit_mentions=row.explicit_mentions or 0,
            implicit_mentions=row.implicit_mentions or 0,
            avg_sentiment=row.avg_sentiment,
            weighted_relevance=row.weighted_relevance,
            last_mentioned_at=row.last_mentioned_at,
            is_etf=etf_service.is_etf(row.ticker),
        )
        for row in rows
    ]


@router.get("/top-etfs")
async def get_top_etfs(
    limit: int = Query(default=10, ge=1, le=50),
    aggregation: AggregationService = Depends(get_aggregation_service),
) -> list[dict]:
    """Get top sector/industry ETFs mentioned across processed videos."""
    return await aggregation.get_top_etfs(limit=limit)


@router.get("/{ticker}", response_model=TickerDetailResponse)
async def get_ticker_detail(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    social_service: SocialContextService | None = Depends(get_social_context_service),
) -> TickerDetailResponse:
    """Get detailed info for a ticker: predictions, themes, performance.

    For ETF tickers (e.g., SMH), reverse-looks up the related themes and
    pulls predictions from the constituent stocks of those themes.
    """
    from src.services.etf_mapping_service import ETFMappingService

    ticker = ticker.upper()
    etf_service = ETFMappingService()
    is_etf = etf_service.is_etf(ticker)

    analytics.record_event(
        "ticker_viewed",
        payload={"ticker": ticker, "is_etf": is_etf},
        counters={"ticker_views": 1},
    )

    if is_etf:
        etf_detail = await _get_etf_ticker_detail(ticker, db, etf_service)
        return await _attach_social(etf_detail, social_service)

    # --- Standard stock detail (existing logic) ---

    # Get aggregation stats
    agg_result = await db.execute(
        select(SpeakerTickerAggregation).where(SpeakerTickerAggregation.ticker == ticker)
    )
    # Use first match (could be from multiple channels)
    agg = agg_result.scalars().first()

    # Get predictions for this ticker with video and channel info
    pred_result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.video).selectinload(Video.channel))
        .where(Prediction.ticker == ticker)
        .order_by(Prediction.created_at.desc())
    )
    predictions = pred_result.scalars().all()

    # Get performance for each prediction
    preds_with_perf = []
    for pred in predictions:
        pwp = PredictionWithPerformance.model_validate(pred)
        if pred.video:
            pwp.video_title = pred.video.title
            pwp.youtube_video_id = pred.video.youtube_video_id
            pwp.published_at = pred.video.published_at
            if pred.video.channel:
                pwp.channel_title = pred.video.channel.title

        perf_result = await db.execute(
            select(PerformanceRecord).where(PerformanceRecord.prediction_id == pred.id)
        )
        perf = perf_result.scalar_one_or_none()
        if perf:
            pwp.performance = PerformanceResponse.model_validate(perf)
        preds_with_perf.append(pwp)

    # Get themes associated with this ticker
    mapping_result = await db.execute(
        select(ThemeTickerMapping).where(ThemeTickerMapping.ticker == ticker)
    )
    mappings = mapping_result.scalars().all()

    theme_ids = [m.theme_id for m in mappings]
    themes = []
    if theme_ids:
        theme_result = await db.execute(
            select(ThemeHierarchy).where(ThemeHierarchy.id.in_(theme_ids))
        )
        themes = [ThemeResponse.model_validate(t) for t in theme_result.scalars().all()]

    detail = TickerDetailResponse(
        ticker=ticker,
        total_mentions=agg.total_mentions if agg else 0,
        explicit_mentions=agg.explicit_mentions if agg else 0,
        implicit_mentions=agg.implicit_mentions if agg else 0,
        avg_sentiment=agg.avg_sentiment if agg else None,
        weighted_relevance=agg.weighted_relevance if agg else None,
        last_mentioned_at=agg.last_mentioned_at if agg else None,
        predictions=preds_with_perf,
        themes=themes,
    )
    return await _attach_social(detail, social_service)


async def _get_etf_ticker_detail(
    etf_ticker: str,
    db: AsyncSession,
    etf_service: "ETFMappingService",
) -> TickerDetailResponse:
    """Build ticker detail for an ETF by aggregating data from constituent stocks."""
    from sqlalchemy import func

    # Reverse lookup: which themes map to this ETF?
    related_theme_names = etf_service.get_themes_for_etf(etf_ticker)

    # Find those themes in the DB
    themes = []
    constituent_tickers: list[str] = []
    if related_theme_names:
        theme_result = await db.execute(
            select(ThemeHierarchy).where(
                func.lower(ThemeHierarchy.name).in_([n.lower() for n in related_theme_names])
            )
        )
        themes_db = theme_result.scalars().all()
        themes = [ThemeResponse.model_validate(t) for t in themes_db]
        theme_ids = [t.id for t in themes_db]

        # Get constituent tickers from these themes
        if theme_ids:
            ticker_result = await db.execute(
                select(ThemeTickerMapping.ticker)
                .where(ThemeTickerMapping.theme_id.in_(theme_ids))
                .distinct()
            )
            constituent_tickers = [row[0].upper() for row in ticker_result.all()]

    # Get predictions for all constituent tickers
    preds_with_perf = []
    if constituent_tickers:
        pred_result = await db.execute(
            select(Prediction)
            .options(selectinload(Prediction.video).selectinload(Video.channel))
            .where(Prediction.ticker.in_(constituent_tickers))
            .order_by(Prediction.created_at.desc())
        )
        predictions = pred_result.scalars().all()

        for pred in predictions:
            pwp = PredictionWithPerformance.model_validate(pred)
            if pred.video:
                pwp.video_title = pred.video.title
                pwp.youtube_video_id = pred.video.youtube_video_id
                pwp.published_at = pred.video.published_at
                if pred.video.channel:
                    pwp.channel_title = pred.video.channel.title

            perf_result = await db.execute(
                select(PerformanceRecord).where(PerformanceRecord.prediction_id == pred.id)
            )
            perf = perf_result.scalar_one_or_none()
            if perf:
                pwp.performance = PerformanceResponse.model_validate(perf)
            preds_with_perf.append(pwp)

    # Get aggregation stats for constituent tickers
    total_mentions = 0
    avg_sentiment = None
    if constituent_tickers:
        agg_result = await db.execute(
            select(SpeakerTickerAggregation).where(
                SpeakerTickerAggregation.ticker.in_(constituent_tickers)
            )
        )
        aggregations = agg_result.scalars().all()
        total_mentions = sum(a.total_mentions or 0 for a in aggregations)
        sentiments = [a.avg_sentiment for a in aggregations if a.avg_sentiment is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None

    return TickerDetailResponse(
        ticker=etf_ticker,
        total_mentions=total_mentions,
        explicit_mentions=0,
        implicit_mentions=total_mentions,
        avg_sentiment=avg_sentiment,
        weighted_relevance=None,
        last_mentioned_at=None,
        predictions=preds_with_perf,
        themes=themes,
    )


@router.get(
    "/{ticker}/sentiment-timeline",
    response_model=list[TickerSentimentDailyPoint],
)
async def get_ticker_sentiment_timeline(
    ticker: str,
    days: int | None = Query(default=None, ge=1, le=3650),
    agg_service: AggregationService = Depends(get_aggregation_service),
) -> list[TickerSentimentDailyPoint]:
    """Get daily bullish vs bearish (vs neutral) mention counts for a ticker.

    Counts both explicit mentions (predictions tagged with this ticker) and
    implicit mentions (theme mentions mapped to this ticker), bucketed by
    the calendar date of the mentioning video. Pass `days` to limit to a
    recent window (e.g. `?days=30`); omit it to get the full history.
    """
    data = await agg_service.get_ticker_daily_sentiment(ticker, days=days)
    return [TickerSentimentDailyPoint(**point) for point in data]


@router.get(
    "/{ticker}/price-history",
    response_model=list[PricePointResponse],
)
async def get_ticker_price_history(
    ticker: str,
    days: int = Query(default=180, ge=1, le=3650),
    market_data: MarketDataSource = Depends(get_market_data),
) -> list[PricePointResponse]:
    """Get daily OHLCV price history for a ticker over the trailing `days`.

    Used to overlay bullish/bearish mention markers on a real price chart.
    """
    ticker = ticker.upper()
    end = date.today()
    start = end - timedelta(days=days)
    points = await market_data.get_price_history(ticker, start, end)
    return [
        PricePointResponse(
            date=p.date.isoformat(),
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close,
            volume=p.volume,
        )
        for p in points
    ]

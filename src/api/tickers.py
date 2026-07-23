"""Tickers API endpoints."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_aggregation_service, get_market_data
from src.database import get_db
from src.models.performance import PerformanceRecord
from src.models.prediction import Prediction
from src.models.speaker_ticker import SpeakerTickerAggregation
from src.models.theme import ThemeHierarchy, ThemeTickerMapping
from src.schemas import (
    PerformanceResponse,
    PredictionResponse,
    PredictionWithPerformance,
    PricePointResponse,
    ThemeResponse,
    TickerDetailResponse,
    TickerResponse,
    TickerSentimentDailyPoint,
)
from src.services.aggregation_service import AggregationService
from src.services.interfaces import MarketDataSource

router = APIRouter(prefix="/api/tickers", tags=["Tickers"])


@router.get("", response_model=list[TickerResponse])
async def list_tickers(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[TickerResponse]:
    """List all tracked tickers with aggregate stats."""
    result = await db.execute(
        select(SpeakerTickerAggregation)
        .order_by(SpeakerTickerAggregation.total_mentions.desc())
        .limit(limit)
        .offset(offset)
    )
    aggregations = result.scalars().all()
    return [TickerResponse.model_validate(a) for a in aggregations]


@router.get("/{ticker}", response_model=TickerDetailResponse)
async def get_ticker_detail(
    ticker: str,
    db: AsyncSession = Depends(get_db),
) -> TickerDetailResponse:
    """Get detailed info for a ticker: predictions, themes, performance."""
    ticker = ticker.upper()

    # Get aggregation stats
    agg_result = await db.execute(
        select(SpeakerTickerAggregation).where(
            SpeakerTickerAggregation.ticker == ticker
        )
    )
    # Use first match (could be from multiple channels)
    agg = agg_result.scalars().first()

    # Get predictions for this ticker
    pred_result = await db.execute(
        select(Prediction)
        .where(Prediction.ticker == ticker)
        .order_by(Prediction.created_at.desc())
    )
    predictions = pred_result.scalars().all()

    # Get performance for each prediction
    preds_with_perf = []
    for pred in predictions:
        pwp = PredictionWithPerformance.model_validate(pred)
        perf_result = await db.execute(
            select(PerformanceRecord).where(
                PerformanceRecord.prediction_id == pred.id
            )
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

    return TickerDetailResponse(
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

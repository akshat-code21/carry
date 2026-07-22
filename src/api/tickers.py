"""Tickers API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.models.performance import PerformanceRecord
from src.models.prediction import Prediction
from src.models.video import Video
from src.models.speaker_ticker import SpeakerTickerAggregation
from src.models.theme import ThemeHierarchy, ThemeTickerMapping
from src.schemas import (
    PerformanceResponse,
    PredictionResponse,
    PredictionWithPerformance,
    ThemeResponse,
    TickerDetailResponse,
    TickerResponse,
)

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

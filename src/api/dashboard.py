"""Aggregated dashboard summary endpoint.

Returns all data the dashboard page needs in a single request, replacing
the previous 5-way fan-out from the frontend. Runs queries concurrently
via asyncio.gather for minimal latency.
"""

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_aggregation_service
from src.database import get_db
from src.models.channel import Channel
from src.models.speaker_ticker import SpeakerTickerAggregation
from src.models.theme import ThemeHierarchy
from src.models.video import Video
from src.schemas import ChannelResponse, VideoResponse
from src.services.aggregation_service import AggregationService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

_CACHE_HEADERS = {"Cache-Control": "public, max-age=30"}


async def _fetch_tickers(db: AsyncSession) -> list[dict]:
    """Inline ticker aggregation query (mirrors GET /api/tickers)."""
    from src.services.etf_mapping_service import ETFMappingService

    etf_service = ETFMappingService()

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
        .limit(50)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "ticker": row.ticker,
            "total_mentions": row.total_mentions or 0,
            "explicit_mentions": row.explicit_mentions or 0,
            "implicit_mentions": row.implicit_mentions or 0,
            "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else None,
            "weighted_relevance": float(row.weighted_relevance) if row.weighted_relevance else None,
            "last_mentioned_at": row.last_mentioned_at.isoformat() if row.last_mentioned_at else None,
            "is_etf": etf_service.is_etf(row.ticker),
        }
        for row in rows
    ]


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    aggregation: AggregationService = Depends(get_aggregation_service),
) -> JSONResponse:
    """Single aggregated endpoint for the dashboard page.

    Replaces 5 separate API calls (videos, channels, tickers, top-etfs, themes)
    with one request using concurrent queries. Expected latency: ~50ms with
    co-located DB.
    """
    # Run all queries concurrently — same session, different coroutines
    video_counts_subq = (
        select(Video.channel_id, sqlfunc.count(Video.id).label("video_count"))
        .where(Video.duration_sec > 60)
        .group_by(Video.channel_id)
        .subquery()
    )

    (
        total_videos,
        videos_result,
        channels_result,
        tickers_data,
        etfs_data,
        theme_counts_result,
    ) = await asyncio.gather(
        db.scalar(
            select(sqlfunc.count(Video.id))
            .where(Video.duration_sec > 60)
        ),
        db.execute(
            select(Video)
            .where(Video.duration_sec > 60)
            .order_by(Video.published_at.desc())
            .limit(20)
        ),
        db.execute(
            select(Channel, sqlfunc.coalesce(video_counts_subq.c.video_count, 0).label("video_count"))
            .outerjoin(video_counts_subq, Channel.id == video_counts_subq.c.channel_id)
            .order_by(Channel.created_at.desc())
        ),
        _fetch_tickers(db),
        aggregation.get_top_etfs(limit=8),
        db.execute(
            select(ThemeHierarchy.level, sqlfunc.count())
            .group_by(ThemeHierarchy.level)
        ),
    )

    videos = [
        VideoResponse.model_validate(v).model_dump(mode="json")
        for v in videos_result.scalars().all()
    ]
    channels = []
    for c, count in channels_result.all():
        resp = ChannelResponse.model_validate(c)
        resp.video_count = count
        channels.append(resp.model_dump(mode="json"))

    theme_counts = dict(theme_counts_result.all())

    return JSONResponse(
        content={
            "total_videos": total_videos or 0,
            "videos": videos,
            "channels": channels,
            "tickers": tickers_data,
            "etfs": etfs_data,
            "theme_counts": {
                "sectors": theme_counts.get("sector", 0),
                "industries": theme_counts.get("industry", 0),
                "themes": theme_counts.get("theme", 0),
                "narratives": theme_counts.get("narrative", 0),
            },
        },
        headers=_CACHE_HEADERS,
    )

"""Usage analytics endpoints - client event ingest and personal usage summary."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import analytics
from src.auth.dependencies import get_current_user, require_admin
from src.database import get_db
from src.models.analytics import DailyUserUsage, UsageEvent
from src.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage", tags=["Usage"])


class ClientEvent(BaseModel):
    """A single frontend-tracked event (page views, feature clicks...)."""

    type: str = Field(min_length=1, max_length=64)
    data: dict = Field(default_factory=dict)


class ClientEventBatch(BaseModel):
    events: list[ClientEvent] = Field(max_length=25)


class UsageSummaryPoint(BaseModel):
    day: str
    api_calls: int = 0
    searches: int = 0
    search_zero_results: int = 0
    page_views: int = 0
    video_views: int = 0
    channel_views: int = 0
    theme_views: int = 0
    ticker_views: int = 0
    expensive_ops: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0


class TopQueryItem(BaseModel):
    query: str
    count: int


class MyUsageResponse(BaseModel):
    totals: dict
    daily: list[UsageSummaryPoint]
    top_queries: list[TopQueryItem]
    recent_events: list[dict]


@router.post("/events", status_code=202)
async def ingest_client_events(
    batch: ClientEventBatch,
    request_user: User = Depends(get_current_user),
) -> dict:
    """Ingest frontend analytics events (page views, feature engagement).

    Events are attributed to the authenticated user; unknown types are kept
    as-is so the frontend can evolve without backend changes.
    """
    for event in batch.events:
        counters = {"page_views": 1} if event.type == "page_viewed" else None
        analytics.record_event(
            event.type,
            payload=event.data,
            counters=counters,
        )
    return {"accepted": len(batch.events)}


@router.get("/me", response_model=MyUsageResponse)
async def get_my_usage(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MyUsageResponse:
    """Usage dashboard data (admin-only feature in the UI)."""
    since = datetime.now(UTC).date() - timedelta(days=days - 1)

    # Daily rollup series
    rows = (
        (
            await db.execute(
                select(DailyUserUsage)
                .where(DailyUserUsage.user_id == user.id, DailyUserUsage.day >= since)
                .order_by(DailyUserUsage.day)
            )
        )
        .scalars()
        .all()
    )

    counter_cols = [
        c
        for c in DailyUserUsage.__table__.columns.keys()
        if c not in ("day", "user_id", "updated_at")
    ]
    daily_points = [
        UsageSummaryPoint(day=str(r.day), **{c: getattr(r, c) or 0 for c in counter_cols})
        for r in rows
    ]

    # Lifetime totals from rollups
    totals_rows = (
        (await db.execute(select(DailyUserUsage).where(DailyUserUsage.user_id == user.id)))
        .scalars()
        .all()
    )
    totals = {c: sum(getattr(r, c) or 0 for r in totals_rows) for c in counter_cols}
    totals["member_since"] = str(user.created_at.date()) if user.created_at else None
    totals["last_seen_at"] = user.last_seen_at.isoformat() if user.last_seen_at else None

    # Top queries (last `days` days of search events)
    top_query_rows = (
        await db.execute(
            select(
                func.lower(func.left(UsageEvent.payload["query"].as_string(), 120)).label("q"),
                func.count().label("n"),
            )
            .where(
                UsageEvent.user_id == user.id,
                UsageEvent.event_type == "search_performed",
                UsageEvent.created_at >= datetime.now(UTC) - timedelta(days=days),
            )
            .group_by("q")
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()
    top_queries = [TopQueryItem(query=row.q or "", count=row.n) for row in top_query_rows if row.q]

    # Recent notable events (excluding noisy page views)
    recent_rows = (
        (
            await db.execute(
                select(UsageEvent)
                .where(
                    UsageEvent.user_id == user.id,
                    UsageEvent.event_type != "page_viewed",
                )
                .order_by(UsageEvent.created_at.desc())
                .limit(15)
            )
        )
        .scalars()
        .all()
    )
    recent_events = [
        {
            "type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in recent_rows
    ]

    return MyUsageResponse(
        totals=totals,
        daily=daily_points,
        top_queries=top_queries,
        recent_events=recent_events,
    )

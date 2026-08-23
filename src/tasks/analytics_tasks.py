"""Celery tasks for analytics maintenance.

- retention_cleanup: prune raw analytics rows older than the configured
  retention window (daily rollups are kept forever).
- aggregate_platform_daily: recompute exact platform stats for the previous
  day, including distinct active users.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.tasks import celery_app

logger = logging.getLogger(__name__)


async def _retention_cleanup() -> dict:
    from src.config import get_settings
    from src.database import async_session_factory
    from src.models.analytics import ApiRequestLog, LlmUsageLog, UsageEvent

    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.analytics_retention_days)

    deleted: dict[str, int] = {}
    async with async_session_factory() as session:
        for model in (UsageEvent, ApiRequestLog, LlmUsageLog):
            result = await session.execute(delete(model).where(model.created_at < cutoff))
            deleted[model.__tablename__] = result.rowcount or 0
        await session.commit()

    total = sum(deleted.values())
    logger.info("Analytics retention cleanup removed %s rows older than %s", total, cutoff)
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}


@celery_app.task(name="analytics.retention_cleanup")
def retention_cleanup() -> dict:
    """Delete raw usage/request/LLM rows beyond the retention window."""
    return asyncio.run(_retention_cleanup())


async def _aggregate_platform_daily() -> dict:
    """Rebuild yesterday's PlatformDailyUsage row with exact numbers."""
    from src.database import async_session_factory
    from src.models.analytics import ApiRequestLog, PlatformDailyUsage

    yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
    day_start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    # Real-time counters already track searches/pages/etc.; recompute api_calls
    # and active_users exactly from request logs.
    async with async_session_factory() as session:
        stats = (
            await session.execute(
                select(
                    func.count().label("api_calls"),
                    func.count(func.distinct(ApiRequestLog.user_id)).label("active_users"),
                ).where(
                    ApiRequestLog.created_at >= day_start,
                    ApiRequestLog.created_at < day_end,
                )
            )
        ).one()

        stmt = (
            pg_insert(PlatformDailyUsage)
            .values(
                day=yesterday,
                api_calls=stats.api_calls or 0,
                active_users=stats.active_users or 0,
            )
            .on_conflict_do_update(
                index_elements=["day"],
                set_={
                    "api_calls": stats.api_calls or 0,
                    "active_users": stats.active_users or 0,
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    logger.info(
        "Aggregated platform usage for %s: %s api calls, %s active users",
        yesterday,
        stats.api_calls,
        stats.active_users,
    )
    return {"day": str(yesterday), "api_calls": stats.api_calls, "active_users": stats.active_users}


@celery_app.task(name="analytics.aggregate_platform_daily")
def aggregate_platform_daily() -> dict:
    """Compute exact platform-wide daily stats for the completed UTC day."""
    return asyncio.run(_aggregate_platform_daily())

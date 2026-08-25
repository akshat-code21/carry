"""Usage analytics service.

Fire-and-forget writers for raw events, API request logs and LLM cost rows,
plus atomic daily-rollup maintenance. Every method swallows exceptions so
analytics can never break a user-facing request. Each call opens its own
short-lived DB session (independent of the request's session).
"""

import logging
import uuid
from contextvars import ContextVar
from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import async_session_factory
from src.models.analytics import (
    ApiRequestLog,
    DailyUserUsage,
    LlmUsageLog,
    PlatformDailyUsage,
    UsageEvent,
)

logger = logging.getLogger(__name__)

# Set by the auth dependency so deep service layers (LLM calls etc.) can
# attribute their usage to the requesting user without explicit plumbing.
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)

# Counters on DailyUserUsage that can be bumped incrementally
_USER_COUNTER_COLUMNS = (
    "searches",
    "search_zero_results",
    "page_views",
    "video_views",
    "channel_views",
    "theme_views",
    "ticker_views",
    "expensive_ops",
    "llm_input_tokens",
    "llm_output_tokens",
)

_PLATFORM_COUNTER_COLUMNS = (
    "searches",
    "search_zero_results",
    "page_views",
    "expensive_ops",
    "llm_input_tokens",
    "llm_output_tokens",
)


def _utc_today() -> date:
    return datetime.now(UTC).date()


class AnalyticsService:
    """Thin wrapper around fire-safe analytics writes."""

    def __init__(self, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = get_settings().analytics_enabled
        self.enabled = enabled
        self._pending: set = set()

    async def flush(self) -> None:
        """Await all pending background writes (used by tests/shutdown)."""
        import asyncio

        if self._pending:
            await asyncio.gather(*self._pending, return_exceptions=True)
        self._pending.clear()

    # ── Core writer ──────────────────────────────────────────────────────

    async def _write(self, *rows, bumps: dict | None = None) -> None:
        """Persist rows + rollup bumps in one transaction. Never raises."""
        if not self.enabled or (not rows and not bumps):
            return
        try:
            async with async_session_factory() as session:  # type: AsyncSession
                for row in rows:
                    session.add(row)
                if bumps:
                    await self._apply_bumps(session, bumps)
                await session.commit()
        except Exception:
            logger.warning("Analytics write failed", exc_info=True)

    @staticmethod
    async def _apply_bumps(session: AsyncSession, bumps: dict) -> None:
        """Upsert per-user and platform daily counters."""
        user_id = bumps.get("user_id")
        day = bumps.get("day") or _utc_today()
        counters: dict[str, int] = bumps.get("counters") or {}
        nonzero = {k: v for k, v in counters.items() if v}

        if not nonzero or not isinstance(user_id, uuid.UUID):
            return

        # Per-user rollup
        values: dict = {"day": day, "user_id": user_id}
        values.update(nonzero)
        stmt = pg_insert(DailyUserUsage).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["day", "user_id"],
            set_={col: getattr(DailyUserUsage, col) + stmt.excluded[col] for col in nonzero},
            # updated_at handled by onupdate
        )
        await session.execute(stmt)

        # Platform-wide rollup (subset of columns exist there)
        platform_values = {"day": day}
        for col in nonzero:
            if col in _PLATFORM_COUNTER_COLUMNS:
                platform_values[col] = nonzero[col]
        if len(platform_values) > 1:
            p_stmt = pg_insert(PlatformDailyUsage).values(**platform_values)
            p_stmt = p_stmt.on_conflict_do_update(
                index_elements=["day"],
                set_={
                    col: getattr(PlatformDailyUsage, col) + p_stmt.excluded[col]
                    for col in platform_values
                    if col != "day"
                },
            )
            await session.execute(p_stmt)

    # ── Public API ───────────────────────────────────────────────────────

    def record_event(
        self,
        event_type: str,
        *,
        user_id: uuid.UUID | str | None = None,
        source: str = "user",
        payload: dict | None = None,
        counters: dict[str, int] | None = None,
        commit: bool = False,
    ) -> None:
        """Record a product-analytics event (+ optional rollup bumps).

        ``commit=True`` makes this synchronous-ish via a background task;
        otherwise callers pass their own session-based flow. Kept simple and
        non-blocking by scheduling the write immediately.
        """
        if not self.enabled:
            return
        if user_id is None:
            user_id = current_user_id.get()
        uid = None
        if isinstance(user_id, str):
            try:
                uid = uuid.UUID(user_id)
            except ValueError:
                uid = None
        elif isinstance(user_id, uuid.UUID):
            uid = user_id

        row = UsageEvent(
            event_type=event_type,
            user_id=uid,
            source=source,
            payload=payload or {},
        )
        bumps = (
            {"user_id": uid, "day": _utc_today(), "counters": counters}
            if counters and uid
            else None
        )
        self._schedule(self._write(row, bumps=bumps))

    def record_api_request(
        self,
        *,
        user_id: str | uuid.UUID | None,
        method: str,
        path: str,
        route_template: str | None,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Record one served HTTP request (+ ``api_calls`` rollup bump)."""
        if not self.enabled:
            return
        uid = None
        if isinstance(user_id, str):
            try:
                uid = uuid.UUID(user_id)
            except ValueError:
                uid = None
        elif isinstance(user_id, uuid.UUID):
            uid = user_id

        row = ApiRequestLog(
            user_id=uid,
            method=method,
            path=path[:512],
            route_template=route_template[:512] if route_template else None,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        bumps = (
            {
                "user_id": uid,
                "day": _utc_today(),
                "counters": {"api_calls": 1},
            }
            if uid
            else None
        )
        self._schedule(self._write(row, bumps=bumps))

    def record_llm_usage(
        self,
        *,
        provider: str,
        model: str,
        purpose: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float | None = None,
        success: bool = True,
        error_summary: str | None = None,
        user_id: str | uuid.UUID | None = None,
    ) -> None:
        """Record one LLM/embedding call in the cost ledger (+ token rollups).

        When ``user_id`` is omitted, falls back to the request's user via
        the ``current_user_id`` context var (set by auth dependency).
        """
        if not self.enabled:
            return
        if user_id is None:
            user_id = current_user_id.get()
        uid = None
        if isinstance(user_id, str):
            try:
                uid = uuid.UUID(user_id)
            except ValueError:
                uid = None
        elif isinstance(user_id, uuid.UUID):
            uid = user_id

        row = LlmUsageLog(
            user_id=uid,
            provider=provider,
            model=model,
            purpose=purpose,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            success=success,
            error_summary=error_summary[:2000] if error_summary else None,
        )
        bumps = (
            {
                "user_id": uid,
                "day": _utc_today(),
                "counters": {
                    "llm_input_tokens": input_tokens,
                    "llm_output_tokens": output_tokens,
                },
            }
            if uid
            else None
        )
        self._schedule(self._write(row, bumps=bumps))

    def record_new_user(self, user_id: str | uuid.UUID) -> None:
        """Count a freshly provisioned account in today's platform stats."""
        if not self.enabled:
            return

        async def _bump_new_user() -> None:
            try:
                async with async_session_factory() as session:
                    stmt = pg_insert(PlatformDailyUsage).values(day=_utc_today(), new_users=1)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["day"],
                        set_={"new_users": PlatformDailyUsage.new_users + 1},
                    )
                    await session.execute(stmt)
                    await session.commit()
            except Exception:
                logger.warning("Analytics new-user bump failed", exc_info=True)

        self._schedule(_bump_new_user())

    # ── Scheduling ───────────────────────────────────────────────────────

    def _schedule(self, coro) -> None:
        """Schedule the coroutine on the running loop without awaiting it."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("No running loop; dropping analytics write")
            if hasattr(coro, "close"):
                coro.close()
            return
        task = loop.create_task(coro)
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)
        # Swallow-and-log any late failure so tasks never surface warnings
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)


# Process-wide singleton
analytics = AnalyticsService()

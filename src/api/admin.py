"""Admin endpoints — invite management and platform-wide usage metrics."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.auth.service import create_invite as create_invite_service
from src.database import get_db
from src.models.analytics import DailyUserUsage
from src.models.user import Invite, User, UserStatus
from src.schemas import UserProfileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


# ── Schemas ──────────────────────────────────────────────────────────────


class CreateInviteRequest(BaseModel):
    invited_email: EmailStr | None = None
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class InviteResponse(BaseModel):
    id: str
    code: str
    invited_email: str | None
    max_uses: int
    uses_count: int
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime

    @classmethod
    def from_invite(cls, inv: Invite) -> "InviteResponse":
        return cls(
            id=str(inv.id),
            code=inv.code,
            invited_email=inv.invited_email,
            max_uses=inv.max_uses,
            uses_count=inv.uses_count,
            expires_at=inv.expires_at,
            revoked_at=inv.revoked_at,
            created_at=inv.created_at,
        )


class InviteLinkResponse(InviteResponse):
    # Convenience: the frontend can build a one-click signup URL with this.
    signup_url: str | None = None


# ── Invites ──────────────────────────────────────────────────────────────


@router.post("/invites")
async def create_invite(
    body: CreateInviteRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> InviteLinkResponse:
    """Create an invite code. Bind to an email to restrict redemption."""
    invite = await create_invite_service(
        db,
        created_by_user_id=admin.id,
        invited_email=str(body.invited_email) if body.invited_email else None,
        max_uses=body.max_uses,
        expires_in_days=body.expires_in_days,
    )
    return InviteLinkResponse.from_invite(invite)


@router.get("/invites", response_model=list[InviteLinkResponse])
async def list_invites(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[InviteLinkResponse]:
    result = await db.execute(select(Invite).order_by(desc(Invite.created_at)).limit(200))
    return [InviteLinkResponse.from_invite(i) for i in result.scalars().all()]


@router.delete("/invites/{invite_id}")
async def revoke_invite(
    invite_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    result = await db.execute(
        update(Invite).where(Invite.id == invite_id).values(revoked_at=datetime.now(UTC))
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Invite not found")
    return {"ok": True}


# ── Platform metrics ─────────────────────────────────────────────────────


class PlatformOverviewResponse(BaseModel):
    users: dict
    activity: dict
    searches: dict
    llm: dict
    daily_active: list[dict]
    top_users: list[dict]
    top_queries: list[dict]
    top_features: list[dict]


@router.get("/metrics/overview")
async def get_platform_overview(
    days: int = 30,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Platform-wide usage snapshot for the admin dashboard.

    Includes user counts, DAU/WAU/MAU, search stats, LLM token spend and
    top users/queries/features over the trailing ``days`` window.
    """
    now = datetime.now(UTC)

    total_users = await db.scalar(select(func.count()).select_from(User))
    active_users = await db.scalar(
        select(func.count()).select_from(User).where(User.status == UserStatus.ACTIVE)
    )
    pending_users = await db.scalar(
        select(func.count()).select_from(User).where(User.status == UserStatus.PENDING_INVITE)
    )

    since_date = now.date() - timedelta(days=days - 1)
    dau = await db.scalar(
        select(func.count(func.distinct(DailyUserUsage.user_id))).where(
            DailyUserUsage.day == now.date()
        )
    )
    wau = await db.scalar(
        select(func.count(func.distinct(DailyUserUsage.user_id))).where(
            DailyUserUsage.day >= now.date() - timedelta(days=6)
        )
    )
    mau = await db.scalar(
        select(func.count(func.distinct(DailyUserUsage.user_id))).where(
            DailyUserUsage.day >= now.date() - timedelta(days=29)
        )
    )

    # Windowed aggregates from rollups
    agg_rows = (
        (await db.execute(select(DailyUserUsage).where(DailyUserUsage.day >= since_date)))
        .scalars()
        .all()
    )
    window_searches = sum(r.searches or 0 for r in agg_rows)
    window_zero = sum(r.search_zero_results or 0 for r in agg_rows)
    window_api_calls = sum(r.api_calls or 0 for r in agg_rows)
    window_expensive = sum(r.expensive_ops or 0 for r in agg_rows)
    window_in_tokens = sum(r.llm_input_tokens or 0 for r in agg_rows)
    window_out_tokens = sum(r.llm_output_tokens or 0 for r in agg_rows)

    # Daily active series
    daily_rows = (
        await db.execute(
            select(
                DailyUserUsage.day,
                func.count(func.distinct(DailyUserUsage.user_id)).label("users"),
                func.sum(DailyUserUsage.searches).label("searches"),
            )
            .where(DailyUserUsage.day >= since_date)
            .group_by(DailyUserUsage.day)
            .order_by(DailyUserUsage.day)
        )
    ).all()

    # Top users by activity in window
    top_user_rows = (
        await db.execute(
            select(
                User.id,
                User.email,
                User.full_name,
                func.sum(DailyUserUsage.api_calls).label("api_calls"),
                func.sum(DailyUserUsage.searches).label("searches"),
                func.max(DailyUserUsage.updated_at).label("last_active"),
            )
            .join(DailyUserUsage, DailyUserUsage.user_id == User.id)
            .where(DailyUserUsage.day >= since_date)
            .group_by(User.id, User.email, User.full_name)
            .order_by(func.sum(DailyUserUsage.api_calls).desc())
            .limit(10)
        )
    ).all()

    # Top queries across all users
    from src.models.analytics import UsageEvent

    top_query_rows = (
        await db.execute(
            select(
                func.lower(func.left(UsageEvent.payload["query"].as_string(), 120)).label("q"),
                func.count().label("n"),
            )
            .where(
                UsageEvent.event_type == "search_performed",
                UsageEvent.created_at >= now - timedelta(days=days),
            )
            .group_by("q")
            .order_by(func.count().desc())
            .limit(10)
        )
    ).all()

    # Feature adoption via page views
    top_feature_rows = (
        await db.execute(
            select(
                func.coalesce(UsageEvent.payload["route"].as_string(), "/").label("route"),
                func.count().label("n"),
            )
            .where(
                UsageEvent.event_type == "page_viewed",
                UsageEvent.created_at >= now - timedelta(days=days),
            )
            .group_by("route")
            .order_by(func.count().desc())
            .limit(12)
        )
    ).all()

    return {
        "users": {
            "total": total_users or 0,
            "active": active_users or 0,
            "pending_invite": pending_users or 0,
            "dau": dau or 0,
            "wau": wau or 0,
            "mau": mau or 0,
        },
        "activity": {
            "window_days": days,
            "api_calls": window_api_calls,
            "expensive_ops": window_expensive,
        },
        "searches": {
            "total": window_searches,
            "zero_results": window_zero,
            "zero_result_rate": round(window_zero / window_searches, 3) if window_searches else 0.0,
        },
        "llm": {
            "input_tokens": window_in_tokens,
            "output_tokens": window_out_tokens,
        },
        "daily_active": [
            {"day": str(r.day), "users": r.users, "searches": r.searches or 0} for r in daily_rows
        ],
        "top_users": [
            {
                "id": str(r.id),
                "email": r.email,
                "full_name": r.full_name,
                "api_calls": r.api_calls or 0,
                "searches": r.searches or 0,
                "last_active": r.last_active.isoformat() if r.last_active else None,
            }
            for r in top_user_rows
        ],
        "top_queries": [{"query": r.q, "count": r.n} for r in top_query_rows if r.q],
        "top_features": [{"route": r.route, "views": r.n} for r in top_feature_rows],
    }


@router.get("/users", response_model=list[UserProfileResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserProfileResponse]:
    result = await db.execute(select(User).order_by(desc(User.created_at)).limit(500))
    return [UserProfileResponse.model_validate(u) for u in result.scalars().all()]

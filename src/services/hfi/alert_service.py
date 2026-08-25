"""Alert service — CRUD + rule-based scoring for HFI alerts."""

import uuid

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.hfi_alert import HfiAlert


async def list_alerts(
    db: AsyncSession,
    user_id: uuid.UUID,
    investor_id: uuid.UUID | None = None,
    severity: str | None = None,
    unread_only: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[HfiAlert], int, int]:
    q = select(HfiAlert).where(HfiAlert.user_id == user_id)
    count_q = select(func.count()).select_from(HfiAlert).where(HfiAlert.user_id == user_id)
    unread_q = (
        select(func.count())
        .select_from(HfiAlert)
        .where(HfiAlert.user_id == user_id, HfiAlert.is_read == False)  # noqa: E712
    )

    if investor_id:
        q = q.where(HfiAlert.investor_id == investor_id)
        count_q = count_q.where(HfiAlert.investor_id == investor_id)
    if severity:
        q = q.where(HfiAlert.severity == severity)
        count_q = count_q.where(HfiAlert.severity == severity)
    if unread_only:
        q = q.where(HfiAlert.is_read == False)  # noqa: E712
        count_q = count_q.where(HfiAlert.is_read == False)  # noqa: E712

    total = (await db.execute(count_q)).scalar_one()
    unread_count = (await db.execute(unread_q)).scalar_one()
    q = q.order_by(desc(HfiAlert.created_at)).limit(limit).offset(offset)
    alerts = list((await db.execute(q)).scalars().all())
    return alerts, total, unread_count


async def mark_alert_read(
    db: AsyncSession, alert_id: uuid.UUID, user_id: uuid.UUID
) -> HfiAlert | None:
    result = await db.execute(
        select(HfiAlert).where(HfiAlert.id == alert_id, HfiAlert.user_id == user_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        return None
    alert.is_read = True
    await db.flush()
    await db.refresh(alert)
    return alert


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        update(HfiAlert)
        .where(HfiAlert.user_id == user_id, HfiAlert.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    return result.rowcount


def score_alert(
    base_event: str,
    conviction: str | None = None,
    sentiment: str | None = None,
    position_change_pct: float | None = None,
    is_new_position: bool = False,
    is_closed: bool = False,
    in_title: bool = False,
    days_since_last_mention: int | None = None,
    context_length: int = 100,
) -> tuple[int, str]:
    """Compute alert score (0-100) and severity string."""
    base_scores = {"new_filing": 40, "new_company_mention": 30, "new_thesis": 35}
    score = base_scores.get(base_event, 25)

    if conviction == "high":
        score += 20
    if sentiment in ("bullish", "bearish"):
        score += 10
    if position_change_pct and abs(position_change_pct) > 20:
        score += 15
    if is_new_position:
        score += 20
    if is_closed:
        score += 15
    if in_title:
        score += 10

    # Deductions
    if days_since_last_mention is not None and days_since_last_mention < 7:
        score -= 15
    if sentiment == "neutral":
        score -= 10
    if context_length < 50:
        score -= 10

    score = max(0, min(100, score))
    if score >= 80:
        severity = "critical"
    elif score >= 60:
        severity = "high"
    elif score >= 40:
        severity = "medium"
    else:
        severity = "low"
    return score, severity

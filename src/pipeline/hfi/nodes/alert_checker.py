"""Alert checker node — rule-based scoring, no LLM calls."""

import uuid
from datetime import datetime, timedelta, timezone

import structlog

from src.pipeline.hfi.state import PipelineState
from src.services.hfi.alert_service import score_alert

logger = structlog.get_logger()


def alert_checker_node(state: PipelineState) -> PipelineState:
    investor_id = state.get("investor_id", "")
    user_id = state.get("user_id", "")
    content_item_id = state.get("content_item_id", "")
    content_type = state.get("content_type", "")
    entities = state.get("entities", [])
    theses = state.get("theses", [])
    cleaned_text = state.get("cleaned_text", "")
    portfolio_changes = state.get("portfolio_changes", [])

    if not investor_id or not user_id:
        return {**state, "alerts_created": []}

    if content_type != "filing" and len(cleaned_text) < 200:
        return {**state, "alerts_created": []}

    created_ids: list[str] = []

    import asyncio

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(
            _create_alerts_async(
                investor_id=investor_id,
                user_id=user_id,
                content_item_id=content_item_id,
                content_type=content_type,
                entities=entities,
                theses=theses,
                portfolio_changes=portfolio_changes,
                created_ids=created_ids,
            )
        )
    except RuntimeError:
        pass

    return {**state, "alerts_created": created_ids}


async def _create_alerts_async(
    investor_id: str,
    user_id: str,
    content_item_id: str,
    content_type: str,
    entities: list,
    theses: list,
    portfolio_changes: list,
    created_ids: list,
) -> None:
    from sqlalchemy import select

    from src.database import async_session_factory
    from src.models.hfi_alert import HfiAlert

    now = datetime.now(timezone.utc)
    cooldown_cutoff = now - timedelta(days=7)

    async with async_session_factory() as db:
        existing = (
            await db.execute(
                select(HfiAlert.alert_type, HfiAlert.investor_id).where(
                    HfiAlert.investor_id == uuid.UUID(investor_id),
                    HfiAlert.created_at > cooldown_cutoff,
                )
            )
        ).all()
        cooldown_set = {(str(row.investor_id), row.alert_type) for row in existing}

        alerts_to_create = []

        # 1. Filing alert
        if content_type == "filing":
            base = "new_filing"
            if (investor_id, base) not in cooldown_set:
                score, severity = score_alert(base, is_new_position=True)
                alerts_to_create.append(
                    HfiAlert(
                        user_id=uuid.UUID(user_id),
                        investor_id=uuid.UUID(investor_id),
                        content_item_id=uuid.UUID(content_item_id),
                        alert_type=base,
                        title="New 13F Filing Detected",
                        summary="A new 13F SEC filing has been processed and parsed.",
                        severity=severity,
                        score=score,
                        extra_metadata={"content_type": content_type},
                    )
                )

        # 2. Portfolio-change alerts
        if content_type == "filing" and portfolio_changes:
            new_positions = [p for p in portfolio_changes if p.get("change_type") == "new_position"]
            closed_positions = [p for p in portfolio_changes if p.get("change_type") == "closed"]
            big_increases = [
                p
                for p in portfolio_changes
                if p.get("change_type") == "increased"
                and (p.get("shares_previous") or 0) > 0
                and (p.get("shares_current") or 0) >= 2 * p.get("shares_previous")
            ]

            for group, label, base, sev, score_kwargs in [
                (new_positions, "New 13F Position", "portfolio_change", "medium", {"is_new_position": True}),
                (big_increases, "13F Position Doubled", "portfolio_change", "low", {"position_change_pct": 100}),
                (closed_positions, "13F Position Closed", "portfolio_change", "low", {"is_closed": True}),
            ]:
                if (investor_id, base) in cooldown_set:
                    continue
                if not group:
                    continue
                top = " | ".join((p.get("ticker") or p.get("company_name") or "?") for p in group[:8])
                alerts_to_create.append(
                    HfiAlert(
                        user_id=uuid.UUID(user_id),
                        investor_id=uuid.UUID(investor_id),
                        content_item_id=uuid.UUID(content_item_id),
                        alert_type=base,
                        title=label,
                        summary=f"{len(group)}: {top}",
                        severity=sev,
                        score=score_alert(base, **score_kwargs)[0],
                        extra_metadata={
                            "change_type": group[0].get("change_type"),
                            "filing_period": group[0].get("filing_period"),
                            "count": len(group),
                        },
                    )
                )

        # 3. Thesis alerts
        for thesis in theses:
            base = "new_thesis"
            if (investor_id, base) not in cooldown_set:
                score, severity = score_alert(
                    base, conviction="high" if thesis.get("conviction_score", 5) >= 7 else "medium"
                )
                alerts_to_create.append(
                    HfiAlert(
                        user_id=uuid.UUID(user_id),
                        investor_id=uuid.UUID(investor_id),
                        content_item_id=uuid.UUID(content_item_id),
                        alert_type=base,
                        title=f"Investment Thesis — {thesis.get('company', '')}",
                        summary=thesis.get("thesis_summary", "")[:300],
                        severity=severity,
                        score=score,
                        extra_metadata={
                            "ticker": thesis.get("ticker"),
                            "company": thesis.get("company"),
                        },
                    )
                )

        for alert in alerts_to_create:
            db.add(alert)
        await db.commit()

        created_ids.extend([str(a.id) for a in alerts_to_create])
        logger.info("Alerts created", count=len(alerts_to_create), investor_id=investor_id)

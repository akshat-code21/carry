"""HFI Reports endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.models.hfi_report import HfiReport
from src.models.user import User
from src.schemas.hfi import ReportListItem, ReportOut

router = APIRouter(prefix="/api/hfi/reports", tags=["HFI - Reports"])


@router.get("", response_model=list[ReportListItem])
async def list_reports(
    investor_id: uuid.UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(HfiReport).where(HfiReport.user_id == user.id)
    if investor_id:
        q = q.where(HfiReport.investor_id == investor_id)
    q = q.order_by(desc(HfiReport.generated_at)).limit(limit).offset(offset)
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = (
        await db.execute(
            select(HfiReport).where(HfiReport.id == report_id, HfiReport.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.is_read:
        report.is_read = True
        await db.flush()
    return report


@router.post("/{report_id}/read", status_code=204)
async def mark_report_read(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        update(HfiReport)
        .where(HfiReport.id == report_id, HfiReport.user_id == user.id)
        .values(is_read=True)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Report not found")


@router.post("/generate/{investor_id}", response_model=ReportOut)
async def generate_investor_report(
    investor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an on-demand AI intelligence report for an investor."""
    import asyncio
    import json

    from src.models.content_item import ContentItem
    from src.models.investor import Investor
    from src.models.portfolio_change import PortfolioChange
    from src.pipeline.hfi.nodes.report_generator import generate_report_from_context

    investor = (
        await db.execute(
            select(Investor).where(Investor.id == investor_id, Investor.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    items = (
        (
            await db.execute(
                select(ContentItem)
                .where(ContentItem.investor_id == investor_id)
                .order_by(ContentItem.created_at.desc())
                .limit(20)
            )
        )
        .scalars()
        .all()
    )

    entities = []
    theses = []
    source_urls = []
    content_ids = []
    for item in items:
        content_ids.append(str(item.id))
        if item.url:
            source_urls.append(item.url)
        if item.extracted_entities:
            entities.extend(item.extracted_entities)
        if item.extracted_theses:
            theses.extend(item.extracted_theses)

    changes = (
        (
            await db.execute(
                select(PortfolioChange)
                .where(PortfolioChange.investor_id == investor_id)
                .order_by(PortfolioChange.created_at.desc())
                .limit(50)
            )
        )
        .scalars()
        .all()
    )

    portfolio_changes_json = "None"
    filing_period = "N/A"
    if changes:
        filing_period = changes[0].filing_period
        portfolio_changes_json = json.dumps(
            [
                {
                    "ticker": c.ticker_symbol,
                    "company": c.company_name,
                    "change": c.change_type,
                    "shares": c.shares_current,
                    "value": c.value_usd,
                    "pct": float(c.percent_of_portfolio) if c.percent_of_portfolio else None,
                }
                for c in changes
            ]
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: generate_report_from_context(
            investor_id=str(investor_id),
            user_id=str(user.id),
            investor_name=investor.name,
            entities=entities,
            theses=theses,
            source_urls=source_urls,
            content_item_ids=content_ids,
            filing_period=filing_period,
            portfolio_changes_json=portfolio_changes_json,
        ),
    )

    # Allow fire-and-forget save to complete
    await asyncio.sleep(0.5)

    latest_report = (
        await db.execute(
            select(HfiReport)
            .where(HfiReport.investor_id == investor_id, HfiReport.user_id == user.id)
            .order_by(desc(HfiReport.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    if not latest_report:
        raise HTTPException(status_code=500, detail="Report generation failed to persist")

    return latest_report

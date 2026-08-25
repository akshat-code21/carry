"""HFI Analytics endpoints — Consensus & Compare views."""

import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.models.investor import Investor
from src.models.portfolio_change import PortfolioChange
from src.models.user import User
from src.schemas.hfi import (
    CompareCell,
    CompareInvestor,
    CompareResponse,
    ConsensusHolding,
    ConsensusResponse,
    FundHoldingDetail,
    PortfolioChangeOut,
)

router = APIRouter(prefix="/api/hfi/analytics", tags=["HFI — Analytics"])


@router.get("/consensus", response_model=ConsensusResponse)
async def get_consensus(
    period: str | None = Query(None, description="Filing period e.g. 2026-Q1. Defaults to latest."),
    filing_period: str | None = Query(None, description="Alias for period"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cross-investor consensus — aggregated 13F portfolio holdings across all active funds."""
    target_period = filing_period or period

    # 1. Fetch available distinct filing periods
    periods_q = (
        select(func.distinct(PortfolioChange.filing_period))
        .where(PortfolioChange.filing_period.is_not(None))
        .order_by(desc(PortfolioChange.filing_period))
        .limit(10)
    )
    periods_res = await db.execute(periods_q)
    available_periods = [p for (p,) in periods_res.all() if p]

    if not target_period:
        target_period = available_periods[0] if available_periods else "N/A"
        if not available_periods:
            return ConsensusResponse(
                filing_period="N/A",
                available_periods=[],
                total_funds_analyzed=0,
                holdings=[],
            )

    # 2. Count total funds analyzed in this period
    total_funds_q = select(func.count(func.distinct(PortfolioChange.investor_id))).where(
        PortfolioChange.filing_period == target_period
    )
    total_funds = (await db.execute(total_funds_q)).scalar() or 0

    # 3. Aggregate holdings by company name (fallback to ticker)
    comp_col = func.coalesce(PortfolioChange.company_name, PortfolioChange.ticker_symbol)

    q = (
        select(
            comp_col.label("company_name"),
            func.max(PortfolioChange.ticker_symbol).label("ticker_symbol"),
            func.sum(PortfolioChange.value_usd).label("total_value_usd"),
        )
        .where(PortfolioChange.filing_period == target_period)
        .where(comp_col.is_not(None))
        .group_by(comp_col)
        .order_by(desc("total_value_usd"))
        .limit(200)
    )

    rows = (await db.execute(q)).all()
    top_companies = [r.company_name for r in rows if r.company_name]

    # 4. Fetch details of funds for these holdings
    funds_by_company: dict[str, list[FundHoldingDetail]] = {}
    if top_companies:
        detail_q = (
            select(
                comp_col.label("company_name"),
                Investor.id.label("investor_id"),
                Investor.name.label("investor_name"),
                func.sum(PortfolioChange.shares_current).label("total_shares_current"),
                func.sum(PortfolioChange.shares_previous).label("total_shares_previous"),
                func.sum(PortfolioChange.value_usd).label("total_value_usd"),
                func.sum(PortfolioChange.percent_of_portfolio).label("total_percent_of_portfolio"),
            )
            .select_from(PortfolioChange)
            .join(Investor, PortfolioChange.investor_id == Investor.id)
            .where(PortfolioChange.filing_period == target_period)
            .where(comp_col.in_(top_companies))
            .group_by(comp_col, Investor.id, Investor.name)
            .order_by(comp_col, desc("total_value_usd"))
        )
        detail_res = await db.execute(detail_q)
        for row in detail_res.all():
            c = row.company_name
            if c not in funds_by_company:
                funds_by_company[c] = []

            curr = row.total_shares_current or 0
            prev = row.total_shares_previous or 0
            if curr > prev and prev == 0:
                change_type = "new_position"
            elif curr > prev:
                change_type = "increased"
            elif curr < prev and curr > 0:
                change_type = "decreased"
            elif curr == 0 and prev > 0:
                change_type = "closed"
            else:
                change_type = "unchanged"

            funds_by_company[c].append(
                FundHoldingDetail(
                    investor_id=str(row.investor_id),
                    investor_name=row.investor_name,
                    change_type=change_type,
                    shares_current=curr,
                    shares_previous=prev,
                    value_usd=int(row.total_value_usd) if row.total_value_usd is not None else None,
                    percent_of_portfolio=round(float(row.total_percent_of_portfolio), 3)
                    if row.total_percent_of_portfolio is not None
                    else None,
                )
            )

    holdings = []
    for r in rows:
        c_funds = funds_by_company.get(r.company_name, [])
        total_holding_count = sum(1 for f in c_funds if f.shares_current > 0)
        buying_count = sum(1 for f in c_funds if f.change_type in ["new_position", "increased"])
        selling_count = sum(1 for f in c_funds if f.change_type in ["decreased", "closed"])

        holdings.append(
            ConsensusHolding(
                ticker_symbol=r.ticker_symbol,
                company_name=r.company_name,
                total_funds_holding=total_holding_count,
                funds_buying=buying_count,
                funds_selling=selling_count,
                total_value_usd=int(r.total_value_usd) if r.total_value_usd else None,
                funds=c_funds,
            )
        )

    # Sort by total_funds_holding desc, total_value_usd desc
    holdings.sort(key=lambda h: (h.total_funds_holding, h.total_value_usd or 0), reverse=True)

    return ConsensusResponse(
        filing_period=target_period,
        available_periods=available_periods,
        total_funds_analyzed=total_funds,
        holdings=holdings,
    )


@router.get("/compare", response_model=CompareResponse)
async def compare_investors(
    investor_ids: str = Query(..., description="Comma-separated investor UUIDs"),
    period: str | None = Query(None, description="Filing period e.g. 2024-Q3"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Side-by-side portfolio comparison across selected investors."""
    try:
        ids = [uuid.UUID(i.strip()) for i in investor_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid investor_ids format")

    if not ids:
        raise HTTPException(status_code=400, detail="Provide at least one investor_id")

    # Verify ownership
    owned = (
        await db.execute(
            select(Investor.id, Investor.name).where(
                Investor.id.in_(ids), Investor.user_id == user.id
            )
        )
    ).all()
    owned_map = {r.id: r.name for r in owned}
    if len(owned_map) != len(ids):
        raise HTTPException(status_code=403, detail="One or more investors not found or not owned")

    if not period:
        latest = (
            await db.execute(
                select(func.max(PortfolioChange.filing_period)).where(
                    PortfolioChange.investor_id.in_(ids)
                )
            )
        ).scalar()
        period = latest or "N/A"

    rows = (
        (
            await db.execute(
                select(PortfolioChange).where(
                    PortfolioChange.investor_id.in_(ids),
                    PortfolioChange.filing_period == period,
                )
            )
        )
        .scalars()
        .all()
    )

    # Collect all tickers
    all_tickers: set[str] = set()
    by_investor: dict[uuid.UUID, list[PortfolioChange]] = defaultdict(list)
    for row in rows:
        if row.ticker_symbol:
            all_tickers.add(row.ticker_symbol)
        by_investor[row.investor_id].append(row)

    sorted_tickers = sorted(all_tickers)

    compare_investors = []
    for inv_id in ids:
        holdings_map = {}
        for row in by_investor.get(inv_id, []):
            if row.ticker_symbol:
                holdings_map[row.ticker_symbol] = row

        holdings = []
        for ticker in sorted_tickers:
            row = holdings_map.get(ticker)
            if row:
                holdings.append(
                    CompareCell(
                        ticker_symbol=ticker,
                        company_name=row.company_name,
                        shares=row.shares_current,
                        value_usd=row.value_usd,
                        percent_of_portfolio=float(row.percent_of_portfolio)
                        if row.percent_of_portfolio
                        else None,
                        change_type=row.change_type,
                    )
                )
            else:
                holdings.append(
                    CompareCell(
                        ticker_symbol=ticker,
                        company_name=None,
                        shares=0,
                        value_usd=None,
                        percent_of_portfolio=None,
                        change_type="not_held",
                    )
                )

        compare_investors.append(
            CompareInvestor(
                investor_id=inv_id,
                investor_name=owned_map[inv_id],
                holdings=holdings,
            )
        )

    return CompareResponse(
        period=period,
        all_tickers=sorted_tickers,
        investors=compare_investors,
    )


@router.get("/periods", response_model=list[str])
async def list_periods(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available filing periods for this user's investors."""
    investor_ids = (
        (await db.execute(select(Investor.id).where(Investor.user_id == user.id))).scalars().all()
    )

    if not investor_ids:
        return []

    periods = (
        (
            await db.execute(
                select(func.distinct(PortfolioChange.filing_period))
                .where(PortfolioChange.investor_id.in_(investor_ids))
                .order_by(PortfolioChange.filing_period.desc())
            )
        )
        .scalars()
        .all()
    )

    return [p for p in periods if p]


@router.get("/portfolio/{investor_id}", response_model=list[PortfolioChangeOut])
async def get_portfolio(
    investor_id: uuid.UUID,
    period: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio holdings for an investor, optionally filtered by period."""
    investor = (
        await db.execute(
            select(Investor).where(Investor.id == investor_id, Investor.user_id == user.id)
        )
    ).scalar_one_or_none()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    q = select(PortfolioChange).where(PortfolioChange.investor_id == investor_id)
    if period and period.lower() != "all":
        q = q.where(PortfolioChange.filing_period == period)

    q = q.order_by(PortfolioChange.filing_period.desc(), desc(PortfolioChange.value_usd))
    rows = (await db.execute(q)).scalars().all()
    return list(rows)

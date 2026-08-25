"""
Portfolio analytics service for 13F filings.

Synchronous (psycopg2 via settings.database_url_sync) so it can be called
directly from the LangGraph pipeline node.

For each 13F filing it:
  1. Resolves ticker symbols from CUSIP/company name (LLM batch + cache).
  2. Computes % of portfolio for every holding.
  3. Compares against the previous filing period and classifies each holding
     as new_position / increased / decreased / closed / unchanged.
  4. Persists PortfolioChange rows (replacing any prior rows for the period,
     so amendments supersede the original filing).
"""

import json
import re
import uuid
from datetime import date, datetime

import structlog
from openai import OpenAI
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from src.config import get_settings
from src.models.portfolio_change import PortfolioChange
from src.models.ticker_cache import TickerCache

logger = structlog.get_logger()

_TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")
RESOLVE_BATCH_SIZE = 20

TICKER_RESOLUTION_PROMPT = """\
You are a financial data assistant. Map each company to its primary US stock ticker symbol.

Companies:
{companies_json}

Return JSON:
{{"tickers": [{{"name": "exact name from input", "ticker": "AAPL"}}]}}

Rules:
- Use the CUSIP or company name to determine the ticker.
- Set ticker to null if the company is not publicly traded or you are unsure.
- Ticker must match ^[A-Z]{{1,5}}(\\.[A-Z]{{1,2}})?$ (e.g. AAPL, GOOGL, BRK.B).
"""

_sync_engine = None


def _get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(get_settings().database_url_sync, pool_pre_ping=True)
    return _sync_engine


# ---------------------------------------------------------------------------
# Public entrypoint — called by the pipeline portfolio node.
# ---------------------------------------------------------------------------


def process_filing(
    *,
    content_item_id: str,
    investor_id: str,
    holdings: list[dict],
    filing_period: str,
    report_date: str | None = None,
) -> list[dict]:
    """Persist PortfolioChange rows for a single 13F filing. Returns change dicts."""
    if not holdings:
        return []
    if not filing_period:
        filing_period = "N/A"

    investor_uuid = _as_uuid(investor_id)
    if investor_uuid is None:
        logger.warning("portfolio: invalid investor_id", investor_id=investor_id)
        return []

    engine = _get_sync_engine()
    with Session(engine) as session:
        try:
            ticker_map = _resolve_tickers(session, holdings)

            total_value = sum(_safe_int(h.get("value")) for h in holdings) or 0
            enriched = []
            for h in holdings:
                name = (h.get("name") or "").strip()
                cusip = (h.get("cusip") or "").strip().upper() or None
                value = _safe_int(h.get("value"))
                shares = _safe_int(h.get("shares"))
                key = cusip or _norm(name)
                enriched.append(
                    {
                        "key": key,
                        "name": name,
                        "cusip": cusip,
                        "ticker": ticker_map.get(key),
                        "value": value,
                        "shares": shares,
                        "percent": round(value / total_value * 100, 3) if total_value else None,
                    }
                )

            prev_rows = _get_previous_period(session, investor_uuid, filing_period)
            prev_by_key = {r["key"]: r for r in prev_rows}

            # Remove any existing rows for this period (amendment supersedes).
            session.execute(
                delete(PortfolioChange).where(
                    PortfolioChange.investor_id == investor_uuid,
                    PortfolioChange.filing_period == filing_period,
                )
            )

            changes: list[dict] = []

            for h in enriched:
                prev = prev_by_key.get(h["key"])
                change_type = _classify_change(prev, h)
                row = PortfolioChange(
                    investor_id=investor_uuid,
                    content_item_id=_as_uuid(content_item_id),
                    ticker_symbol=h["ticker"],
                    company_name=h["name"] or None,
                    cusip=h["cusip"],
                    change_type=change_type,
                    shares_previous=prev["shares"] if prev else 0,
                    shares_current=h["shares"],
                    value_usd=h["value"] if h["value"] else None,
                    percent_of_portfolio=h["percent"],
                    filing_period=filing_period,
                    report_date=_parse_date(report_date),
                )
                session.add(row)
                changes.append(
                    {
                        "ticker": h["ticker"],
                        "company_name": h["name"],
                        "change_type": change_type,
                        "shares_previous": prev["shares"] if prev else 0,
                        "shares_current": h["shares"],
                        "value_usd": h["value"],
                        "percent_of_portfolio": h["percent"],
                        "filing_period": filing_period,
                    }
                )

            session.commit()
            logger.info(
                "Portfolio persisted",
                investor_id=investor_id,
                filing_period=filing_period,
                holdings=len(changes),
            )
            # Recalculate all filing periods for this investor chronologically
            recalculate_investor_portfolio_changes(session, investor_uuid)
            return changes
        except Exception:
            session.rollback()
            logger.error(
                "Portfolio processing failed",
                investor_id=investor_id,
                filing_period=filing_period,
                exc_info=True,
            )
            return []


# ---------------------------------------------------------------------------
# Change classification & Recalculation
# ---------------------------------------------------------------------------


def recalculate_investor_portfolio_changes(session: Session, investor_uuid: uuid.UUID) -> None:
    """Recalculate shares_previous and change_type for all filing periods chronologically."""
    try:
        periods_q = (
            select(func.distinct(PortfolioChange.filing_period))
            .where(PortfolioChange.investor_id == investor_uuid)
            .order_by(PortfolioChange.filing_period.asc())
        )
        periods = [p for (p,) in session.execute(periods_q).all() if p]
        if not periods:
            return

        prev_by_key: dict[str, dict] = {}

        for period in periods:
            rows = (
                session.execute(
                    select(PortfolioChange).where(
                        PortfolioChange.investor_id == investor_uuid,
                        PortfolioChange.filing_period == period,
                    )
                )
                .scalars()
                .all()
            )

            current_by_key: dict[str, dict] = {}
            for r in rows:
                key = r.cusip or _norm(r.company_name or "")
                if not key:
                    continue

                curr_shares = r.shares_current or 0
                current_by_key[key] = {
                    "name": r.company_name or "",
                    "cusip": r.cusip,
                    "ticker": r.ticker_symbol,
                    "shares": curr_shares,
                }

                prev_info = prev_by_key.get(key)
                prev_shares = prev_info["shares"] if prev_info else 0

                if prev_info is None:
                    r.change_type = "new_position"
                    r.shares_previous = 0
                elif curr_shares > prev_shares:
                    r.change_type = "increased"
                    r.shares_previous = prev_shares
                elif curr_shares < prev_shares:
                    r.change_type = "decreased"
                    r.shares_previous = prev_shares
                else:
                    r.change_type = "unchanged"
                    r.shares_previous = prev_shares

            prev_by_key = current_by_key

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(
            "Failed to recalculate investor portfolio changes",
            investor_id=str(investor_uuid),
            error=str(e),
        )


def _classify_change(prev: dict | None, cur: dict) -> str:
    if prev is None:
        return "new_position"
    if cur["shares"] > prev["shares"]:
        return "increased"
    if cur["shares"] < prev["shares"]:
        return "decreased"
    return "unchanged"


def _get_previous_period(session: Session, investor_uuid, filing_period: str) -> list[dict]:
    latest_prev = session.execute(
        select(func.max(PortfolioChange.filing_period)).where(
            PortfolioChange.investor_id == investor_uuid,
            PortfolioChange.filing_period < filing_period,
        )
    ).scalar()
    if not latest_prev:
        return []
    rows = (
        session.execute(
            select(PortfolioChange).where(
                PortfolioChange.investor_id == investor_uuid,
                PortfolioChange.filing_period == latest_prev,
            )
        )
        .scalars()
        .all()
    )
    out = []
    for r in rows:
        key = r.cusip or _norm(r.company_name or "")
        out.append(
            {
                "key": key,
                "name": r.company_name or "",
                "cusip": r.cusip,
                "ticker": r.ticker_symbol,
                "shares": r.shares_current or 0,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Ticker resolution (LLM batch + persistent cache)
# ---------------------------------------------------------------------------


def _resolve_tickers(session: Session, holdings: list[dict]) -> dict:
    result: dict = {}
    missing: list[dict] = []

    for h in holdings:
        name = (h.get("name") or "").strip()
        cusip = (h.get("cusip") or "").strip().upper() or None
        key = cusip or _norm(name)
        if not key:
            continue
        result[key] = _cached_ticker(session, name, cusip)
        if result[key] is None:
            missing.append({"name": name, "cusip": cusip, "key": key})

    for i in range(0, len(missing), RESOLVE_BATCH_SIZE):
        batch = missing[i : i + RESOLVE_BATCH_SIZE]
        resolved = _llm_resolve_tickers(batch)
        for item in batch:
            ticker = resolved.get(item["name"].strip().lower())
            if ticker:
                result[item["key"]] = ticker
                session.add(
                    TickerCache(company_name=item["name"], cusip=item["cusip"], ticker=ticker)
                )
    try:
        session.commit()
    except Exception:
        session.rollback()
    return result


def _cached_ticker(session: Session, name: str, cusip: str | None) -> str | None:
    if cusip:
        row = (
            session.execute(
                select(TickerCache)
                .where(TickerCache.cusip == cusip)
                .order_by(TickerCache.created_at.desc())
            )
            .scalars()
            .first()
        )
        if row and row.ticker:
            return row.ticker
    row = (
        session.execute(
            select(TickerCache)
            .where(TickerCache.company_name == name)
            .order_by(TickerCache.created_at.desc())
        )
        .scalars()
        .first()
    )
    return row.ticker if row else None


def _llm_resolve_tickers(batch: list[dict]) -> dict[str, str]:
    companies = [{"name": b["name"], "cusip": b["cusip"]} for b in batch]
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        prompt = TICKER_RESOLUTION_PROMPT.format(companies_json=json.dumps(companies))
        response = client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_completion_tokens=1500,
            timeout=60,
        )
        parsed = json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.warning("Ticker resolution failed", error=str(e))
        return {}

    out: dict[str, str] = {}
    raw_tickers = parsed.get("tickers")
    if isinstance(raw_tickers, dict):
        raw_tickers = list(raw_tickers.values())
    elif not isinstance(raw_tickers, list):
        raw_tickers = []

    for t in raw_tickers:
        if not isinstance(t, dict):
            continue
        symbol = (t.get("ticker") or "").upper()
        name = (t.get("name") or "").strip().lower()
        if name and symbol and _TICKER_RE.match(symbol):
            out[name] = symbol
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_int(val) -> int:
    if val is None:
        return 0
    try:
        return int(str(val).replace(",", ""))
    except (ValueError, AttributeError):
        return 0


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _as_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

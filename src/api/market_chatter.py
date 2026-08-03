"""TickerFlow API routes — social-sentiment ticker endpoints.

Mounted under ``/api/v1`` to coexist with the existing yt-chatter
``/api/tickers`` routes without collision.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.market_chatter import (
    MCDashboardResponse,
    MCErrorResponse,
    MCTickerResponse,
    SourceName,
)
from src.services.market_chatter.collection_service import (
    CollectionService,
    UnsupportedTickerError,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["TickerFlow"],
    responses={400: {"model": MCErrorResponse}, 404: {"model": MCErrorResponse}},
)


def _get_service(request: Request) -> CollectionService:
    """Retrieve the CollectionService stashed in app.state during lifespan."""
    service: CollectionService | None = getattr(request.app.state, "tickerflow_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="TickerFlow service is not initialised. Check server logs.",
        )
    return service


@router.get("/health")
async def tickerflow_health(request: Request) -> dict[str, str]:
    """TickerFlow-specific health check."""
    settings = getattr(request.app.state, "tickerflow_settings", None)
    return {
        "status": "ok",
        "service": "tickerflow",
        "sentiment_provider": settings.sentiment_provider if settings else "unknown",
        "adanos_plan": settings.adanos_plan if settings else "unknown",
    }


@router.get("/tickers/{symbol}", response_model=MCTickerResponse)
async def get_ticker(
    symbol: str,
    source: SourceName = Query(default=SourceName.REDDIT),
    period_days: int = Query(default=7),
    refresh: bool = Query(default=False),
    service: CollectionService = Depends(_get_service),
) -> MCTickerResponse:
    """Get social-sentiment data for a ticker symbol."""
    try:
        return await service.ticker_response(symbol, source, period_days, force=refresh)
    except UnsupportedTickerError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Unexpected error processing ticker %s: %s", symbol, exc)
        raise HTTPException(
            status_code=500, detail=f"Unable to process ticker data: {exc}"
        ) from exc


@router.post("/tickers/{symbol}/refresh", response_model=MCTickerResponse)
async def refresh_ticker(
    symbol: str,
    source: SourceName = Query(default=SourceName.REDDIT),
    period_days: int = Query(default=7),
    service: CollectionService = Depends(_get_service),
) -> MCTickerResponse:
    """Force-refresh social-sentiment data for a ticker symbol."""
    try:
        return await service.ticker_response(symbol, source, period_days, force=True)
    except UnsupportedTickerError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tickerflow/dashboard", response_model=MCDashboardResponse)
@router.get("/dashboard/overview", response_model=MCDashboardResponse)
@router.get("/market-chatter/dashboard", response_model=MCDashboardResponse)
async def get_tickerflow_dashboard(
    period_days: int = Query(default=7, ge=1, le=90),
    days: int | None = Query(default=None, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> MCDashboardResponse:
    """Get aggregate TickerFlow social sentiment dashboard stats."""
    from src.services.market_chatter.dashboard_service import DashboardService

    effective_period = days if days is not None else period_days
    dashboard_service = DashboardService()
    return await dashboard_service.get_dashboard_data(db, period_days=effective_period)

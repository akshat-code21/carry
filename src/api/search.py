"""Search API endpoints."""

from fastapi import APIRouter, Depends, Query
from uuid import UUID

from src.api.deps import get_search_service
from src.schemas import (
    SearchResponse,
    SearchSegmentResult,
    SearchPredictionResult,
    StockSearchResult,
)
from src.services.search_service import SearchService

router = APIRouter(prefix="/api", tags=["Search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query(default="hybrid", description="Search type: keyword, semantic, hybrid"),
    channel: UUID | None = Query(default=None, description="Filter by channel ID"),
    ticker: str | None = Query(default=None, description="Filter by ticker"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Hybrid search across transcript segments and predictions.

    Supports keyword (tsvector), semantic (pgvector), or hybrid search.
    """
    results = await search_service.hybrid_search(
        query=q,
        search_type=type,
        channel_id=channel,
        ticker=ticker,
        limit=limit,
        offset=offset,
    )

    return SearchResponse(
        segments=[SearchSegmentResult(**s) for s in results["segments"]],
        predictions=[SearchPredictionResult(**p) for p in results["predictions"]],
        total=results["total"],
    )


@router.get("/search/stocks", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service),
) -> list[StockSearchResult]:
    """Search for stocks relevant to a query based on theme matching.

    Returns top tickers implied by the search query's themes.
    """
    results = await search_service.search_stocks_for_query(q, limit)
    return [StockSearchResult(**r) for r in results]

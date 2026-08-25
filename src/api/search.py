"""Search API endpoints."""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import analytics
from src.api.deps import (
    get_query_router,
    get_search_answer_service,
    get_search_coverage_service,
    get_search_service,
)
from src.database import get_db
from src.models.channel import Channel
from src.schemas import (
    SearchAnswerResponse,
    SearchCoverageResponse,
    SearchPredictionResult,
    SearchResponse,
    SearchSegmentResult,
    SegmentGroup,
    StockDiscoveryResult,
    StockSearchResult,
)
from src.services.query_router import QueryRouter
from src.services.search_answer_service import SearchAnswerService
from src.services.search_coverage_service import SearchCoverageService
from src.services.search_service import SearchService

router = APIRouter(prefix="/api", tags=["Search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query(default="hybrid", description="Search type: keyword, semantic, hybrid"),
    channel: UUID | None = Query(default=None, description="Filter by channel ID"),
    ticker: str | None = Query(default=None, description="Filter by ticker"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(
        default="relevance", pattern="^(relevance|recent)$", description="Group sort order"
    ),
    search_service: SearchService = Depends(get_search_service),
    query_router: QueryRouter = Depends(get_query_router),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Smart search with query intent classification.

    Classifies the query into an intent and routes to the appropriate search strategy:
    - sector_discovery: aggregated stock search across themes
    - ticker_narrative: direct narrative intelligence for a specific ticker
    - entity_lookup / factual_search: hybrid transcript segment search
    """
    started = time.perf_counter()

    # Step 1: Classify query intent
    intent = await query_router.classify(q)

    # Step 1.5: Look up channel_type if a channel filter is applied
    channel_type: str | None = None
    if channel:
        ch_result = await db.execute(select(Channel.channel_type).where(Channel.id == channel))
        row = ch_result.scalar_one_or_none()
        if row:
            channel_type = row

    # Step 2: Route to appropriate search strategy
    stocks = []

    if intent.intent == "sector_discovery":
        # Global search: instrument_type from query (stocks vs ETFs).
        # Channel filter still wins inside search_stocks_for_query.
        stock_results = await search_service.search_stocks_for_query(
            query=q,
            sector_hint=intent.sector_hint,
            limit=10,
            channel_type=channel_type,
            instrument_type=intent.instrument_type,
        )
        stocks = [StockDiscoveryResult(**s) for s in stock_results]

    elif intent.intent in ("ticker_narrative", "sentiment_check") and intent.ticker_hint:
        # Direct ticker narrative / sentiment check — bypass text search,
        # go straight to structured data
        stock_results = await search_service.search_ticker_narrative(intent.ticker_hint)
        stocks = [StockDiscoveryResult(**s) for s in stock_results]

    # Step 3: Run hybrid search for segments + predictions
    # For ticker queries, also search using the company name / ticker for better segment recall
    search_query = q
    search_ticker = ticker
    if intent.ticker_hint and not ticker:
        search_ticker = intent.ticker_hint

    results = await search_service.hybrid_search(
        query=search_query,
        search_type=type,
        channel_id=channel,
        ticker=search_ticker,
        limit=limit,
        offset=offset,
        sort=sort,
    )

    # ── Usage analytics ─────────────────────────────────────────────────
    duration_ms = (time.perf_counter() - started) * 1000.0
    total_results = int(results.get("total", 0)) or (
        len(results.get("segments", [])) + len(results.get("predictions", [])) + len(stocks)
    )
    analytics.record_event(
        "search_performed",
        payload={
            "query": q[:280],
            "search_type": type,
            "intent": intent.intent,
            "ticker_hint": intent.ticker_hint,
            "sector_hint": intent.sector_hint,
            "instrument_type": intent.instrument_type,
            "result_count": total_results,
            "group_count": len(results.get("groups", [])),
            "sort": sort,
            "zero_results": total_results == 0,
            "duration_ms": round(duration_ms, 1),
        },
        counters={"searches": 1, **({"search_zero_results": 1} if total_results == 0 else {})},
    )

    # Effective instrument class for UI labels (channel scope can override query)
    if channel_type == "institutional":
        effective_instrument = "etfs"
    elif channel_type == "individual":
        effective_instrument = "stocks"
    else:
        effective_instrument = intent.instrument_type or "stocks"

    return SearchResponse(
        segments=[SearchSegmentResult(**s) for s in results["segments"]],
        groups=[SegmentGroup(**g) for g in results.get("groups", [])],
        predictions=[SearchPredictionResult(**p) for p in results["predictions"]],
        stocks=stocks,
        videos=results.get("videos", {}),
        channels=results.get("channels", {}),
        total=results["total"],
        has_more=bool(results.get("has_more", False)),
        query_intent=intent.intent,
        instrument_type=effective_instrument,
    )


@router.get("/search/stocks", response_model=list[StockSearchResult])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service),
    query_router: QueryRouter = Depends(get_query_router),
) -> list[StockSearchResult]:
    """Search for stocks or ETFs relevant to a query based on theme matching.

    Uses query understanding to decide instrument class (stocks vs ETFs).
    """
    started = time.perf_counter()
    intent = await query_router.classify(q)
    results = await search_service.search_stocks_for_query(
        q,
        sector_hint=intent.sector_hint,
        limit=limit,
        instrument_type=intent.instrument_type,
    )
    analytics.record_event(
        "search_performed",
        payload={
            "query": q[:280],
            "search_type": "stocks",
            "intent": intent.intent,
            "result_count": len(results),
            "zero_results": not results,
            "duration_ms": round((time.perf_counter() - started) * 1000.0, 1),
        },
        counters={"searches": 1},
    )
    # Map to legacy StockSearchResult format
    return [
        StockSearchResult(
            ticker=r["ticker"],
            total_relevance=r.get("composite_score", r.get("total_relevance", 0.0)),
            themes=r.get("themes", []),
        )
        for r in results
    ]


@router.get("/search/answer", response_model=SearchAnswerResponse)
async def search_answer(
    q: str = Query(..., min_length=1, description="Search query"),
    segment_ids: str | None = Query(
        default=None,
        description="Comma-separated transcript segment IDs in fused-rank order",
    ),
    limit: int = Query(default=12, ge=3, le=20, description="Max segments fed to synthesis"),
    answer_service: SearchAnswerService = Depends(get_search_answer_service),
) -> SearchAnswerResponse:
    """Synthesized answer for a search query with clip citations.

    Cached per normalized query for 24h. Returns available=False when there
    is insufficient evidence or synthesis fails — clients hide the card.
    """
    ids = [s.strip() for s in segment_ids.split(",") if s.strip()] if segment_ids else None
    result = await answer_service.get_or_create(q, ids, max_input=limit)
    return SearchAnswerResponse(**result)


@router.get("/search/coverage", response_model=SearchCoverageResponse)
async def search_coverage(
    q: str = Query(..., min_length=1, description="Search query"),
    segment_ids: str | None = Query(
        default=None,
        description="Comma-separated transcript segment IDs in fused-rank order",
    ),
    window_days: int = Query(default=14, ge=7, le=90, description="Coverage window"),
    coverage_service: SearchCoverageService = Depends(get_search_coverage_service),
) -> SearchCoverageResponse:
    """Coverage intelligence for a topic: video count, stance distribution,
    weekly volume, and week-over-week momentum.

    Stance comes from local FinBERT classification of each video's best
    matching snippet. Cached 6h. total_videos=0 means nothing to show.
    """
    ids = [s.strip() for s in segment_ids.split(",") if s.strip()] if segment_ids else None
    result = await coverage_service.get_or_create(q, ids, window_days=window_days)

    analytics.record_event(
        "coverage_computed",
        payload={
            "query": q[:280],
            "window_days": window_days,
            "total_videos": result.get("total_videos", 0),
            "wow_delta_pct": result.get("wow_delta_pct"),
        },
    )
    return SearchCoverageResponse(**result)

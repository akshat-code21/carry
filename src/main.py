"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.analytics.middleware import AnalyticsMiddleware
from src.api.activity import router as activity_router
from src.api.admin import router as admin_router
from src.api.channels import router as channels_router
from src.api.market_chatter import router as market_chatter_router
from src.api.pipeline import router as pipeline_router
from src.api.predictions import router as predictions_router
from src.api.search import router as search_router
from src.api.themes import router as themes_router
from src.api.tickers import router as tickers_router
from src.api.usage import router as usage_router
from src.api.videos import router as videos_router
from src.api.websub import router as websub_router
from src.auth.dependencies import get_current_user
from src.auth.router import router as auth_router
from src.config import get_settings
from src.database import engine
from src.services.market_chatter.cache import JsonCache
from src.services.market_chatter.collection_service import CollectionService
from src.services.market_chatter.providers import (
    build_price_provider,
    build_sentiment_provider,
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — initialise and tear down TickerFlow services."""
    # ── TickerFlow init ─────────────────────────────────────────────────
    cache = await JsonCache.connect(settings.redis_url)
    sentiment_provider = build_sentiment_provider(settings)
    price_provider = build_price_provider(settings)

    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    service = CollectionService(
        settings=settings,
        session_factory=session_factory,
        cache=cache,
        sentiment_provider=sentiment_provider,
        price_provider=price_provider,
    )

    app.state.tickerflow_settings = settings
    app.state.tickerflow_service = service
    app.state.tickerflow_cache = cache
    app.state.tickerflow_sentiment_provider = sentiment_provider

    log.info(
        "TickerFlow initialised  provider=%s  plan=%s",
        settings.sentiment_provider,
        settings.adanos_plan,
    )

    yield

    # ── TickerFlow teardown ──────────────────────────────────────────────
    await sentiment_provider.close()
    await cache.close()
    log.info("TickerFlow shut down")


app = FastAPI(
    title="YT Chatter API",
    description=(
        "Search engine for financial market commentary from YouTube. "
        "Extracts predictions, themes, and tickers from video transcripts "
        "and tracks performance against actual market data. "
        "Includes the TickerFlow social-sentiment module."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware — allow configured origins, Vercel deployments, and local dev
cors_origins_list = list(settings.cors_origins)
dev_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
for dev_origin in dev_origins:
    if dev_origin not in cors_origins_list:
        cors_origins_list.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_origin_regex=settings.api_cors_origin_regex if settings.api_cors_origin_regex else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usage analytics — logs every API request with latency + user attribution.
# Added after CORS so preflight OPTIONS requests bypass it entirely.
app.add_middleware(AnalyticsMiddleware)

# Register routers.
#
# Authentication: every user-facing router requires an authenticated,
# activated account (Clerk session token → app User row). Public exceptions:
#   - / and /health (infra probes)
#   - /docs, /redoc, /openapi.json
#   - /api/websub/callback — secured via HMAC signature instead; the Google
#     hub cannot authenticate. /api/websub/simulate is admin-gated internally.
#
# Pipeline triggers are additionally admin-gated inside src/api/pipeline.py.
_protected = [Depends(get_current_user)]

app.include_router(search_router, dependencies=_protected)
app.include_router(videos_router, dependencies=_protected)
app.include_router(predictions_router, dependencies=_protected)
app.include_router(channels_router, dependencies=_protected)
app.include_router(tickers_router, dependencies=_protected)
app.include_router(themes_router, dependencies=_protected)
app.include_router(pipeline_router)  # self-guards: auth + require_admin
app.include_router(websub_router)  # callback public (HMAC), simulate admin-gated
app.include_router(activity_router, dependencies=_protected)
app.include_router(market_chatter_router, dependencies=_protected)

# Auth & usage & admin routers handle their own dependency wiring
app.include_router(auth_router)
app.include_router(usage_router, dependencies=_protected)
app.include_router(admin_router)  # self-guards: require_admin


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are present even when 500 internal server errors occur."""
    log.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "yt-chatter",
        "version": "0.1.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "environment": settings.app_env,
        "services": {
            "youtube_api": bool(settings.youtube_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "openai": bool(settings.openai_api_key),
            "fred": bool(settings.fred_api_key),
            "websub": settings.websub_enabled,
            "public_base_url": settings.public_base_url or None,
            "tickerflow": {
                "sentiment_provider": settings.sentiment_provider,
                "adanos_plan": settings.adanos_plan,
            },
        },
    }

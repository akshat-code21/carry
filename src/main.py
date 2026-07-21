"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.channels import router as channels_router
from src.api.pipeline import router as pipeline_router
from src.api.predictions import router as predictions_router
from src.api.search import router as search_router
from src.api.themes import router as themes_router
from src.api.tickers import router as tickers_router
from src.api.videos import router as videos_router
from src.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

app = FastAPI(
    title="YT Chatter API",
    description=(
        "Search engine for financial market commentary from YouTube. "
        "Extracts predictions, themes, and tickers from video transcripts "
        "and tracks performance against actual market data."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware — allow all origins in dev (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(search_router)
app.include_router(videos_router)
app.include_router(predictions_router)
app.include_router(channels_router)
app.include_router(tickers_router)
app.include_router(themes_router)
app.include_router(pipeline_router)


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
        },
    }

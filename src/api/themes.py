"""Themes API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_theme_service
from src.database import get_db
from src.models.theme import ThemeHierarchy, ThemeMention, ThemeTickerMapping
from src.models.video import Video
from src.schemas import ThemeResponse, ThemeTickerMappingResponse, VideoResponse
from src.services.theme_service import ThemeService

router = APIRouter(prefix="/api/themes", tags=["Themes"])


@router.get("")
async def list_themes(
    theme_service: ThemeService = Depends(get_theme_service),
) -> list[dict]:
    """Get hierarchical theme taxonomy (sector → industry → theme → tickers)."""
    return await theme_service.get_theme_hierarchy_tree()


@router.get("/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ThemeResponse:
    """Get a single theme by ID."""
    result = await db.execute(select(ThemeHierarchy).where(ThemeHierarchy.id == theme_id))
    theme = result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    return ThemeResponse.model_validate(theme)


@router.get("/{theme_id}/tickers", response_model=list[ThemeTickerMappingResponse])
async def get_theme_tickers(
    theme_id: UUID,
    theme_service: ThemeService = Depends(get_theme_service),
) -> list[ThemeTickerMappingResponse]:
    """Get all tickers mapped to a theme."""
    mappings = await theme_service.get_ticker_mappings(theme_id)
    return [ThemeTickerMappingResponse.model_validate(m) for m in mappings]


@router.get("/{theme_id}/videos", response_model=list[VideoResponse])
async def get_theme_videos(
    theme_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[VideoResponse]:
    """Get all videos that discuss a given theme."""
    # Find videos via theme_mentions (exclude Shorts)
    result = await db.execute(
        select(Video)
        .join(ThemeMention, ThemeMention.video_id == Video.id)
        .where(ThemeMention.theme_id == theme_id, Video.duration_sec > 60)
        .distinct()
        .order_by(Video.published_at.desc())
        .limit(limit)
    )
    videos = result.scalars().all()
    return [VideoResponse.model_validate(v) for v in videos]

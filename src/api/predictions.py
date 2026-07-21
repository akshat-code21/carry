"""Predictions API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.performance import PerformanceRecord
from src.models.prediction import Prediction
from src.schemas import PerformanceResponse, PredictionResponse, PredictionWithPerformance

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("", response_model=list[PredictionResponse])
async def list_predictions(
    ticker: str | None = Query(default=None, description="Filter by ticker"),
    theme: UUID | None = Query(default=None, description="Filter by theme ID"),
    direction: str | None = Query(default=None, description="Filter by direction"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[PredictionResponse]:
    """List predictions, optionally filtered by ticker or theme."""
    stmt = (
        select(Prediction)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if ticker:
        stmt = stmt.where(Prediction.ticker == ticker.upper())
    if theme:
        stmt = stmt.where(Prediction.theme_id == theme)
    if direction:
        stmt = stmt.where(Prediction.direction == direction.lower())

    result = await db.execute(stmt)
    predictions = result.scalars().all()
    return [PredictionResponse.model_validate(p) for p in predictions]


@router.get("/{prediction_id}/performance", response_model=PredictionWithPerformance)
async def get_prediction_performance(
    prediction_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PredictionWithPerformance:
    """Get a prediction with its performance data."""
    pred_result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = pred_result.scalar_one_or_none()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    response = PredictionWithPerformance.model_validate(prediction)

    # Fetch performance record
    perf_result = await db.execute(
        select(PerformanceRecord).where(
            PerformanceRecord.prediction_id == prediction_id
        )
    )
    performance = perf_result.scalar_one_or_none()

    if performance:
        response.performance = PerformanceResponse.model_validate(performance)

    return response

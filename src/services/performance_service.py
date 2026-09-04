"""Performance service - computes returns and prediction accuracy."""

import logging
import uuid as uuid_mod
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.performance import PerformanceRecord
from src.models.prediction import Prediction
from src.models.video import Video
from src.services.interfaces import MarketDataSource

logger = logging.getLogger(__name__)


class PerformanceService:
    """Computes price performance after predictions and evaluates accuracy."""

    def __init__(self, db: AsyncSession, market_data: MarketDataSource) -> None:
        self.db = db
        self.market_data = market_data

    async def compute_performance(self, prediction_id: uuid_mod.UUID) -> PerformanceRecord | None:
        """Compute performance for a single prediction.

        Fetches price at video date + 1d/1w/1m and computes returns.
        """
        # Get prediction and video
        pred_result = await self.db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = pred_result.scalar_one_or_none()
        if not prediction or not prediction.ticker:
            return None

        video_result = await self.db.execute(select(Video).where(Video.id == prediction.video_id))
        video = video_result.scalar_one_or_none()
        if not video or not video.published_at:
            return None

        video_date = video.published_at.date()
        ticker = prediction.ticker.upper()

        # Fetch prices at different time horizons
        price_at_video = await self.market_data.get_price_at_date(ticker, video_date)
        if price_at_video is None:
            logger.warning(f"No price data for {ticker} at {video_date} - skipping performance")
            return None

        price_1d = await self.market_data.get_price_at_date(ticker, video_date + timedelta(days=1))
        price_1w = await self.market_data.get_price_at_date(ticker, video_date + timedelta(days=7))
        price_1m = await self.market_data.get_price_at_date(ticker, video_date + timedelta(days=30))

        # Compute returns
        return_1d = self._compute_return(price_at_video, price_1d)
        return_1w = self._compute_return(price_at_video, price_1w)
        return_1m = self._compute_return(price_at_video, price_1m)

        # Evaluate direction accuracy
        direction_accurate = self._evaluate_direction(prediction.direction, return_1w)

        # Check if performance record already exists
        exist_result = await self.db.execute(
            select(PerformanceRecord).where(PerformanceRecord.prediction_id == prediction.id)
        )
        record = exist_result.scalar_one_or_none()

        if record:
            record.price_at_video = price_at_video
            record.price_1d = price_1d
            record.price_1w = price_1w
            record.price_1m = price_1m
            record.return_1d = return_1d
            record.return_1w = return_1w
            record.return_1m = return_1m
            record.direction_accurate = direction_accurate
        else:
            # Create new performance record
            record = PerformanceRecord(
                ticker=ticker,
                video_id=video.id,
                prediction_id=prediction.id,
                price_at_video=price_at_video,
                price_1d=price_1d,
                price_1w=price_1w,
                price_1m=price_1m,
                return_1d=return_1d,
                return_1w=return_1w,
                return_1m=return_1m,
                direction_accurate=direction_accurate,
            )
            self.db.add(record)

        await self.db.flush()

        # Update prediction accuracy
        if direction_accurate is not None:
            prediction.accurate = direction_accurate
            await self.db.flush()

        return record

    async def compute_all_pending(self) -> list[PerformanceRecord]:
        """Compute performance for all predictions that don't have records yet."""
        # Find predictions with tickers that have no performance records
        result = await self.db.execute(
            select(Prediction).where(
                Prediction.ticker.isnot(None),
                Prediction.accurate.is_(None),
            )
        )
        predictions = result.scalars().all()

        records = []
        for prediction in predictions:
            record = await self.compute_performance(prediction.id)
            if record:
                records.append(record)

        return records

    @staticmethod
    def _compute_return(base_price: float, future_price: float | None) -> float | None:
        """Compute percentage return."""
        if future_price is None or base_price == 0:
            return None
        return ((future_price - base_price) / base_price) * 100

    @staticmethod
    def _evaluate_direction(
        predicted_direction: str | None, actual_return: float | None
    ) -> bool | None:
        """Check if predicted direction matches actual price movement.

        Uses 1-week return as the primary signal.
        """
        if predicted_direction is None or actual_return is None:
            return None

        direction = predicted_direction.lower()
        if direction == "bullish":
            return actual_return > 0
        elif direction == "bearish":
            return actual_return < 0
        elif direction == "neutral":
            return abs(actual_return) < 2.0  # Within ±2% counts as neutral
        return None

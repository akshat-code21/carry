"""Step 5: Market Data & Performance Tracking.

Fetches price data for all tickers found in predictions,
computes returns, and evaluates prediction accuracy.
"""

import logging
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction import Prediction
from src.services.interfaces import MarketDataSource
from src.services.performance_service import PerformanceService

logger = logging.getLogger(__name__)


class MarketTrackingPipeline:
    """Pipeline step 5: Fetch market data and compute performance metrics."""

    def __init__(
        self,
        db: AsyncSession,
        market_data: MarketDataSource,
    ) -> None:
        self.db = db
        self.market_data = market_data
        self.performance_service = PerformanceService(db, market_data)

    async def track_video_predictions(self, video_id: uuid_mod.UUID) -> dict:
        """Compute performance for all predictions in a video.

        Returns summary of what was tracked.
        """
        result = await self.db.execute(
            select(Prediction).where(
                Prediction.video_id == video_id,
                Prediction.ticker.isnot(None),
                Prediction.accurate.is_(None),
            )
        )
        predictions = result.scalars().all()

        tracked = 0
        failed = 0

        for prediction in predictions:
            try:
                record = await self.performance_service.compute_performance(prediction.id)
                if record:
                    tracked += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Performance tracking failed for prediction {prediction.id}: {e}")
                failed += 1

        await self.db.flush()

        logger.info(f"Tracked {tracked} predictions for video {video_id} ({failed} failed)")
        return {"tracked": tracked, "failed": failed}

    async def track_all_pending(self) -> dict:
        """Compute performance for all pending predictions across all videos."""
        records = await self.performance_service.compute_all_pending()
        await self.db.flush()

        logger.info(f"Tracked {len(records)} pending predictions")
        return {"tracked": len(records)}

    async def get_unique_tickers(self) -> list[str]:
        """Get all unique tickers across all predictions."""
        result = await self.db.execute(
            select(Prediction.ticker).where(Prediction.ticker.isnot(None)).distinct()
        )
        return [row[0].upper() for row in result.all()]

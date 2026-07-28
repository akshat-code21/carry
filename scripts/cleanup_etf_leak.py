"""One-off cleanup: remove ETF leakage from individual-channel data.

Fixes data already written before instrument-policy enforcement:

1. Delete ThemeTickerMapping rows whose ticker is a known ETF
   (theme mappings are equities-only).
2. Null Prediction.ticker for predictions on individual-channel videos
   when the ticker is a known ETF (keep the narrative text).
3. Recompute speaker_ticker_aggregation for every channel so dashboard /
   top-stocks no longer surface leaked ETFs.

Run:
    uv run python -m scripts.cleanup_etf_leak
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from src.database import async_session_factory, engine
from src.models.channel import Channel
from src.models.prediction import Prediction
from src.models.theme import ThemeTickerMapping
from src.models.video import Video
from src.services.aggregation_service import AggregationService
from src.services.etf_mapping_service import ETFMappingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup() -> None:
    # Force a fresh load so class-level cache cannot hide newly expanded ETFs.
    ETFMappingService._loaded = False
    ETFMappingService._all_etf_tickers = set()
    etf_service = ETFMappingService()
    known_etfs = etf_service.get_all_etf_tickers()
    logger.info(f"Known ETF universe size: {len(known_etfs)}")

    async with async_session_factory() as session:
        # --- 1. Purge ETF rows from theme_ticker_mappings ---
        mapping_result = await session.execute(select(ThemeTickerMapping))
        mappings = list(mapping_result.scalars().all())
        deleted_mappings = 0
        for m in mappings:
            if m.ticker and etf_service.is_etf(m.ticker):
                await session.delete(m)
                deleted_mappings += 1
        logger.info(f"Deleted {deleted_mappings} ETF theme_ticker_mappings")

        # --- 2. Null ETF tickers on individual-channel predictions ---
        ind_ch_result = await session.execute(
            select(Channel.id).where(Channel.channel_type == "individual")
        )
        ind_channel_ids = [row[0] for row in ind_ch_result.all()]

        nulled_preds = 0
        if ind_channel_ids:
            video_result = await session.execute(
                select(Video.id).where(Video.channel_id.in_(ind_channel_ids))
            )
            video_ids = [row[0] for row in video_result.all()]
            if video_ids:
                pred_result = await session.execute(
                    select(Prediction).where(
                        Prediction.video_id.in_(video_ids),
                        Prediction.ticker.isnot(None),
                    )
                )
                for pred in pred_result.scalars().all():
                    if pred.ticker and etf_service.is_etf(pred.ticker):
                        pred.ticker = None
                        nulled_preds += 1
        logger.info(
            f"Nulled ETF tickers on {nulled_preds} individual-channel predictions"
        )

        # --- 3. Also null stock tickers on institutional predictions (policy) ---
        inst_ch_result = await session.execute(
            select(Channel.id).where(Channel.channel_type == "institutional")
        )
        inst_channel_ids = [row[0] for row in inst_ch_result.all()]
        nulled_inst = 0
        if inst_channel_ids:
            video_result = await session.execute(
                select(Video.id).where(Video.channel_id.in_(inst_channel_ids))
            )
            video_ids = [row[0] for row in video_result.all()]
            if video_ids:
                pred_result = await session.execute(
                    select(Prediction).where(
                        Prediction.video_id.in_(video_ids),
                        Prediction.ticker.isnot(None),
                    )
                )
                for pred in pred_result.scalars().all():
                    if pred.ticker and not etf_service.is_etf(pred.ticker):
                        pred.ticker = None
                        nulled_inst += 1
        logger.info(
            f"Nulled stock tickers on {nulled_inst} institutional-channel predictions"
        )

        await session.flush()

        # --- 4. Recompute aggregation for all channels ---
        all_ch = await session.execute(select(Channel.id))
        channel_ids = [row[0] for row in all_ch.all()]
        agg = AggregationService(session)
        for cid in channel_ids:
            await agg.update_channel_aggregation(cid)
            logger.info(f"Re-aggregated channel {cid}")

        await session.commit()
        logger.info(
            f"Cleanup complete. mappings_deleted={deleted_mappings}, "
            f"individual_etf_preds_nulled={nulled_preds}, "
            f"institutional_stock_preds_nulled={nulled_inst}, "
            f"channels_reaggregated={len(channel_ids)}"
        )


async def main() -> None:
    await cleanup()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

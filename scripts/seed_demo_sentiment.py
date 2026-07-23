"""One-off script: seeds a demo channel/video/predictions so the
bullish/bearish sentiment-timeline feature can be tested without running
the full YouTube + LLM ingestion pipeline.

Run from the repo root with:
    uv run python scripts/seed_demo_sentiment.py

Safe to delete after testing.
"""

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make sure the repo root (parent of this scripts/ dir) is importable as
# `src`, regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import async_session_factory
from src.models.channel import Channel
from src.models.prediction import Prediction
from src.models.video import Video
from src.services.aggregation_service import AggregationService

TICKER = "AAPL"


async def main() -> None:
    async with async_session_factory() as db:
        channel = Channel(
            youtube_channel_id=f"demo-channel-{uuid.uuid4().hex[:8]}",
            title="Demo Finance Channel",
        )
        db.add(channel)
        await db.flush()

        today = datetime.now(timezone.utc)
        directions = ["bullish", "bearish", "neutral"]

        for day_offset in range(10):
            published_at = today - timedelta(days=day_offset)
            video = Video(
                channel_id=channel.id,
                youtube_video_id=f"demo-video-{uuid.uuid4().hex[:8]}",
                title=f"Demo video for {published_at.date().isoformat()}",
                published_at=published_at,
                processed=True,
                transcript_status="complete",
            )
            db.add(video)
            await db.flush()

            # 1-4 predictions per day, random-ish direction so the chart has
            # varied bars.
            for _ in range(random.randint(1, 4)):
                direction = random.choices(
                    directions, weights=[0.5, 0.35, 0.15]
                )[0]
                db.add(
                    Prediction(
                        video_id=video.id,
                        ticker=TICKER,
                        prediction_text=f"Demo {direction} take on {TICKER}",
                        direction=direction,
                        confidence=round(random.uniform(0.5, 0.95), 2),
                        extracted_by="demo-seed-script",
                    )
                )

        await db.commit()

        # Recompute the ticker aggregation rollup so it shows up in the
        # /api/tickers list endpoint too, not just the detail/timeline ones.
        agg_service = AggregationService(db)
        await agg_service.update_channel_aggregation(channel.id)
        await db.commit()

    print(f"Seeded demo data for ticker {TICKER}.")
    print(f"Try: http://localhost:8000/api/tickers/{TICKER}/sentiment-timeline")
    print(f"Try: http://localhost:3000/tickers/{TICKER}")


if __name__ == "__main__":
    asyncio.run(main())

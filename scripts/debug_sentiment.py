"""Diagnostic script: figures out why /sentiment-timeline returns [] for a
ticker that clearly has mentions (per /api/tickers/{ticker}).

Run from repo root:
    uv run python scripts/debug_sentiment.py NVDA

Safe to delete after debugging.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from src.database import async_session_factory
from src.models.theme import ThemeMention, ThemeTickerMapping
from src.models.video import Video


async def main(ticker: str) -> None:
    ticker = ticker.upper()
    async with async_session_factory() as db:
        mapping_result = await db.execute(
            select(ThemeTickerMapping).where(ThemeTickerMapping.ticker == ticker)
        )
        mappings = mapping_result.scalars().all()
        print(f"ThemeTickerMapping rows for {ticker}: {len(mappings)}")
        theme_ids = [m.theme_id for m in mappings]

        if not theme_ids:
            print("No theme mappings found at all -- exact-match ticker mismatch likely (case/whitespace).")
            return

        mention_result = await db.execute(
            select(ThemeMention).where(ThemeMention.theme_id.in_(theme_ids))
        )
        mentions = mention_result.scalars().all()
        print(f"ThemeMention rows for those themes: {len(mentions)}")

        video_ids = list({m.video_id for m in mentions})
        print(f"Distinct video_ids referenced: {len(video_ids)}")

        if video_ids:
            video_result = await db.execute(
                select(Video).where(Video.id.in_(video_ids))
            )
            videos = video_result.scalars().all()
            print(f"Video rows found for those ids: {len(videos)} (expected {len(video_ids)})")
            null_published = [v for v in videos if v.published_at is None]
            print(f"Videos with published_at = NULL: {len(null_published)} / {len(videos)}")
            for v in videos[:5]:
                print(f"  video={v.id} published_at={v.published_at!r} title={v.title[:60]!r}")

        # Also check for sentiment values present
        sentiments = [m.sentiment for m in mentions]
        print(f"Sentiment value sample: {sentiments[:10]}")
        print(f"Distinct sentiment values: {set(sentiments)}")


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    asyncio.run(main(ticker_arg))

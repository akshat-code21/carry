"""One-off fix-up script: backfills Video.published_at for videos that were
ingested before the youtube_service.py fix (which previously never fetched
`snippet.publishedAt` from the YouTube Data API, leaving published_at NULL
for every video ingested via the yt-dlp flat-playlist path).

Run from repo root:
    uv run python scripts/backfill_published_at.py

Safe to delete after running.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from src.config import get_settings
from src.database import async_session_factory
from src.models.video import Video

BATCH_SIZE = 50


async def main() -> None:
    settings = get_settings()
    if not settings.youtube_api_key:
        print("YOUTUBE_API_KEY is not set in .env -- cannot backfill.")
        return

    from googleapiclient.discovery import build

    service = build("youtube", "v3", developerKey=settings.youtube_api_key)

    async with async_session_factory() as db:
        result = await db.execute(
            select(Video).where(Video.published_at.is_(None))
        )
        videos = list(result.scalars().all())
        print(f"Found {len(videos)} videos with published_at = NULL")

        if not videos:
            return

        videos_by_youtube_id = {v.youtube_video_id: v for v in videos}
        all_ids = list(videos_by_youtube_id.keys())

        updated = 0
        not_found = 0

        for i in range(0, len(all_ids), BATCH_SIZE):
            batch_ids = all_ids[i : i + BATCH_SIZE]
            response = (
                service.videos()
                .list(part="snippet", id=",".join(batch_ids))
                .execute()
            )
            items = {item["id"]: item for item in response.get("items", [])}

            for vid_id in batch_ids:
                item = items.get(vid_id)
                video = videos_by_youtube_id[vid_id]
                if item is None:
                    not_found += 1
                    continue

                published_at_str = item["snippet"].get("publishedAt")
                if not published_at_str:
                    continue

                from datetime import datetime

                video.published_at = datetime.fromisoformat(
                    published_at_str.replace("Z", "+00:00")
                )
                updated += 1

            print(f"Processed batch {i // BATCH_SIZE + 1}: updated so far = {updated}")

        await db.commit()
        print(f"Done. Updated {updated} videos. {not_found} not found on YouTube (deleted/private).")


if __name__ == "__main__":
    asyncio.run(main())

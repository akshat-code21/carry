"""Subscribe (or re-subscribe) all channels to YouTube WebSub.

Use after:
  - first deploy of WebSub
  - PUBLIC_BASE_URL / ngrok URL changes
  - lease recovery

Usage:
  make subscribe-websub
  # or:
  uv run python scripts/subscribe_all_channels_websub.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script file
# (uv run python scripts/... does not install `src` as a package by default).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("subscribe_all_channels_websub")


async def main() -> int:
    from sqlalchemy import select

    from src.config import get_settings
    from src.database import async_session_factory, engine
    from src.models.channel import Channel
    from src.tasks.pipeline_tasks import subscribe_channel_websub_task

    settings = get_settings()
    if not settings.websub_enabled:
        logger.error(
            "PUBLIC_BASE_URL is not set. Start ngrok (or set your public API URL), "
            "add PUBLIC_BASE_URL to .env, then re-run."
        )
        return 1

    logger.info("PUBLIC_BASE_URL=%s", settings.public_base_url)
    logger.info("WebSub hub=%s", settings.websub_hub_url)

    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Channel).where(Channel.websub_status != "disabled")
            )
            channels = list(result.scalars().all())

        if not channels:
            logger.info("No channels to subscribe.")
            return 0

        logger.info("Queueing WebSub subscribe for %s channels…", len(channels))
        for ch in channels:
            subscribe_channel_websub_task.delay(str(ch.id))
            logger.info("  queued %s (%s)", ch.title, ch.youtube_channel_id)

        logger.info(
            "Done. Ensure the Celery worker is running so subscribe tasks execute. "
            "Watch API logs for hub verification GETs on /api/websub/callback."
        )
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""Classify existing channels as individual or institutional.

One-time migration script to classify already-ingested channels.
Run via: uv run python -m scripts.classify_existing_channels
"""

import asyncio
import json
import logging

from sqlalchemy import select

from src.config import get_settings
from src.database import async_session_factory, engine
from src.models.channel import Channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

CHANNEL_CLASSIFICATION_PROMPT = """Classify this YouTube channel as either "individual" or "institutional".

- "institutional": Financial institutions, banks, brokerages, research firms, hedge funds, asset managers, financial news networks, or any channel representing a company/organization rather than a person. Examples: Fundstrat, Morgan Stanley, Goldman Sachs, JP Morgan, BlackRock, Bloomberg, CNBC, Barclays, UBS, Deutsche Bank, BofA Securities, Citi, Wells Fargo, Jefferies.
- "individual": Personal channels run by individual traders, analysts, influencers, or content creators. The channel is clearly associated with one person or a small team creating personal content. Examples: ProfGMarkets, Meet Kevin, Stock Moe, Andrei Jikh, Graham Stephan.

Channel Title: "{title}"
Channel Description: "{description}"

Return ONLY valid JSON: {{"channel_type": "individual" or "institutional"}}"""


async def classify_existing_channels() -> None:
    """Classify all existing channels that still have the default 'individual' type."""
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY is required for channel classification")
        return

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    async with async_session_factory() as session:
        result = await session.execute(select(Channel))
        channels = result.scalars().all()

        logger.info(f"Found {len(channels)} channels to classify")

        updated = 0
        for channel in channels:
            desc_truncated = (channel.description or "")[:500]

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "user",
                            "content": CHANNEL_CLASSIFICATION_PROMPT.format(
                                title=channel.title,
                                description=desc_truncated,
                            ),
                        },
                    ],
                    temperature=0.0,
                    max_completion_tokens=50,
                )

                content = response.choices[0].message.content
                data = json.loads(content)
                channel_type = data.get("channel_type", "individual")

                if channel_type not in ("individual", "institutional"):
                    channel_type = "individual"

                old_type = channel.channel_type
                channel.channel_type = channel_type
                updated += 1

                logger.info(
                    f"  {channel.title}: {old_type} → {channel_type}"
                )

            except Exception as e:
                logger.warning(
                    f"  Failed to classify '{channel.title}': {e} - keeping as '{channel.channel_type}'"
                )

        await session.commit()
        logger.info(f"\n✅ Classification complete: {updated}/{len(channels)} channels updated")


async def main() -> None:
    await classify_existing_channels()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

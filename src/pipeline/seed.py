"""Seed script — loads theme_taxonomy.json into the database.

Run via: uv run python -m src.pipeline.seed
"""

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from src.database import async_session_factory, engine
from src.models.theme import ThemeHierarchy, ThemeTickerMapping

logger = logging.getLogger(__name__)

TAXONOMY_FILE = Path(__file__).parent.parent.parent / "data" / "theme_taxonomy.json"


async def seed_taxonomy() -> None:
    """Load the theme taxonomy from JSON into the database."""
    if not TAXONOMY_FILE.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {TAXONOMY_FILE}")

    with open(TAXONOMY_FILE) as f:
        data = json.load(f)

    async with async_session_factory() as session:
        sectors = data.get("sectors", [])
        stats = {"sectors": 0, "industries": 0, "themes": 0, "ticker_mappings": 0}

        for sector_data in sectors:
            # Check if sector already exists
            existing = await session.execute(
                select(ThemeHierarchy).where(
                    ThemeHierarchy.level == "sector",
                    ThemeHierarchy.name == sector_data["name"],
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"Sector '{sector_data['name']}' already exists, skipping")
                continue

            # Create sector
            sector = ThemeHierarchy(
                level="sector",
                name=sector_data["name"],
                description=sector_data.get("description"),
            )
            session.add(sector)
            await session.flush()
            stats["sectors"] += 1

            for industry_data in sector_data.get("industries", []):
                # Create industry under sector
                industry = ThemeHierarchy(
                    parent_id=sector.id,
                    level="industry",
                    name=industry_data["name"],
                    description=industry_data.get("description"),
                )
                session.add(industry)
                await session.flush()
                stats["industries"] += 1

                for theme_data in industry_data.get("themes", []):
                    # Create theme under industry
                    theme = ThemeHierarchy(
                        parent_id=industry.id,
                        level="theme",
                        name=theme_data["name"],
                        description=theme_data.get("description"),
                    )
                    session.add(theme)
                    await session.flush()
                    stats["themes"] += 1

                    # Create ticker mappings for this theme
                    for ticker in theme_data.get("tickers", []):
                        mapping = ThemeTickerMapping(
                            theme_id=theme.id,
                            ticker=ticker,
                            relevance_score=1.0,  # Curated = max relevance
                            source="curated",
                            notes=f"Seeded from taxonomy for theme: {theme_data['name']}",
                        )
                        session.add(mapping)
                        stats["ticker_mappings"] += 1

        await session.commit()

        logger.info(
            f"Seed complete: {stats['sectors']} sectors, "
            f"{stats['industries']} industries, {stats['themes']} themes, "
            f"{stats['ticker_mappings']} ticker mappings"
        )
        print(f"✅ Seeded taxonomy: {stats}")


async def main() -> None:
    """Entry point for the seed script."""
    logging.basicConfig(level=logging.INFO)
    await seed_taxonomy()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

"""Theme service — theme taxonomy CRUD and matching."""

import logging
import uuid as uuid_mod
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.theme import ThemeHierarchy, ThemeMention, ThemeTickerMapping
from src.services.interfaces import ExtractedTheme

logger = logging.getLogger(__name__)


class ThemeService:
    """Handles theme hierarchy operations, theme matching, and ticker mappings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_themes(self) -> list[ThemeHierarchy]:
        """Get all themes in the hierarchy."""
        result = await self.db.execute(select(ThemeHierarchy))
        return list(result.scalars().all())

    async def get_themes_by_level(self, level: str) -> list[ThemeHierarchy]:
        """Get all themes at a specific level (sector, industry, theme, narrative)."""
        result = await self.db.execute(select(ThemeHierarchy).where(ThemeHierarchy.level == level))
        return list(result.scalars().all())

    async def get_theme_children(self, parent_id: uuid_mod.UUID) -> list[ThemeHierarchy]:
        """Get direct children of a theme in the hierarchy."""
        result = await self.db.execute(
            select(ThemeHierarchy).where(ThemeHierarchy.parent_id == parent_id)
        )
        return list(result.scalars().all())

    async def match_theme(self, extracted: ExtractedTheme) -> ThemeHierarchy | None:
        """Match an LLM-extracted theme against the hierarchy.

        Attempts exact name match at the 'theme' level first,
        then falls back to fuzzy matching at the industry/sector level.
        """
        # Try exact match on theme name (case-insensitive)
        result = await self.db.execute(
            select(ThemeHierarchy).where(
                ThemeHierarchy.level == "theme",
                ThemeHierarchy.name.ilike(extracted.theme),
            )
        )
        theme = result.scalar_one_or_none()
        if theme:
            return theme

        # Try matching at industry level
        result = await self.db.execute(
            select(ThemeHierarchy).where(
                ThemeHierarchy.level == "industry",
                ThemeHierarchy.name.ilike(f"%{extracted.industry}%"),
            )
        )
        industry = result.scalar_one_or_none()

        if industry:
            # Create a new theme under this industry
            new_theme = ThemeHierarchy(
                parent_id=industry.id,
                level="theme",
                name=extracted.theme,
                description=extracted.narrative,
            )
            self.db.add(new_theme)
            await self.db.flush()
            return new_theme

        # No match found — create as a narrative-level free-text entry
        logger.info(f"No taxonomy match for theme '{extracted.theme}' — creating narrative entry")
        new_theme = ThemeHierarchy(
            parent_id=None,
            level="narrative",
            name=extracted.theme[:255],
            description=extracted.narrative,
        )
        self.db.add(new_theme)
        await self.db.flush()
        return new_theme

    async def create_theme_mention(
        self,
        video_id: uuid_mod.UUID,
        segment_id: uuid_mod.UUID,
        theme_id: uuid_mod.UUID,
        sentiment: str,
        relevance_score: float,
        mention_text: str | None,
        narrative: str | None,
        llm_sentiment: str | None = None,
        finbert_confidence: float | None = None,
    ) -> ThemeMention:
        """Record a theme mention in a video segment."""
        mention = ThemeMention(
            video_id=video_id,
            segment_id=segment_id,
            theme_id=theme_id,
            sentiment=sentiment,
            llm_sentiment=llm_sentiment,
            finbert_confidence=finbert_confidence,
            relevance_score=relevance_score,
            mention_text=mention_text,
            narrative=narrative,
        )
        self.db.add(mention)
        await self.db.flush()
        return mention

    async def get_ticker_mappings(self, theme_id: uuid_mod.UUID) -> list[ThemeTickerMapping]:
        """Get all ticker mappings for a theme."""
        result = await self.db.execute(
            select(ThemeTickerMapping).where(ThemeTickerMapping.theme_id == theme_id)
        )
        return list(result.scalars().all())

    async def add_ticker_mapping(
        self,
        theme_id: uuid_mod.UUID,
        ticker: str,
        relevance_score: float,
        source: str = "curated",
        notes: str | None = None,
    ) -> ThemeTickerMapping | None:
        """Add a new equity ticker mapping for a theme.

        Theme→ticker mappings are stock-only. ETFs belong in etf_mappings.json
        and are resolved only for institutional channels. Returns None if the
        ticker is a known ETF (rejected) or empty after cleaning.
        """
        import re

        from src.services.etf_mapping_service import ETFMappingService

        # Handle LLM outputs like "SAMSUNG ELECTRONICS (005930.KS)"
        match = re.search(r"\((.*?)\)", ticker)
        if match:
            clean_ticker = match.group(1).strip()
        else:
            # Fallback: take the first word to drop any trailing company names
            clean_ticker = ticker.strip().split(" ")[0]

        # Enforce DB limit
        clean_ticker = clean_ticker.upper()[:20]
        if not clean_ticker:
            return None

        # Never store ETFs as theme stock mappings
        if ETFMappingService().is_etf(clean_ticker):
            logger.info(
                f"Rejecting ETF ticker {clean_ticker} for theme_id={theme_id} "
                f"(source={source}) — theme mappings are equities only"
            )
            return None

        mapping = ThemeTickerMapping(
            theme_id=theme_id,
            ticker=clean_ticker,
            relevance_score=relevance_score,
            source=source,
            notes=notes,
        )
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def get_theme_hierarchy_tree(self, include_narratives: bool = False) -> list[dict]:
        """Build a hierarchical tree structure of all themes for API responses.

        Uses 2 queries (all nodes + ticker mappings via selectinload) instead of
        the previous N+1 approach that fired 133 sequential queries.
        """
        # Single query: load all hierarchy nodes with their ticker mappings
        # The selectinload fires one additional SELECT for ticker_mappings
        stmt = (
            select(ThemeHierarchy)
            .options(selectinload(ThemeHierarchy.ticker_mappings))
            .order_by(ThemeHierarchy.level, ThemeHierarchy.name)
        )
        if not include_narratives:
            stmt = stmt.where(ThemeHierarchy.level != "narrative")

        result = await self.db.execute(stmt)
        all_nodes = result.scalars().all()

        # Build lookup structures in-memory — O(n)
        nodes_by_id: dict[uuid_mod.UUID, ThemeHierarchy] = {}
        children_by_parent: dict[uuid_mod.UUID | None, list[ThemeHierarchy]] = defaultdict(list)

        for node in all_nodes:
            nodes_by_id[node.id] = node
            children_by_parent[node.parent_id].append(node)

        # Build the tree starting from root nodes (parent_id is None)
        tree: list[dict] = []

        for sector in children_by_parent[None]:
            if sector.level == "narrative":
                # Narrative-level themes (free-text LLM extractions)
                tree.append({
                    "id": str(sector.id),
                    "name": sector.name,
                    "description": sector.description,
                    "level": sector.level,
                    "industries": [],
                })
                continue

            if sector.level != "sector":
                continue

            sector_node = {
                "id": str(sector.id),
                "name": sector.name,
                "description": sector.description,
                "level": sector.level,
                "industries": [],
            }

            for industry in children_by_parent.get(sector.id, []):
                industry_node = {
                    "id": str(industry.id),
                    "name": industry.name,
                    "description": industry.description,
                    "level": industry.level,
                    "themes": [],
                }

                for theme in children_by_parent.get(industry.id, []):
                    theme_node = {
                        "id": str(theme.id),
                        "name": theme.name,
                        "description": theme.description,
                        "level": theme.level,
                        "tickers": [
                            {
                                "ticker": m.ticker,
                                "relevance_score": m.relevance_score,
                                "source": m.source,
                            }
                            for m in theme.ticker_mappings
                        ],
                    }
                    industry_node["themes"].append(theme_node)

                sector_node["industries"].append(industry_node)

            tree.append(sector_node)

        return tree

    async def get_theme_stats(self) -> dict[str, int]:
        """Get theme counts grouped by level. Single query, ~4 rows returned."""
        result = await self.db.execute(
            select(ThemeHierarchy.level, func.count())
            .group_by(ThemeHierarchy.level)
        )
        counts = dict(result.all())
        return {
            "sectors": counts.get("sector", 0),
            "industries": counts.get("industry", 0),
            "themes": counts.get("theme", 0),
            "narratives": counts.get("narrative", 0),
        }

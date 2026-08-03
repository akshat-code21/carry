"""Step 3: Theme→Ticker Mapping.

Enriches theme-ticker mappings by combining curated seed data
with LLM-generated suggestions, then updates speaker-ticker aggregation.
"""

import logging
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.theme import ThemeHierarchy, ThemeMention
from src.models.video import Video
from src.services.aggregation_service import AggregationService
from src.services.interfaces import LLMProvider
from src.services.theme_service import ThemeService

logger = logging.getLogger(__name__)


MIN_THEME_TICKER_RELEVANCE_SCORE = 0.85


class ThemeMappingPipeline:
    """Pipeline step 3: Enrich theme→ticker mappings and update aggregation."""

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: LLMProvider,
        theme_service: ThemeService,
        aggregation_service: AggregationService,
    ) -> None:
        self.db = db
        self.llm = llm_provider
        self.theme_service = theme_service
        self.aggregation_service = aggregation_service

    async def enrich_video_themes(self, video_id: uuid_mod.UUID) -> dict:
        """Enrich theme→ticker mappings for all themes mentioned in a video.

        For each theme mentioned:
        1. Look up curated ticker mappings
        2. If fewer than expected, call LLM for enrichment
        3. Merge and store new mappings
        4. Update speaker-ticker aggregation for the channel

        Returns a summary of new mappings added.
        """
        # Get all theme mentions for this video
        mention_result = await self.db.execute(
            select(ThemeMention).where(ThemeMention.video_id == video_id)
        )
        mentions = mention_result.scalars().all()

        if not mentions:
            return {"new_mappings": 0}

        # Get unique theme IDs
        theme_ids = list({m.theme_id for m in mentions})
        new_mappings_count = 0

        for theme_id in theme_ids:
            # Get existing mappings
            existing = await self.theme_service.get_ticker_mappings(theme_id)
            existing_tickers = {m.ticker.upper() for m in existing}

            # Get the theme details for the LLM enrichment prompt
            theme_result = await self.db.execute(
                select(ThemeHierarchy).where(ThemeHierarchy.id == theme_id)
            )
            theme = theme_result.scalar_one_or_none()
            if not theme:
                continue

            # Get the narrative from the most relevant mention
            best_mention = max(
                [m for m in mentions if m.theme_id == theme_id],
                key=lambda m: m.relevance_score or 0,
            )
            narrative = best_mention.narrative or theme.description or ""

            # LLM enrichment pass
            try:
                suggested_tickers = await self.llm.enrich_theme_tickers(theme.name, narrative)

                for suggestion in suggested_tickers:
                    if suggestion.relevance_score < MIN_THEME_TICKER_RELEVANCE_SCORE:
                        logger.debug(
                            f"Skipping suggested ticker {suggestion.ticker} "
                            f"for theme '{theme.name}' due to low relevance score "
                            f"({suggestion.relevance_score} < "
                            f"{MIN_THEME_TICKER_RELEVANCE_SCORE})"
                        )
                        continue

                    ticker = suggestion.ticker.upper()
                    if ticker not in existing_tickers:
                        mapping = await self.theme_service.add_ticker_mapping(
                            theme_id=theme_id,
                            ticker=ticker,
                            relevance_score=suggestion.relevance_score,
                            source="llm",
                            notes=suggestion.reason,
                        )
                        # None when rejected as ETF / invalid
                        if mapping is not None:
                            existing_tickers.add(ticker)
                            new_mappings_count += 1

            except Exception as e:
                logger.warning(f"LLM ticker enrichment failed for theme '{theme.name}': {e}")

        # Update speaker-ticker aggregation for the channel
        video_result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = video_result.scalar_one_or_none()
        if video:
            await self.aggregation_service.update_channel_aggregation(video.channel_id)

        await self.db.flush()

        logger.info(f"Added {new_mappings_count} new ticker mappings for video {video_id}")
        return {"new_mappings": new_mappings_count}

    async def enrich_all_themes(self) -> dict:
        """Run enrichment on all themes that have fewer than 3 ticker mappings."""
        result = await self.db.execute(
            select(ThemeHierarchy).where(ThemeHierarchy.level == "theme")
        )
        themes = result.scalars().all()

        total_new = 0
        for theme in themes:
            existing = await self.theme_service.get_ticker_mappings(theme.id)
            if len(existing) < 3:
                try:
                    suggested = await self.llm.enrich_theme_tickers(
                        theme.name, theme.description or ""
                    )
                    existing_tickers = {m.ticker.upper() for m in existing}

                    for suggestion in suggested:
                        if suggestion.relevance_score < MIN_THEME_TICKER_RELEVANCE_SCORE:
                            continue

                        ticker = suggestion.ticker.upper()
                        if ticker not in existing_tickers:
                            mapping = await self.theme_service.add_ticker_mapping(
                                theme_id=theme.id,
                                ticker=ticker,
                                relevance_score=suggestion.relevance_score,
                                source="llm",
                                notes=suggestion.reason,
                            )
                            if mapping is not None:
                                existing_tickers.add(ticker)
                                total_new += 1
                except Exception as e:
                    logger.warning(f"Enrichment failed for theme '{theme.name}': {e}")

        await self.db.flush()
        return {"new_mappings": total_new}

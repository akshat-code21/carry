"""Step 2: LLM-Powered Content Analysis.

Splits transcripts into chunks, sends them to the LLM for analysis,
and stores extracted themes, predictions, and entity data.
"""

import logging
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction import Prediction
from src.models.transcript_segment import TranscriptSegment
from src.models.video import Video
from src.services.interfaces import LLMProvider, TranscriptSegmentDTO
from src.services.theme_service import ThemeService

logger = logging.getLogger(__name__)

# ~30 second chunks as specified in plan_1.md
CHUNK_DURATION_SEC = 30


class AnalysisPipeline:
    """Pipeline step 2: LLM analysis of transcript content."""

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: LLMProvider,
        theme_service: ThemeService,
    ) -> None:
        self.db = db
        self.llm = llm_provider
        self.theme_service = theme_service

    async def analyze_video(self, video_id: uuid_mod.UUID) -> dict:
        """Run LLM analysis on all transcript segments for a video.

        Chunks segments into ~30-second windows, sends each to the LLM,
        and stores extracted themes and predictions.

        Returns a summary of what was extracted.
        """
        # Fetch video and its transcript segments
        video_result = await self.db.execute(
            select(Video).where(Video.id == video_id)
        )
        video = video_result.scalar_one_or_none()
        if not video:
            raise ValueError(f"Video not found: {video_id}")

        if video.transcript_status != "fetched":
            raise ValueError(
                f"Video transcript not ready (status: {video.transcript_status})"
            )

        seg_result = await self.db.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.video_id == video_id)
            .order_by(TranscriptSegment.start_sec)
        )
        segments = list(seg_result.scalars().all())

        if not segments:
            logger.warning(f"No transcript segments found for video: {video.title}")
            return {"themes": 0, "predictions": 0}

        # Chunk segments into ~30-second windows
        chunks = self._chunk_segments(segments)

        total_themes = 0
        total_predictions = 0

        for chunk_segments, chunk_db_segments in chunks:
            try:
                # Send chunk to LLM for analysis
                result = await self.llm.analyze_transcript_chunk(
                    chunk_segments, video.title
                )

                # Process extracted themes
                for extracted_theme in result.themes:
                    matched_theme = await self.theme_service.match_theme(
                        extracted_theme
                    )
                    if matched_theme and chunk_db_segments:
                        # Use the first segment in the chunk for the mention
                        await self.theme_service.create_theme_mention(
                            video_id=video.id,
                            segment_id=chunk_db_segments[0].id,
                            theme_id=matched_theme.id,
                            sentiment=extracted_theme.sentiment,
                            relevance_score=extracted_theme.confidence,
                            mention_text=chunk_db_segments[0].text[:500],
                            narrative=extracted_theme.narrative,
                        )
                        total_themes += 1

                # Process extracted predictions
                for extracted_pred in result.predictions:
                    prediction = Prediction(
                        video_id=video.id,
                        segment_id=(
                            chunk_db_segments[0].id if chunk_db_segments else None
                        ),
                        ticker=extracted_pred.ticker,
                        prediction_text=extracted_pred.text,
                        direction=extracted_pred.direction,
                        confidence=extracted_pred.confidence,
                        timeframe_hint=extracted_pred.timeframe,
                        extracted_by="claude-sonnet-4",
                    )
                    self.db.add(prediction)
                    total_predictions += 1

            except Exception as e:
                logger.error(
                    f"LLM analysis failed for chunk in video {video.title}: {e}"
                )
                continue

        # Mark video as processed
        video.processed = True
        await self.db.flush()

        logger.info(
            f"Analysis complete for '{video.title}': "
            f"{total_themes} themes, {total_predictions} predictions"
        )

        return {
            "themes": total_themes,
            "predictions": total_predictions,
        }

    def _chunk_segments(
        self, segments: list[TranscriptSegment]
    ) -> list[tuple[list[TranscriptSegmentDTO], list[TranscriptSegment]]]:
        """Group transcript segments into ~30-second chunks.

        Returns list of (DTOs for LLM, DB segments for reference) tuples.
        """
        if not segments:
            return []

        chunks: list[tuple[list[TranscriptSegmentDTO], list[TranscriptSegment]]] = []
        current_dtos: list[TranscriptSegmentDTO] = []
        current_db_segs: list[TranscriptSegment] = []
        chunk_start = segments[0].start_sec

        for seg in segments:
            current_dtos.append(
                TranscriptSegmentDTO(
                    start_sec=seg.start_sec,
                    end_sec=seg.end_sec,
                    text=seg.text,
                )
            )
            current_db_segs.append(seg)

            # Check if chunk duration exceeded
            if seg.end_sec - chunk_start >= CHUNK_DURATION_SEC:
                chunks.append((current_dtos, current_db_segs))
                current_dtos = []
                current_db_segs = []
                chunk_start = seg.end_sec

        # Don't forget the last chunk
        if current_dtos:
            chunks.append((current_dtos, current_db_segs))

        return chunks

    async def analyze_all_unprocessed(self) -> list[dict]:
        """Run analysis on all videos with fetched transcripts that haven't been processed."""
        result = await self.db.execute(
            select(Video).where(
                Video.transcript_status == "fetched",
                Video.processed.is_(False),
            )
        )
        videos = result.scalars().all()

        summaries = []
        for video in videos:
            try:
                summary = await self.analyze_video(video.id)
                summary["video_id"] = str(video.id)
                summary["video_title"] = video.title
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Failed to analyze video {video.title}: {e}")
                summaries.append(
                    {
                        "video_id": str(video.id),
                        "video_title": video.title,
                        "error": str(e),
                    }
                )

        return summaries

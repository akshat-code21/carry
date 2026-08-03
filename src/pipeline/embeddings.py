"""Step 4: Embedding Generation.

Generates vector embeddings for transcript segments using the API-based embedding provider.
Stores embeddings in the pgvector column for semantic search.
"""

import logging
import uuid as uuid_mod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transcript_segment import TranscriptSegment
from src.services.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)

# Process embeddings in batches to manage memory and API rate limits
BATCH_SIZE = 50


class EmbeddingPipeline:
    """Pipeline step 4: Generate and store embeddings for semantic search."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.db = db
        self.embedding_provider = embedding_provider

    async def embed_video_segments(self, video_id: uuid_mod.UUID) -> int:
        """Generate embeddings for all transcript segments of a video.

        Only processes segments that don't already have embeddings.
        Returns the number of segments embedded.
        """
        # Fetch segments without embeddings
        result = await self.db.execute(
            select(TranscriptSegment)
            .where(
                TranscriptSegment.video_id == video_id,
                TranscriptSegment.embedding.is_(None),
            )
            .order_by(TranscriptSegment.start_sec)
        )
        segments = list(result.scalars().all())

        if not segments:
            logger.info(f"No segments need embedding for video {video_id}")
            return 0

        embedded_count = 0

        # Process in batches
        for i in range(0, len(segments), BATCH_SIZE):
            batch = segments[i : i + BATCH_SIZE]
            texts = [seg.text for seg in batch]

            try:
                embeddings = await self.embedding_provider.embed(texts)

                for seg, embedding in zip(batch, embeddings):
                    seg.embedding = embedding
                    embedded_count += 1

                await self.db.flush()

            except Exception as e:
                logger.error(f"Embedding generation failed for batch {i // BATCH_SIZE}: {e}")
                continue

        logger.info(f"Generated {embedded_count} embeddings for video {video_id}")
        return embedded_count

    async def embed_all_pending(self) -> dict:
        """Generate embeddings for all segments across all videos that are missing embeddings.

        Returns a summary of work done.
        """
        # Find all segments without embeddings
        result = await self.db.execute(
            select(TranscriptSegment.video_id)
            .where(TranscriptSegment.embedding.is_(None))
            .distinct()
        )
        video_ids = [row[0] for row in result.all()]

        total_embedded = 0
        videos_processed = 0

        for video_id in video_ids:
            count = await self.embed_video_segments(video_id)
            total_embedded += count
            videos_processed += 1

        logger.info(
            f"Embedding complete: {total_embedded} segments across {videos_processed} videos"
        )
        return {
            "videos_processed": videos_processed,
            "segments_embedded": total_embedded,
        }

"""Initial schema - all tables.

Revision ID: 001
Revises: None
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # channels
    op.create_table(
        "channels",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("youtube_channel_id", sa.String(255), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("thumbnail_url", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_channels_youtube_channel_id", "channels", ["youtube_channel_id"])

    # videos
    op.create_table(
        "videos",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("channel_id", sa.UUID(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("youtube_video_id", sa.String(255), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("duration_sec", sa.Integer()),
        sa.Column("thumbnail_url", sa.String(1000)),
        sa.Column("view_count", sa.BigInteger()),
        sa.Column("transcript_status", sa.String(50), server_default="pending"),
        sa.Column("processed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_videos_channel_id", "videos", ["channel_id"])
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"])

    # transcript_segments
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384)),
    )
    op.create_index("ix_transcript_segments_video_id", "transcript_segments", ["video_id"])

    # theme_hierarchy
    op.create_table(
        "theme_hierarchy",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("parent_id", sa.UUID(), sa.ForeignKey("theme_hierarchy.id")),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_theme_hierarchy_parent_id", "theme_hierarchy", ["parent_id"])
    op.create_index("ix_theme_hierarchy_name", "theme_hierarchy", ["name"])

    # theme_mentions
    op.create_table(
        "theme_mentions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("segment_id", sa.UUID(), sa.ForeignKey("transcript_segments.id"), nullable=False),
        sa.Column("theme_id", sa.UUID(), sa.ForeignKey("theme_hierarchy.id"), nullable=False),
        sa.Column("sentiment", sa.String(50)),
        sa.Column("relevance_score", sa.Float()),
        sa.Column("mention_text", sa.Text()),
        sa.Column("narrative", sa.Text()),
    )
    op.create_index("ix_theme_mentions_video_id", "theme_mentions", ["video_id"])
    op.create_index("ix_theme_mentions_segment_id", "theme_mentions", ["segment_id"])
    op.create_index("ix_theme_mentions_theme_id", "theme_mentions", ["theme_id"])

    # theme_ticker_mappings
    op.create_table(
        "theme_ticker_mappings",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("theme_id", sa.UUID(), sa.ForeignKey("theme_hierarchy.id"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("relevance_score", sa.Float()),
        sa.Column("source", sa.String(50), server_default="curated"),
        sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_theme_ticker_mappings_theme_id", "theme_ticker_mappings", ["theme_id"])
    op.create_index("ix_theme_ticker_mappings_ticker", "theme_ticker_mappings", ["ticker"])

    # predictions
    op.create_table(
        "predictions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("segment_id", sa.UUID(), sa.ForeignKey("transcript_segments.id")),
        sa.Column("theme_id", sa.UUID(), sa.ForeignKey("theme_hierarchy.id")),
        sa.Column("ticker", sa.String(20)),
        sa.Column("prediction_text", sa.Text(), nullable=False),
        sa.Column("direction", sa.String(50)),
        sa.Column("confidence", sa.Float()),
        sa.Column("timeframe_hint", sa.String(100)),
        sa.Column("extracted_by", sa.String(100)),
        sa.Column("accurate", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_predictions_video_id", "predictions", ["video_id"])
    op.create_index("ix_predictions_segment_id", "predictions", ["segment_id"])
    op.create_index("ix_predictions_theme_id", "predictions", ["theme_id"])
    op.create_index("ix_predictions_ticker", "predictions", ["ticker"])

    # performance_records
    op.create_table(
        "performance_records",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("video_id", sa.UUID(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("prediction_id", sa.UUID(), sa.ForeignKey("predictions.id"), nullable=False),
        sa.Column("price_at_video", sa.Float()),
        sa.Column("price_1d", sa.Float()),
        sa.Column("price_1w", sa.Float()),
        sa.Column("price_1m", sa.Float()),
        sa.Column("return_1d", sa.Float()),
        sa.Column("return_1w", sa.Float()),
        sa.Column("return_1m", sa.Float()),
        sa.Column("direction_accurate", sa.Boolean()),
    )
    op.create_index("ix_performance_records_ticker", "performance_records", ["ticker"])
    op.create_index("ix_performance_records_video_id", "performance_records", ["video_id"])
    op.create_index("ix_performance_records_prediction_id", "performance_records", ["prediction_id"])

    # speaker_ticker_aggregation
    op.create_table(
        "speaker_ticker_aggregation",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("channel_id", sa.UUID(), sa.ForeignKey("channels.id"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("total_mentions", sa.Integer(), server_default="0"),
        sa.Column("explicit_mentions", sa.Integer(), server_default="0"),
        sa.Column("implicit_mentions", sa.Integer(), server_default="0"),
        sa.Column("avg_sentiment", sa.Float()),
        sa.Column("weighted_relevance", sa.Float()),
        sa.Column("last_mentioned_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_speaker_ticker_agg_channel_id", "speaker_ticker_aggregation", ["channel_id"])
    op.create_index("ix_speaker_ticker_agg_ticker", "speaker_ticker_aggregation", ["ticker"])

    # Create GIN indexes for full-text search
    op.execute(
        "CREATE INDEX ix_transcript_segments_text_search "
        "ON transcript_segments USING GIN (to_tsvector('english', text))"
    )
    op.execute(
        "CREATE INDEX ix_predictions_text_search "
        "ON predictions USING GIN (to_tsvector('english', prediction_text))"
    )

    # Create HNSW index for vector similarity search
    op.execute(
        "CREATE INDEX ix_transcript_segments_embedding_cosine "
        "ON transcript_segments USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("speaker_ticker_aggregation")
    op.drop_table("performance_records")
    op.drop_table("predictions")
    op.drop_table("theme_ticker_mappings")
    op.drop_table("theme_mentions")
    op.drop_table("theme_hierarchy")
    op.drop_table("transcript_segments")
    op.drop_table("videos")
    op.drop_table("channels")
    op.execute("DROP EXTENSION IF EXISTS vector")

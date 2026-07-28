"""Add WebSub channel tracking, video ingest status, and activity events.

Revision ID: 004
Revises: 003
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Channel WebSub / discovery columns
    op.add_column(
        "channels",
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "channels",
        sa.Column("websub_subscribed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "channels",
        sa.Column("websub_lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "channels",
        sa.Column(
            "websub_status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
    )

    # Video auto-ingest state
    op.add_column(
        "videos",
        sa.Column(
            "ingest_status",
            sa.String(50),
            nullable=False,
            server_default="discovered",
        ),
    )
    op.add_column(
        "videos",
        sa.Column(
            "transcript_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Mark already-processed videos as completed for consistency
    op.execute(
        """
        UPDATE videos
        SET ingest_status = CASE
            WHEN processed = true THEN 'completed'
            WHEN transcript_status = 'fetched' THEN 'ready_for_analysis'
            WHEN transcript_status = 'failed' THEN 'failed'
            ELSE 'discovered'
        END
        """
    )

    # Activity events table
    op.create_table(
        "activity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.id"),
            nullable=False,
        ),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id"),
            nullable=True,
        ),
        sa.Column("youtube_video_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "event_type",
            "youtube_video_id",
            name="uq_activity_event_type_youtube_video",
        ),
    )
    op.create_index("ix_activity_events_event_type", "activity_events", ["event_type"])
    op.create_index("ix_activity_events_channel_id", "activity_events", ["channel_id"])
    op.create_index("ix_activity_events_video_id", "activity_events", ["video_id"])
    op.create_index(
        "ix_activity_events_youtube_video_id", "activity_events", ["youtube_video_id"]
    )
    op.create_index("ix_activity_events_created_at", "activity_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_activity_events_created_at", table_name="activity_events")
    op.drop_index("ix_activity_events_youtube_video_id", table_name="activity_events")
    op.drop_index("ix_activity_events_video_id", table_name="activity_events")
    op.drop_index("ix_activity_events_channel_id", table_name="activity_events")
    op.drop_index("ix_activity_events_event_type", table_name="activity_events")
    op.drop_table("activity_events")

    op.drop_column("videos", "transcript_attempts")
    op.drop_column("videos", "ingest_status")

    op.drop_column("channels", "websub_status")
    op.drop_column("channels", "websub_lease_expires_at")
    op.drop_column("channels", "websub_subscribed_at")
    op.drop_column("channels", "last_checked_at")

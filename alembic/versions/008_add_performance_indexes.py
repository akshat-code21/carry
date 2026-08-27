"""Add performance indexes for theme_hierarchy.level and videos.published_at.

Revision ID: 008_perf_indexes
Create Date: 2026-08-27
"""

from alembic import op

# revision identifiers
revision = "008_perf_indexes"
down_revision = "f8a92b113478"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index on theme_hierarchy.level — eliminates seq-scan of ~2,945 rows
    # when filtering by level (used by stats endpoint and hierarchy builder)
    op.create_index(
        "ix_theme_hierarchy_level",
        "theme_hierarchy",
        ["level"],
    )

    # Index on videos.published_at DESC — supports ORDER BY in dashboard
    # and list_videos queries
    op.create_index(
        "ix_videos_published_at",
        "videos",
        ["published_at"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("ix_videos_published_at", table_name="videos")
    op.drop_index("ix_theme_hierarchy_level", table_name="theme_hierarchy")

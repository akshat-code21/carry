"""add search_answers cache table

Revision ID: 007
Revises: a1b2c3d4e5f7
Create Date: 2026-08-24 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "search_answers",
        sa.Column("query_hash", sa.String(64), primary_key=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("answer_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("search_answers")

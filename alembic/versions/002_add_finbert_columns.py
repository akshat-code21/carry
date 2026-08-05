"""Add FinBERT sentiment columns.

Adds llm_sentiment and finbert_confidence to theme_mentions,
and llm_direction and finbert_confidence to predictions.

Revision ID: 002
Revises: 001
Create Date: 2026-07-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # theme_mentions: add FinBERT audit columns
    op.add_column(
        "theme_mentions",
        sa.Column("llm_sentiment", sa.String(50), nullable=True),
    )
    op.add_column(
        "theme_mentions",
        sa.Column("finbert_confidence", sa.Float(), nullable=True),
    )

    # predictions: add FinBERT audit columns
    op.add_column(
        "predictions",
        sa.Column("llm_direction", sa.String(50), nullable=True),
    )
    op.add_column(
        "predictions",
        sa.Column("finbert_confidence", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("predictions", "finbert_confidence")
    op.drop_column("predictions", "llm_direction")
    op.drop_column("theme_mentions", "finbert_confidence")
    op.drop_column("theme_mentions", "llm_sentiment")

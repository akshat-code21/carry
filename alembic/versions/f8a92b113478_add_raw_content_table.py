"""add_raw_content_table

Revision ID: f8a92b113478
Revises: e4e38ec36752
Create Date: 2026-07-29 17:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8a92b113478'
down_revision: str | None = 'e4e38ec36752'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'raw_content',
        sa.Column('id', sa.String(length=128), nullable=False),
        sa.Column('symbol', sa.String(length=16), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=128), nullable=True),
        sa.Column('url', sa.String(length=512), nullable=True),
        sa.Column('engagement_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_metadata', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_content_symbol'), 'raw_content', ['symbol'], unique=False)
    op.create_index(op.f('ix_raw_content_source'), 'raw_content', ['source'], unique=False)
    op.create_index(op.f('ix_raw_content_content_hash'), 'raw_content', ['content_hash'], unique=False)
    op.create_index(op.f('ix_raw_content_created_at'), 'raw_content', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_raw_content_created_at'), table_name='raw_content')
    op.drop_index(op.f('ix_raw_content_content_hash'), table_name='raw_content')
    op.drop_index(op.f('ix_raw_content_source'), table_name='raw_content')
    op.drop_index(op.f('ix_raw_content_symbol'), table_name='raw_content')
    op.drop_table('raw_content')

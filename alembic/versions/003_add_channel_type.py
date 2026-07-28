"""Add channel_type column.

Adds channel_type to channels table to distinguish individual creator
channels from institutional channels (Fundstrat, Morgan Stanley, etc.).
Defaults to 'individual' for all existing channels.

Revision ID: 003
Revises: 002
Create Date: 2026-07-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "channels",
        sa.Column(
            "channel_type",
            sa.String(50),
            nullable=False,
            server_default="individual",
        ),
    )


def downgrade() -> None:
    op.drop_column("channels", "channel_type")

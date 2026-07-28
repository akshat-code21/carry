"""Dedupe speaker_ticker_aggregation and add unique (channel_id, ticker).

Concurrent process_video tasks for the same channel could insert multiple
rows for the same (channel_id, ticker). The aggregation upsert then failed
with MultipleResultsFound on scalar_one_or_none().

Revision ID: 005
Revises: 004
Create Date: 2026-07-28
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Normalize tickers to uppercase so case variants collapse under the unique key.
    op.execute(
        "UPDATE speaker_ticker_aggregation SET ticker = UPPER(ticker) "
        "WHERE ticker <> UPPER(ticker)"
    )

    # Keep one row per (channel_id, ticker): prefer highest total_mentions,
    # then most recently updated. Delete the rest.
    op.execute(
        """
        DELETE FROM speaker_ticker_aggregation a
        USING speaker_ticker_aggregation b
        WHERE a.channel_id = b.channel_id
          AND a.ticker = b.ticker
          AND a.id <> b.id
          AND (
            COALESCE(a.total_mentions, 0) < COALESCE(b.total_mentions, 0)
            OR (
              COALESCE(a.total_mentions, 0) = COALESCE(b.total_mentions, 0)
              AND COALESCE(a.updated_at, '-infinity'::timestamptz)
                < COALESCE(b.updated_at, '-infinity'::timestamptz)
            )
            OR (
              COALESCE(a.total_mentions, 0) = COALESCE(b.total_mentions, 0)
              AND COALESCE(a.updated_at, '-infinity'::timestamptz)
                = COALESCE(b.updated_at, '-infinity'::timestamptz)
              AND a.id::text < b.id::text
            )
          )
        """
    )

    op.create_unique_constraint(
        "uq_speaker_ticker_agg_channel_ticker",
        "speaker_ticker_aggregation",
        ["channel_id", "ticker"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_speaker_ticker_agg_channel_ticker",
        "speaker_ticker_aggregation",
        type_="unique",
    )

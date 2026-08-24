"""add_hfi_tables

Revision ID: a1b2c3d4e5f6
Revises: 006
Create Date: 2026-08-24 10:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enum types
hfi_source_type = sa.Enum(
    "sec_13f", "website", "youtube", "rss", "twitter", "custom",
    name="hfi_source_type",
)
hfi_content_type = sa.Enum(
    "filing", "article", "video", "newsletter", "website_page", "custom",
    name="hfi_content_type",
)
hfi_processing_status = sa.Enum(
    "pending", "processing", "completed", "failed", "skipped",
    name="hfi_processing_status",
)
portfolio_change_type = sa.Enum(
    "new_position", "increased", "decreased", "closed", "unchanged",
    name="portfolio_change_type",
)
hfi_entity_type = sa.Enum(
    "company", "ticker", "person", "theme", "sector", "macro_theme",
    name="hfi_entity_type",
)
hfi_sentiment = sa.Enum("bullish", "bearish", "neutral", "mixed", name="hfi_sentiment")
hfi_conviction_level = sa.Enum("high", "medium", "low", "unknown", name="hfi_conviction_level")
hfi_report_type = sa.Enum(
    "investor_report", "daily_digest", "event_report",
    name="hfi_report_type",
)
hfi_alert_type = sa.Enum(
    "new_filing", "new_company_mention", "new_thesis",
    "high_conviction", "portfolio_change", "daily_digest_ready",
    name="hfi_alert_type",
)
hfi_alert_severity = sa.Enum("low", "medium", "high", "critical", name="hfi_alert_severity")


def upgrade() -> None:
    # 1. investors
    op.create_table(
        "investors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("cik_number", sa.String, nullable=True, index=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_investors_user_id", "investors", ["user_id"])
    op.create_index("idx_investors_active", "investors", ["user_id", "is_active"])

    # 2. hfi_sources
    op.create_table(
        "hfi_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", hfi_source_type, nullable=False),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=True),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_frequency_hours", sa.Integer, nullable=False, server_default="24"),
        sa.Column("consecutive_failures", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_hfi_sources_investor_id", "hfi_sources", ["investor_id"])
    op.create_index("idx_hfi_sources_type", "hfi_sources", ["source_type"])

    # 3. content_items
    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("hfi_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_type", hfi_content_type, nullable=False),
        sa.Column("title", sa.String, nullable=True),
        sa.Column("url", sa.String, nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("cleaned_text", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String, nullable=False),
        sa.Column("processing_status", hfi_processing_status, nullable=False, server_default="pending"),
        sa.Column("processing_error", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("extracted_entities", postgresql.JSONB, nullable=True),
        sa.Column("extracted_theses", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("content_hash", name="unique_content_item_hash"),
    )
    op.create_index("idx_content_source_id", "content_items", ["source_id"])
    op.create_index("idx_content_investor_id", "content_items", ["investor_id"])
    op.create_index("idx_content_published", "content_items", ["investor_id", "published_at"])
    op.create_index("idx_content_type", "content_items", ["investor_id", "content_type"])

    # 4. portfolio_changes
    op.create_table(
        "portfolio_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker_symbol", sa.String, nullable=False),
        sa.Column("company_name", sa.String, nullable=True),
        sa.Column("cusip", sa.String, nullable=True),
        sa.Column("change_type", portfolio_change_type, nullable=False),
        sa.Column("shares_previous", sa.BigInteger, server_default="0"),
        sa.Column("shares_current", sa.BigInteger, nullable=False),
        sa.Column("value_usd", sa.BigInteger, nullable=True),
        sa.Column("percent_of_portfolio", sa.Numeric(6, 3), nullable=True),
        sa.Column("filing_period", sa.String, nullable=False),
        sa.Column("report_date", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_portfolio_investor", "portfolio_changes", ["investor_id"])
    op.create_index("idx_portfolio_ticker", "portfolio_changes", ["ticker_symbol"])
    op.create_index("idx_portfolio_period", "portfolio_changes", ["investor_id", "filing_period"])
    op.create_index("idx_portfolio_change", "portfolio_changes", ["change_type"])

    # 5. ticker_cache
    op.create_table(
        "ticker_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String, nullable=False),
        sa.Column("cusip", sa.String, nullable=True),
        sa.Column("ticker", sa.String, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("company_name", name="uq_ticker_cache_company"),
    )
    op.create_index(
        "idx_ticker_cache_cusip",
        "ticker_cache",
        ["cusip"],
        postgresql_where=sa.text("cusip IS NOT NULL"),
    )

    # 6. extracted_mentions
    op.create_table(
        "extracted_mentions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", hfi_entity_type, nullable=False),
        sa.Column("entity_name", sa.String, nullable=False),
        sa.Column("ticker_symbol", sa.String, nullable=True),
        sa.Column("sentiment", hfi_sentiment, nullable=True),
        sa.Column("conviction_level", hfi_conviction_level, nullable=True),
        sa.Column("context_snippet", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_mentions_content", "extracted_mentions", ["content_item_id"])
    op.create_index("idx_mentions_investor", "extracted_mentions", ["investor_id"])
    op.create_index(
        "idx_mentions_ticker",
        "extracted_mentions",
        ["ticker_symbol"],
        postgresql_where=sa.text("ticker_symbol IS NOT NULL"),
    )
    op.create_index("idx_mentions_entity", "extracted_mentions", ["entity_type", "entity_name"])

    # 7. hfi_reports
    op.create_table(
        "hfi_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("report_type", hfi_report_type, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column(
            "source_item_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_hfi_reports_user_id", "hfi_reports", ["user_id"])
    op.create_index("idx_hfi_reports_type", "hfi_reports", ["user_id", "report_type"])
    op.create_index("idx_hfi_reports_generated", "hfi_reports", ["user_id", "generated_at"])

    # 8. hfi_alerts
    op.create_table(
        "hfi_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "investor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("hfi_reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("alert_type", hfi_alert_type, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("severity", hfi_alert_severity, nullable=False, server_default="medium"),
        sa.Column("score", sa.Integer, nullable=False, server_default="50"),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("email_sent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="chk_hfi_alert_score_range"),
    )
    op.create_index("idx_hfi_alerts_user_unread", "hfi_alerts", ["user_id", "is_read", "created_at"])
    op.create_index("idx_hfi_alerts_type", "hfi_alerts", ["alert_type"])


def downgrade() -> None:
    op.drop_table("hfi_alerts")
    op.drop_table("hfi_reports")
    op.drop_table("extracted_mentions")
    op.drop_table("ticker_cache")
    op.drop_table("portfolio_changes")
    op.drop_table("content_items")
    op.drop_table("hfi_sources")
    op.drop_table("investors")

    # Drop enum types
    for enum_type in [
        hfi_alert_severity, hfi_alert_type, hfi_report_type,
        hfi_conviction_level, hfi_sentiment, hfi_entity_type,
        portfolio_change_type, hfi_processing_status,
        hfi_content_type, hfi_source_type,
    ]:
        enum_type.drop(op.get_bind(), checkfirst=True)

"""Cached LLM-synthesized answers for search queries."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class SearchAnswer(Base):
    """One synthesized answer per normalized search query (24h TTL)."""

    __tablename__ = "search_answers"

    # sha256 of the whitespace-normalized, lowercased query
    query_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""Performance record model - tracks price changes after predictions."""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False, index=True
    )
    price_at_video: Mapped[float | None] = mapped_column(Float)
    price_1d: Mapped[float | None] = mapped_column(Float)
    price_1w: Mapped[float | None] = mapped_column(Float)
    price_1m: Mapped[float | None] = mapped_column(Float)
    return_1d: Mapped[float | None] = mapped_column(Float)
    return_1w: Mapped[float | None] = mapped_column(Float)
    return_1m: Mapped[float | None] = mapped_column(Float)
    direction_accurate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    video = relationship("Video", back_populates="performance_records")
    prediction = relationship("Prediction", back_populates="performance_records")

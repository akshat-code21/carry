"""QuotaUsage model — tracks monthly Adanos API budget consumption."""

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    __table_args__ = (
        UniqueConstraint("provider", "period", name="uq_quota_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    period: Mapped[str] = mapped_column(String(7))
    used_requests: Mapped[int] = mapped_column(Integer, default=0)

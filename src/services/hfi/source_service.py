"""Source service — auto-creates SEC 13F sources for investors."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.hfi_source import HfiSource


def sec_13f_source_url(cik: str) -> str:
    """EDGAR company filings browse URL for a CIK — used as the canonical source URL."""
    cik_padded = cik.zfill(10)
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik_padded}&type=13F"


async def ensure_sec_13f_source(
    db: AsyncSession,
    investor_id: uuid.UUID,
    investor_name: str,
    cik_number: str,
) -> HfiSource | None:
    """Auto-create (or update) the active `sec_13f` source for an investor.

    Called when an investor is created/updated with a CIK so that 13F
    ingestion works without any manual source setup.
    """
    result = await db.execute(
        select(HfiSource).where(
            HfiSource.investor_id == investor_id, HfiSource.source_type == "sec_13f"
        )
    )
    source = result.scalars().first()

    if source:
        config = dict(source.config or {})
        config["cik_number"] = cik_number
        source.config = config
        source.is_active = True
        await db.flush()
        await db.refresh(source)
        return source

    source = HfiSource(
        investor_id=investor_id,
        source_type="sec_13f",
        url=sec_13f_source_url(cik_number),
        label=f"{investor_name} SEC 13F",
        check_frequency_hours=24,
        is_active=True,
        config={"cik_number": cik_number},
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


async def create_source(
    db: AsyncSession,
    investor_id: uuid.UUID,
    source_type: str,
    url: str,
    label: str | None = None,
    config: dict | None = None,
) -> HfiSource:
    source = HfiSource(
        investor_id=investor_id,
        source_type=source_type,
        url=url,
        label=label,
        config=config or {},
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


async def delete_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    from src.models.investor import Investor

    result = await db.execute(
        select(HfiSource)
        .join(Investor, Investor.id == HfiSource.investor_id)
        .where(HfiSource.id == source_id, Investor.user_id == user_id)
    )
    source = result.scalars().first()
    if not source:
        return False
    await db.delete(source)
    await db.commit()
    return True

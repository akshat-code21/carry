"""
HFI background jobs — ingestion and processing.
Combined from Pet-Project's ingestion_job.py and processing_job.py.
Uses yt-chatter's async session factory.
"""

import hashlib
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import func, select

from src.database import async_session_factory
from src.models.content_item import ContentItem
from src.models.hfi_source import HfiSource
from src.models.investor import Investor
from src.services.hfi.ingestion.content_hasher import compute_hash

logger = structlog.get_logger()

BATCH_SIZE = 10


# ---------------------------------------------------------------------------
# Ingestion: fetch raw content from active sources
# ---------------------------------------------------------------------------


async def run_ingestion_for_investor(investor_id) -> dict:
    """Trigger ingestion for ALL active sources belonging to one investor."""
    investor_uuid = (
        investor_id if isinstance(investor_id, uuid.UUID) else uuid.UUID(str(investor_id))
    )

    async with async_session_factory() as db:
        sources = (
            (
                await db.execute(
                    select(HfiSource).where(
                        HfiSource.investor_id == investor_uuid, HfiSource.is_active.is_(True)
                    )
                )
            )
            .scalars()
            .all()
        )

    results = {"investor_id": str(investor_uuid), "processed": 0, "failed": 0, "skipped": 0}
    for source in sources:
        r = await _ingest_source(source)
        results["processed"] += r.get("new_items", 0)
        results["failed"] += 1 if r.get("error") else 0
        results["skipped"] += r.get("skipped", 0)

    # Update investor last_synced_at
    async with async_session_factory() as db:
        investor = (
            await db.execute(select(Investor).where(Investor.id == investor_uuid))
        ).scalar_one_or_none()
        if investor:
            investor.last_synced_at = datetime.now(timezone.utc)
            await db.commit()

    logger.info("Investor ingestion complete", **results)
    return results


async def _ingest_source(source) -> dict:
    """Fetch documents from a single source and persist new ContentItem records."""
    source_type = source.source_type
    source_id = str(source.id)
    investor_id = str(source.investor_id)

    log = logger.bind(source_id=source_id, source_type=source_type)

    # Inject CIK from investor into source config if missing for SEC
    if source_type == "sec_13f" and not source.config.get("cik_number"):
        async with async_session_factory() as db:
            investor = (
                await db.execute(select(Investor).where(Investor.id == uuid.UUID(investor_id)))
            ).scalar_one_or_none()
            if investor and investor.cik_number:
                source.config["cik_number"] = investor.cik_number

    try:
        docs = await _fetch_documents(source)
    except Exception as e:
        log.error("Fetch failed", error=str(e))
        await _increment_failure(source_id)
        return {"error": str(e)}

    if not docs:
        log.info("No new documents")
        return {"new_items": 0, "skipped": 0}

    new_count = 0
    skip_count = 0
    seen_hashes: set[str] = set()

    async with async_session_factory() as db:
        for doc in docs:
            raw_text = doc.page_content or ""

            sample = raw_text[:1000]
            if sample:
                non_printable = sum(
                    1 for c in sample if not c.isprintable() and c not in ("\n", "\r", "\t")
                )
                if non_printable / len(sample) > 0.15:
                    skip_count += 1
                    continue

            raw_text = raw_text.replace("\x00", "")

            if not raw_text.strip():
                skip_count += 1
                continue

            content_hash = compute_hash(raw_text)

            if content_hash in seen_hashes:
                skip_count += 1
                continue
            existing = (
                await db.execute(
                    select(ContentItem.id).where(ContentItem.content_hash == content_hash)
                )
            ).scalar_one_or_none()
            if existing:
                skip_count += 1
                continue
            seen_hashes.add(content_hash)

            content_type = _detect_content_type(source_type, doc.metadata)

            safe_metadata = {}
            for k, v in doc.metadata.items():
                if k in ("source", "title", "published"):
                    continue
                if isinstance(v, str):
                    safe_metadata[k] = v.replace("\x00", "")
                else:
                    safe_metadata[k] = v

            published_at = _parse_datetime(
                doc.metadata.get("published_at") or doc.metadata.get("report_date") or ""
            )

            item = ContentItem(
                source_id=uuid.UUID(source_id),
                investor_id=uuid.UUID(investor_id),
                content_type=content_type,
                title=doc.metadata.get("title") or None,
                url=doc.metadata.get("source") or None,
                raw_text=raw_text,
                content_hash=content_hash,
                published_at=published_at,
                processing_status="pending",
                extra_metadata={
                    "source_url": (doc.metadata.get("source", source.url) or "").replace("\x00", ""),
                    "title": (doc.metadata.get("title", "") or "").replace("\x00", ""),
                    "published_at": (doc.metadata.get("published", "") or "").replace("\x00", ""),
                    **safe_metadata,
                },
            )
            db.add(item)
            new_count += 1

        await db.commit()

    # Persist newest accession so future syncs only fetch newer filings
    if source_type == "sec_13f" and docs:
        newest = None
        for doc in docs:
            accession = (doc.metadata or {}).get("accession_number") or ""
            if not accession:
                continue
            if newest is None or accession > newest:
                newest = accession
        if newest:
            await _persist_last_accession(source_id, newest)

    await _reset_failure(source_id)
    await _update_last_checked(source_id)

    log.info("Ingestion done", new_items=new_count, skipped=skip_count)
    return {"new_items": new_count, "skipped": skip_count}


async def _fetch_documents(source) -> list:
    """Dispatch to the correct adapter/loader."""
    source_type = source.source_type

    if source_type == "sec_13f":
        from src.services.hfi.ingestion.sec_adapter import SECEdgarAdapter
        adapter = SECEdgarAdapter()
        return await adapter.fetch(source)
    else:
        logger.warning("Unknown source_type, skipping", source_type=source_type)
        return []


def _detect_content_type(source_type: str, metadata: dict) -> str:
    if source_type == "sec_13f":
        return "filing"
    if source_type == "youtube":
        return "video"
    if source_type == "rss":
        return "article"
    url = metadata.get("source", "").lower()
    if url.endswith(".pdf"):
        return "filing"
    return "article"


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


async def _persist_last_accession(source_id: str, accession: str) -> None:
    async with async_session_factory() as db:
        source = (
            await db.execute(select(HfiSource).where(HfiSource.id == uuid.UUID(source_id)))
        ).scalar_one_or_none()
        if source:
            config = dict(source.config or {})
            config["last_accession"] = accession
            source.config = config
            await db.commit()


async def _increment_failure(source_id: str) -> None:
    async with async_session_factory() as db:
        source = (
            await db.execute(select(HfiSource).where(HfiSource.id == uuid.UUID(source_id)))
        ).scalar_one_or_none()
        if source:
            source.consecutive_failures = (source.consecutive_failures or 0) + 1
            if source.consecutive_failures >= 5:
                source.is_active = False
            await db.commit()


async def _reset_failure(source_id: str) -> None:
    async with async_session_factory() as db:
        source = (
            await db.execute(select(HfiSource).where(HfiSource.id == uuid.UUID(source_id)))
        ).scalar_one_or_none()
        if source and source.consecutive_failures:
            source.consecutive_failures = 0
            await db.commit()


async def _update_last_checked(source_id: str) -> None:
    async with async_session_factory() as db:
        source = (
            await db.execute(select(HfiSource).where(HfiSource.id == uuid.UUID(source_id)))
        ).scalar_one_or_none()
        if source:
            source.last_checked_at = datetime.now(timezone.utc)
            await db.commit()


# ---------------------------------------------------------------------------
# Processing: run pending content items through the LangGraph pipeline
# ---------------------------------------------------------------------------


async def process_pending_content_for_investor(investor_id: str | uuid.UUID) -> dict:
    """Trigger processing for all pending content items belonging to a specific investor."""
    inv_uuid = investor_id if isinstance(investor_id, uuid.UUID) else uuid.UUID(str(investor_id))

    async with async_session_factory() as db:
        rows = (
            (
                await db.execute(
                    select(ContentItem)
                    .where(
                        ContentItem.investor_id == inv_uuid,
                        ContentItem.processing_status == "pending",
                    )
                    .order_by(
                        func.coalesce(
                            ContentItem.extra_metadata["filing_period"].as_string(), ""
                        ),
                        ContentItem.published_at.asc().nulls_last(),
                        ContentItem.created_at.asc(),
                    )
                )
            )
            .scalars()
            .all()
        )

        if not rows:
            return {"processed": 0, "failed": 0}

        for item in rows:
            item.processing_status = "processing"
        await db.commit()

    results = {"processed": 0, "failed": 0}
    for item in rows:
        success = await _run_pipeline_for_item(item)
        if success:
            results["processed"] += 1
        else:
            results["failed"] += 1

    logger.info("Investor content processing complete", investor_id=str(inv_uuid), **results)
    return results


async def _run_pipeline_for_item(item) -> bool:
    """Run a single ContentItem through the LangGraph pipeline."""
    from src.models.investor import Investor
    from src.models.user import User
    from src.pipeline.hfi.pipeline import run_pipeline
    from src.pipeline.hfi.state import PipelineState

    content_item_id = str(item.id)
    investor_id = str(item.investor_id)

    try:
        async with async_session_factory() as db:
            investor = (
                await db.execute(select(Investor).where(Investor.id == item.investor_id))
            ).scalar_one_or_none()
            user = (
                (await db.execute(select(User).where(User.id == investor.user_id))).scalar_one_or_none()
                if investor
                else None
            )

        if not investor or not user:
            logger.warning("Missing investor or user", content_item_id=content_item_id)
            await _mark_failed(content_item_id, "investor or user not found")
            return False

        source_url = (item.extra_metadata or {}).get("source_url", "")
        filing_period = (item.extra_metadata or {}).get("filing_period", "")
        holdings = (item.extra_metadata or {}).get("holdings", [])
        report_date = (item.extra_metadata or {}).get("report_date", "")

        initial_state: PipelineState = {
            "content_item_id": content_item_id,
            "investor_id": investor_id,
            "user_id": str(investor.user_id),
            "content_type": item.content_type,
            "raw_text": item.raw_text or "",
            "source_url": source_url,
            "cleaned_text": "",
            "chunks": [],
            "holdings": holdings,
            "entities": [],
            "theses": [],
            "portfolio_changes": [],
            "embeddings_stored": False,
            "report_generated": False,
            "report_triggered": False,
            "alerts_created": [],
            "error": None,
            "investor_name": investor.name,
            "filing_period": filing_period,
            "report_date": report_date,
        }

        import asyncio
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(None, run_pipeline, initial_state)

        if final_state.get("error"):
            await _mark_failed(content_item_id, final_state["error"])
            return False

        await _mark_completed(content_item_id, final_state)
        return True

    except Exception as e:
        logger.error("Pipeline execution error", content_item_id=content_item_id, error=str(e))
        await _mark_failed(content_item_id, str(e))
        return False


async def _mark_completed(content_item_id: str, final_state: dict) -> None:
    async with async_session_factory() as db:
        item = (
            await db.execute(
                select(ContentItem).where(ContentItem.id == uuid.UUID(content_item_id))
            )
        ).scalar_one_or_none()
        if item:
            item.processing_status = "completed"
            item.cleaned_text = final_state.get("cleaned_text", "")
            item.extracted_entities = final_state.get("entities", [])
            item.extracted_theses = final_state.get("theses", [])
            await db.commit()


async def _mark_failed(content_item_id: str, error: str) -> None:
    async with async_session_factory() as db:
        item = (
            await db.execute(
                select(ContentItem).where(ContentItem.id == uuid.UUID(content_item_id))
            )
        ).scalar_one_or_none()
        if item:
            item.processing_status = "failed"
            item.extra_metadata = {**(item.extra_metadata or {}), "error": error}
            await db.commit()

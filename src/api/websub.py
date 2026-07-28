"""YouTube WebSub (PubSubHubbub) callback endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.channel import Channel
from src.schemas import SimulateWebSubRequest, SimulateWebSubResponse
from src.services.websub_service import WebSubService
from src.tasks.pipeline_tasks import handle_websub_notification_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/websub", tags=["WebSub"])


@router.get("/callback")
async def websub_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_topic: str | None = Query(None, alias="hub.topic"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_lease_seconds: str | None = Query(None, alias="hub.lease_seconds"),
) -> Response:
    """Hub verification challenge — must echo hub.challenge as plain text."""
    if hub_mode not in ("subscribe", "unsubscribe"):
        raise HTTPException(status_code=400, detail="Invalid hub.mode")

    if not hub_challenge:
        raise HTTPException(status_code=400, detail="Missing hub.challenge")

    logger.info(
        "WebSub verification: mode=%s topic=%s lease=%s",
        hub_mode,
        hub_topic,
        hub_lease_seconds,
    )
    return Response(content=hub_challenge, media_type="text/plain", status_code=200)


@router.post("/callback")
async def websub_notify(request: Request) -> Response:
    """Receive Atom push notification from the Google WebSub hub.

    Verifies signature (if secret configured), enqueues discovery work, returns
    204 quickly so the hub does not time out.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature")

    websub = WebSubService()
    if not websub.verify_signature(body, signature):
        logger.warning("WebSub notification rejected: invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    if not body.strip():
        return Response(status_code=204)

    # Heavy work off the request path
    handle_websub_notification_task.delay(body.decode("utf-8", errors="replace"))
    logger.info("WebSub notification queued (%s bytes)", len(body))
    return Response(status_code=204)


@router.post("/simulate", response_model=SimulateWebSubResponse)
async def simulate_websub_push(
    request: SimulateWebSubRequest,
    db: AsyncSession = Depends(get_db),
) -> SimulateWebSubResponse:
    """Dry-run a new-upload WebSub notification without a real YouTube publish.

    Builds the same Atom XML the Google hub would POST, then runs the normal
    discovery path (optionally full auto-ingest).

    Modes:
      - full: discovery → video_detected → auto-ingest → process → video_processed
      - discovery_only: discovery → video_detected only (no transcript/LLM)

    Tips:
      - Use a **real** YouTube video id that is **not** already in your DB
        (e.g. an older episode you never backfilled) for a full pipeline test.
      - Re-using an id already in the DB is a no-op (already_exists).
    """
    mode = (request.mode or "full").strip().lower()
    if mode not in ("full", "discovery_only"):
        raise HTTPException(
            status_code=400,
            detail="mode must be 'full' or 'discovery_only'",
        )

    if not request.youtube_channel_id and not request.channel_id:
        raise HTTPException(
            status_code=400,
            detail="Provide youtube_channel_id or channel_id",
        )

    channel: Channel | None = None
    if request.channel_id:
        result = await db.execute(
            select(Channel).where(Channel.id == request.channel_id)
        )
        channel = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(Channel).where(
                Channel.youtube_channel_id == request.youtube_channel_id
            )
        )
        channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail="Channel not found — backfill/ingest the channel first",
        )

    youtube_channel_id = channel.youtube_channel_id
    websub = WebSubService()
    atom = websub.build_atom_notification(
        youtube_channel_id=youtube_channel_id,
        youtube_video_id=request.youtube_video_id.strip(),
        title=request.title,
    )

    enqueue_ingest = mode == "full"
    task = handle_websub_notification_task.delay(
        atom,
        enqueue_ingest,
        "simulate",
    )

    logger.info(
        "Simulated WebSub push queued: channel=%s video=%s mode=%s task=%s",
        youtube_channel_id,
        request.youtube_video_id,
        mode,
        task.id,
    )

    msg = (
        "Queued full auto-ingest path (detected → process → ready)."
        if enqueue_ingest
        else "Queued discovery-only path (video_detected activity, no processing)."
    )
    return SimulateWebSubResponse(
        task_id=task.id,
        status="queued",
        mode=mode,
        youtube_channel_id=youtube_channel_id,
        youtube_video_id=request.youtube_video_id.strip(),
        title=request.title,
        message=msg,
    )

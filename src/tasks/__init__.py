"""Celery app configuration and task definitions."""

from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "yt_chatter",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    imports=["src.tasks.pipeline_tasks"],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="yt_chatter",
    worker_prefetch_multiplier=1,  # One task at a time for API rate limiting
    broker_connection_retry_on_startup=True,
)

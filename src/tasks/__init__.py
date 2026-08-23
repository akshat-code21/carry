"""Celery app configuration and task definitions."""

from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "yt_chatter",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Beat schedule: WebSub lease renewal + optional RSS fallback + performance updates
_beat_schedule: dict = {
    "renew-websub-leases": {
        "task": "pipeline.renew_websub_leases",
        "schedule": crontab(minute=30, hour="*/6"),  # every 6 hours at :30
    },
    "update-performance-daily": {
        "task": "pipeline.update_performance",
        "schedule": crontab(minute=0, hour=6),  # daily 06:00 UTC
    },
    # Analytics maintenance
    "aggregate-platform-daily": {
        "task": "analytics.aggregate_platform_daily",
        "schedule": crontab(minute=0, hour=1),  # daily 01:00 UTC (previous day finalised)
    },
    "analytics-retention-cleanup": {
        "task": "analytics.retention_cleanup",
        "schedule": crontab(minute=30, hour=3),  # daily 03:30 UTC
    },
}

# Optional infrequent RSS fallback (0 disables)
if settings.discovery_fallback_poll_hours > 0:
    _poll_hours = max(1, settings.discovery_fallback_poll_hours)
    _beat_schedule["poll-channels-fallback"] = {
        "task": "pipeline.poll_channels_for_new_videos",
        # crontab hour step: every N hours
        "schedule": crontab(minute=15, hour=f"*/{_poll_hours}"),
    }

celery_app.conf.update(
    imports=["src.tasks.pipeline_tasks", "src.tasks.analytics_tasks"],
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="yt_chatter",
    worker_prefetch_multiplier=1,  # One task at a time for API rate limiting
    broker_connection_retry_on_startup=True,
    beat_schedule=_beat_schedule,
)

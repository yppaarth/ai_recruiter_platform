from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "recruiter_outreach",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.followup_tasks",
        "app.tasks.reply_tasks",
        "app.tasks.analytics_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_soft_time_limit=300,
    task_time_limit=600,
    beat_schedule={
        "check-followups-every-hour": {
            "task": "app.tasks.followup_tasks.process_pending_followups",
            "schedule": 3600.0,
        },
        "check-replies-every-30min": {
            "task": "app.tasks.reply_tasks.check_for_replies",
            "schedule": 1800.0,
        },
    },
)

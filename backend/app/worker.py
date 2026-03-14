from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.task_routes = {"app.tasks.*": "main-queue"}

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "escalate-unresolved-complaints": {
        "task": "escalate_unresolved_complaints",
        "schedule": crontab(hour="*/6"),  # Run every 6 hours
    },
}

# Timezone configuration
celery_app.conf.timezone = "UTC"

from celery import Celery
from api.config import settings

celery_app = Celery(
    "xpose",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "api.tasks.scan_orchestrator.*": {"queue": "scans"},
        "api.tasks.module_tasks.*": {"queue": "modules"},
    },
)

# Explicit imports so Celery registers all tasks at worker startup
# (autodiscover_tasks alone doesn't reliably find them in this package layout)
import api.tasks.scan_orchestrator  # noqa: E402, F401
import api.tasks.module_tasks  # noqa: E402, F401

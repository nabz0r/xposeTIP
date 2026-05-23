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
        "api.tasks.similarity.*": {"queue": "scans"},
        "api.tasks.watchdog.*": {"queue": "scans"},
    },
    # S148: Redis broker visibility_timeout — gives acks_late tasks
    # enough headroom to complete before broker redelivers. 2h covers
    # even the longest cascade scans.
    broker_transport_options={"visibility_timeout": 7200},
    # S148: beat schedule — orphan-scan watchdog every 5 minutes.
    beat_schedule={
        "sweep-orphan-scans": {
            "task": "api.tasks.watchdog.sweep_orphan_scans",
            "schedule": 300.0,
        },
        # S172 — Live Merkle rebuild over bfp_claims, every 5min.
        # Always-insert semantic: each tick appends one row per workspace.
        "rebuild-bfp-merkle-roots": {
            "task": "api.tasks.bfp.rebuild_merkle_roots",
            "schedule": 300.0,
        },
    },
)

# Explicit imports so Celery registers all tasks at worker startup
# (autodiscover_tasks alone doesn't reliably find them in this package layout)
import api.tasks.scan_orchestrator  # noqa: E402, F401
import api.tasks.module_tasks  # noqa: E402, F401
import api.tasks.web_discovery  # noqa: E402, F401
import api.tasks.similarity  # noqa: E402, F401
import api.tasks.watchdog  # noqa: E402, F401
import api.tasks.bfp  # noqa: E402, F401


@celery_app.on_after_configure.connect
def setup_worker_logging(sender, **kwargs):
    """Install RedisLogHandler on worker processes."""
    import os
    container = os.environ.get("XPOSE_CONTAINER", "worker")
    from api.services.log_handler import setup_logging
    setup_logging(redis_url=settings.REDIS_URL, container=container)
    import logging as _logging
    _logging.getLogger("api.tasks").info("xpose Worker started — Redis log handler active")


from celery.signals import worker_process_init  # noqa: E402


@worker_process_init.connect
def setup_redis_logging_per_process(**kwargs):
    """Install RedisLogHandler in each prefork child process."""
    import os
    import logging as _logging
    from api.services.log_handler import RedisLogHandler

    os.environ.setdefault("XPOSE_CONTAINER", "worker")
    container = os.environ.get("XPOSE_CONTAINER", "worker")
    handler = RedisLogHandler(redis_url=settings.REDIS_URL, container=container)
    handler.setLevel(_logging.DEBUG)
    handler.setFormatter(_logging.Formatter("%(message)s"))

    root = _logging.getLogger()
    if not any(isinstance(h, RedisLogHandler) for h in root.handlers):
        root.addHandler(handler)
        root.setLevel(_logging.DEBUG)

    _logging.getLogger(__name__).info("Worker process Redis log handler active (pid=%s)", os.getpid())

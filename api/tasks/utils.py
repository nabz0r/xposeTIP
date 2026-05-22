from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.config import settings

sync_engine = create_engine(settings.DATABASE_URL_SYNC)
_SessionLocal = sessionmaker(bind=sync_engine)


def get_sync_session():
    return _SessionLocal()


# ═══════════════════════════════════════════════════════════════════════════
# S153 — Scan task revocation helpers
# ═══════════════════════════════════════════════════════════════════════════

import logging as _logging

_log = _logging.getLogger(__name__)


def stash_scan_child_tasks(scan_id: str, task_ids: list[str]) -> None:
    """Persist the child task IDs of a scan's chord in Redis so cancel can
    revoke them later. Set with 24h TTL — chord rarely runs that long, and
    the natural expiration avoids stale keys.

    Called once by launch_scan after chord(...)(callback) returns.
    """
    if not task_ids:
        return
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        key = f"scan:{scan_id}:child_tasks"
        rc.sadd(key, *task_ids)
        rc.expire(key, 86400)
        rc.close()
    except Exception:
        _log.exception("stash_scan_child_tasks failed for %s (non-fatal)", scan_id)


def revoke_scan_tasks(scan_id: str, parent_task_id: str | None = None) -> int:
    """Revoke all known Celery tasks for a scan: stashed chord children +
    the parent launch_scan task. Returns count of revocations attempted.

    Safe to call multiple times; revoking an already-completed task is a no-op
    on the Celery side.
    """
    from api.tasks import celery_app

    revoked = 0
    # 1. Revoke stashed child tasks
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        key = f"scan:{scan_id}:child_tasks"
        child_ids = rc.smembers(key)
        for task_id in child_ids:
            tid = task_id.decode() if isinstance(task_id, bytes) else task_id
            try:
                celery_app.control.revoke(tid, terminate=True)
                revoked += 1
            except Exception:
                _log.exception("revoke child %s failed", tid)
        rc.delete(key)
        rc.close()
    except Exception:
        _log.exception("revoke_scan_tasks Redis stage failed for %s", scan_id)

    # 2. Revoke parent (no-op if already finished, but cheap)
    if parent_task_id:
        try:
            celery_app.control.revoke(parent_task_id, terminate=True)
            revoked += 1
        except Exception:
            _log.exception("revoke parent %s failed", parent_task_id)

    return revoked

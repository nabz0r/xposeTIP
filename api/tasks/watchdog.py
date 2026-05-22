"""S148 — Orphan-scan watchdog.

Runs every 5min via Celery beat. Finds scans that the worker fleet has
clearly abandoned (queued too long, running with no progress, or running
beyond the broker visibility_timeout window) and marks them failed.

Safe-only: does not redispatch tasks. That's the broker's job via
acks_late + reject_on_worker_lost (S148 Layer A). The watchdog is the
backstop for the cases where redelivery itself fails or never fires.
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, or_, and_

from api.tasks import celery_app
from api.tasks.utils import get_sync_session
from api.models.scan import Scan

logger = logging.getLogger(__name__)

# Thresholds (minutes)
QUEUED_ORPHAN_MIN = 30        # status='queued' more than 30min = lost
RUNNING_NO_PROGRESS_MIN = 20  # status='running' but no module_progress activity for 20min = lost
RUNNING_HARD_TIMEOUT_MIN = 240  # status='running' for 4h = hard cap (beyond visibility_timeout x2)


def _is_running_no_progress(scan: Scan, now: datetime) -> bool:
    """True if status='running', started > 20min ago, and module_progress
    is empty or every entry is still 'queued'."""
    if not scan.started_at:
        return False
    age = now - scan.started_at
    if age < timedelta(minutes=RUNNING_NO_PROGRESS_MIN):
        return False
    progress = scan.module_progress or {}
    if not progress:
        return True
    return all(state == "queued" for state in progress.values())


@celery_app.task(name="api.tasks.watchdog.sweep_orphan_scans")
def sweep_orphan_scans() -> dict:
    """Mark orphaned scans as failed. Returns a summary dict for observability."""
    session = get_sync_session()
    swept = {"queued_orphan": 0, "running_no_progress": 0, "running_hard_timeout": 0}
    try:
        now = datetime.now(timezone.utc)
        queued_cutoff = now - timedelta(minutes=QUEUED_ORPHAN_MIN)
        hard_cutoff = now - timedelta(minutes=RUNNING_HARD_TIMEOUT_MIN)

        # Single query — all candidates needing inspection
        candidates = session.execute(
            select(Scan).where(
                or_(
                    and_(Scan.status == "queued", Scan.created_at < queued_cutoff),
                    and_(Scan.status == "running", Scan.started_at < hard_cutoff),
                    Scan.status == "running",  # also pull for no-progress check
                )
            )
        ).scalars().all()

        for scan in candidates:
            reason = None

            if scan.status == "queued":
                reason = (
                    f"orphan: queued for >{QUEUED_ORPHAN_MIN}min, "
                    f"worker never picked up task (likely worker restart between dispatch and execution)"
                )
                swept["queued_orphan"] += 1

            elif scan.status == "running":
                if scan.started_at and (now - scan.started_at) > timedelta(minutes=RUNNING_HARD_TIMEOUT_MIN):
                    reason = (
                        f"orphan: running for >{RUNNING_HARD_TIMEOUT_MIN}min "
                        f"(beyond broker visibility_timeout — task lost without redelivery)"
                    )
                    swept["running_hard_timeout"] += 1
                elif _is_running_no_progress(scan, now):
                    reason = (
                        f"orphan: running for >{RUNNING_NO_PROGRESS_MIN}min "
                        f"with no module_progress activity (worker died after status flip)"
                    )
                    swept["running_no_progress"] += 1

            if reason:
                scan.status = "failed"
                scan.cascade_state = "failed"
                scan.completed_at = now
                scan.error_log = reason
                logger.warning("watchdog: marked scan %s failed — %s", scan.id, reason)

        session.commit()

        if any(swept.values()):
            logger.info("watchdog sweep complete: %s", swept)
        else:
            logger.debug("watchdog sweep clean (no orphans)")

        return swept
    except Exception:
        logger.exception("watchdog sweep failed")
        session.rollback()
        raise
    finally:
        session.close()

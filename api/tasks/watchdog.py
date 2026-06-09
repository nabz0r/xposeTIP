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

# S241 — sentinel left on Scan.error_log when the watchdog re-dispatches a
# queued orphan. Presence of this marker means we already burned our one
# retry — a still-queued scan on the next tick gets failed instead of
# re-dispatched again. Bounded to one retry to avoid infinite loops.
REDISPATCH_MARKER = "[watchdog] re-dispatched"


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
    swept = {
        "queued_redispatched": 0,
        "queued_orphan": 0,
        "running_no_progress": 0,
        "running_hard_timeout": 0,
    }
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
                # S241 — re-dispatch once before giving up. The S241 atomic
                # claim in launch_scan makes re-dispatch safe even if the
                # original broker task eventually arrives.
                already_tried = bool(scan.error_log) and REDISPATCH_MARKER in scan.error_log
                if not already_tried:
                    try:
                        from api.tasks.scan_orchestrator import launch_scan
                        task = launch_scan.delay(str(scan.id))
                        scan.celery_task_id = task.id
                        scan.error_log = f"{REDISPATCH_MARKER} {task.id} at {now.isoformat()}"
                        swept["queued_redispatched"] += 1
                        logger.warning(
                            "watchdog: re-dispatched orphan queued scan %s -> %s",
                            scan.id, task.id,
                        )
                        continue  # leave status=queued; launch_scan's atomic claim flips it
                    except Exception:
                        logger.exception(
                            "watchdog: re-dispatch failed for %s — falling through to mark failed",
                            scan.id,
                        )
                # Already burned our retry (or re-dispatch raised) — give up.
                reason = (
                    f"orphan: still queued >{QUEUED_ORPHAN_MIN}min after watchdog re-dispatch "
                    f"(broker likely still saturated — manual relaunch needed)"
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

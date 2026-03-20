import logging
import uuid
from datetime import datetime, timezone

from celery import chord
from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task(name="api.tasks.scan_orchestrator.launch_scan", bind=True)
def launch_scan(self, scan_id: str):
    from api.models.scan import Scan
    from api.models.target import Target

    session = get_sync_session()
    try:
        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return {"error": "Scan not found"}

        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        session.commit()

        target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
        if not target:
            scan.status = "failed"
            scan.error_log = "Target not found"
            session.commit()
            return {"error": "Target not found"}

        email = target.email
        modules = scan.modules or []

        if not modules:
            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            session.commit()
            return {"status": "no modules"}

        scan.module_progress = {mod: "queued" for mod in modules}
        session.commit()

        from api.tasks.module_tasks import run_module
        module_tasks = [run_module.s(scan_id, mod, email) for mod in modules]
        callback = finalize_scan.si(scan_id)
        chord(module_tasks)(callback)

        return {"status": "launched", "modules": modules}
    except Exception:
        session.rollback()
        logger.exception("launch_scan failed for %s", scan_id)
        raise
    finally:
        session.close()


@celery_app.task(name="api.tasks.scan_orchestrator.finalize_scan")
def finalize_scan(scan_id: str):
    from api.models.scan import Scan
    from api.models.target import Target
    from api.models.finding import Finding
    from sqlalchemy import func

    session = get_sync_session()
    try:
        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return

        # Count findings
        total_findings = session.execute(
            select(func.count()).select_from(Finding).where(Finding.scan_id == scan.id)
        ).scalar() or 0

        scan.status = "completed"
        scan.completed_at = datetime.now(timezone.utc)
        scan.findings_count = total_findings
        if scan.started_at:
            duration = datetime.now(timezone.utc) - scan.started_at
            scan.duration_ms = int(duration.total_seconds() * 1000)

        # Update target
        target = session.execute(select(Target).where(Target.id == scan.target_id)).scalar_one_or_none()
        if target:
            target.status = "completed"
            target.last_scanned = datetime.now(timezone.utc)
            if not target.first_scanned:
                target.first_scanned = datetime.now(timezone.utc)

        session.commit()

        # Compute exposure score (separate transaction so scan status is visible)
        try:
            from api.services.layer4.score_engine import compute_score
            score, breakdown = compute_score(scan.target_id, session)
            logger.info("Score for target %s: %d", scan.target_id, score)
        except Exception:
            logger.exception("Score computation failed for target %s", scan.target_id)
            # Ensure score is at least 0 on failure
            if target:
                target.exposure_score = target.exposure_score or 0
                target.score_breakdown = target.score_breakdown or {}
                session.commit()

        # Build identity graph (separate transaction)
        try:
            from api.services.layer4.graph_builder import build_graph
            build_graph(scan.target_id, scan.workspace_id, session)
        except Exception:
            logger.exception("Graph build failed for target %s", scan.target_id)

    except Exception:
        session.rollback()
        logger.exception("finalize_scan failed for %s", scan_id)
        raise
    finally:
        session.close()

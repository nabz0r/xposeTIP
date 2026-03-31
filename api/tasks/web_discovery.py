"""Celery task for Phase C — Web Discovery."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from api.tasks import celery_app
from api.tasks.utils import get_sync_session
from api.services.event_bus import publish_event

logger = logging.getLogger(__name__)


@celery_app.task(
    name="api.tasks.web_discovery.run_discovery",
    bind=True,
    soft_time_limit=120,
    time_limit=180,
)
def run_discovery(self, target_id: str, session_id: str, workspace_id: str,
                  triggered_by: str = None, budget_config: dict = None):
    """Run Phase C Web Discovery for a target."""
    db = get_sync_session()
    try:
        from api.models.target import Target
        from api.models.discovery import DiscoverySession
        from api.discovery.pipeline import DiscoveryPipeline
        from api.discovery.query_generator import DiscoveryBudget

        tid = uuid.UUID(target_id)
        sid = uuid.UUID(session_id)

        target = db.execute(select(Target).where(Target.id == tid)).scalar_one_or_none()
        if not target:
            logger.error("Discovery: target %s not found", target_id)
            return

        session_obj = db.execute(
            select(DiscoverySession).where(DiscoverySession.id == sid)
        ).scalar_one_or_none()
        if not session_obj:
            logger.error("Discovery: session %s not found", session_id)
            return

        publish_event("discovery.started", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
        })

        bc = budget_config or {}
        budget = DiscoveryBudget(
            max_queries=bc.get("max_queries", session_obj.max_queries),
            max_pages=bc.get("max_pages", session_obj.max_pages),
            max_seconds=bc.get("budget_seconds", session_obj.budget_seconds),
        )

        def on_discovery(node):
            publish_event("discovery.node", {
                "workspace_id": workspace_id,
                "target_id": target_id,
                "session_id": session_id,
                **node,
            })

        pipeline = DiscoveryPipeline(
            target_id=target_id,
            session_id=session_id,
            budget=budget,
            db_session=db,
            on_discovery=on_discovery,
            dry_run=False,
        )
        result = pipeline.run()

        session_obj.status = "completed"
        session_obj.queries_executed = result.get("queries_executed", 0)
        session_obj.pages_fetched = result.get("pages_fetched", 0)
        session_obj.leads_found = result.get("leads_found", 0)
        session_obj.completed_at = datetime.now(timezone.utc)
        db.commit()

        publish_event("discovery.completed", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
            "queries_executed": result.get("queries_executed", 0),
            "pages_fetched": result.get("pages_fetched", 0),
            "leads_found": result.get("leads_found", 0),
            "duration_seconds": result.get("duration_seconds", 0),
        })

        logger.info("Discovery complete for %s: %d leads in %.1fs",
                     target_id, result.get("leads_found", 0),
                     result.get("duration_seconds", 0))

    except Exception as e:
        logger.exception("Discovery failed for %s: %s", target_id, e)
        try:
            session_obj = db.execute(
                select(DiscoverySession).where(DiscoverySession.id == uuid.UUID(session_id))
            ).scalar_one_or_none()
            if session_obj:
                session_obj.status = "error"
                session_obj.error_message = str(e)[:500]
                session_obj.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass

        publish_event("discovery.error", {
            "workspace_id": workspace_id,
            "target_id": target_id,
            "session_id": session_id,
            "error": str(e)[:200],
        })
    finally:
        db.close()

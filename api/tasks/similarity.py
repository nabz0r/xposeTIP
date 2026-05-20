"""Celery task — recompute fingerprint-similarity pairs for a target.

Enqueued by scan_orchestrator.finalize_scan after the fingerprint is written.
Async so it does not block the perceived scan completion.
"""
import logging
import uuid

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="api.tasks.similarity.recompute_similarities_for_target",
    bind=True,
    soft_time_limit=60,
    time_limit=90,
)
def recompute_similarities_for_target(self, target_id: str, workspace_id: str):
    """Recompute pairwise similarities for `target_id` against the workspace.

    Idempotent. Safe to retry — uses DELETE+INSERT pattern preserving
    `first_detected` via batch harvest.
    """
    from api.services.layer4.similarity_engine import recompute_for_target

    session = get_sync_session()
    try:
        stats = recompute_for_target(
            session=session,
            target_id=uuid.UUID(target_id),
            workspace_id=uuid.UUID(workspace_id),
        )
        return stats
    except Exception:
        session.rollback()
        logger.exception("recompute_similarities_for_target failed for %s", target_id)
        raise
    finally:
        session.close()

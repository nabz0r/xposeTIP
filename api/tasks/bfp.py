"""S172 — BFP Merkle root rebuild beat task.

Runs every 300s via Celery beat (`api/tasks/__init__.py:beat_schedule`).
Calls the existing `rebuild_all_workspaces()` builder, which is idempotent
and is the sole writer to `bfp_merkle_roots` + `bfp_claims.merkle_position`.

Semantics — ALWAYS INSERT (S172 locked decision):
    Each tick appends one row per workspace-with-claims to `bfp_merkle_roots`,
    even when `root_hash` and `num_leaves` are identical to the previous row.
    This is CT-STH-style liveness signalling: the existence of the row at
    time T is itself proof the log was alive at T.

    The `/bfp` page counter "Merkle roots committed" therefore ticks at every
    beat regardless of substrate change. This is the intended visitor signal.

Observability:
    - Logs at INFO level on per-tick summary (workspaces touched, total leaves)
    - Logs at DEBUG when no workspaces have claims yet (nothing to rebuild)
    - Logs at EXCEPTION on failure; DB rollback; Celery retry NOT configured
      (next tick in 300s will pick up — no point retrying tighter)
    - Publishes `bfp.merkle_root_committed` event per workspace on `bfp:events`
      channel via the generalized `publish_event(..., channel=BFP_CHANNEL)`.
      Future public BFP SSE consumers can subscribe to this channel.

Concurrency assumption:
    Celery beat is singleton-per-deploy (standard `celery beat` invocation,
    one process). If two beat schedulers run concurrently in the same deploy,
    duplicate rows are possible — `bfp_merkle_roots` has no UNIQUE constraint
    on `(workspace_id, computed_at)` and the design intentionally tolerates
    history appending. No distributed lock added for MVP.
"""
import logging
from datetime import datetime, timezone

from api.services.bfp.merkle_builder import rebuild_all_workspaces
from api.services.event_bus import BFP_CHANNEL, publish_event
from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task(name="api.tasks.bfp.rebuild_merkle_roots")
def rebuild_merkle_roots() -> dict:
    """Rebuild Merkle roots over `bfp_claims` for every workspace with at
    least one claim. Returns a summary dict for observability.
    """
    session = get_sync_session()
    summary = {"workspaces": 0, "total_leaves": 0, "errors": 0}
    try:
        results = rebuild_all_workspaces(session)
        session.commit()

        # Publish per-workspace events AFTER commit (so subscribers never see
        # an event for a row that may yet roll back).
        now_iso = datetime.now(timezone.utc).isoformat()
        for r in results:
            if r["root_hash"] is None:
                # Workspace exists in the iteration but had zero claims — skip.
                # rebuild_all_workspaces only iterates workspaces with ≥1 claim,
                # so this branch is defensive; it shouldn't fire in practice.
                continue
            summary["workspaces"] += 1
            summary["total_leaves"] += r["num_leaves"]
            publish_event(
                "bfp.merkle_root_committed",
                {
                    "workspace_id": str(r["workspace_id"]),
                    "root_hash": r["root_hash"],
                    "num_leaves": r["num_leaves"],
                    "root_version": 1,
                    "computed_at": now_iso,
                },
                channel=BFP_CHANNEL,
            )

        if summary["workspaces"] > 0:
            logger.info(
                "bfp.merkle: rebuilt %d workspaces, %d total leaves",
                summary["workspaces"], summary["total_leaves"],
            )
        else:
            logger.debug("bfp.merkle: no workspaces with claims — nothing to rebuild")

        return summary
    except Exception:
        logger.exception("bfp.merkle: rebuild failed")
        session.rollback()
        summary["errors"] = 1
        raise
    finally:
        session.close()

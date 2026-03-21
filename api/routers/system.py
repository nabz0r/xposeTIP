import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace, require_role
from api.config import settings
from api.database import get_db
from api.models.finding import Finding
from api.models.identity import Identity
from api.models.module import Module
from api.models.scan import Scan
from api.models.target import Target
from api.models.user import User
from api.tasks.module_tasks import SCANNER_REGISTRY

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def system_stats(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Infrastructure health
    infra = {}

    # PostgreSQL
    try:
        result = await db.execute(text("SELECT version()"))
        pg_version = result.scalar()
        infra["postgresql"] = {"status": "healthy", "version": pg_version}
    except Exception as e:
        infra["postgresql"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        import redis as r
        rc = r.from_url(settings.REDIS_URL)
        rc.ping()
        redis_info = rc.info("server")
        infra["redis"] = {
            "status": "healthy",
            "version": redis_info.get("redis_version", "unknown"),
            "connected_clients": rc.info("clients").get("connected_clients", 0),
        }
        rc.close()
    except Exception as e:
        infra["redis"] = {"status": "unhealthy", "error": str(e)}

    # Celery workers
    try:
        from api.tasks import celery_app
        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active() or {}
        registered = inspector.registered() or {}
        worker_count = len(registered)
        active_tasks = sum(len(t) for t in active.values())
        infra["celery"] = {
            "status": "healthy" if worker_count > 0 else "unhealthy",
            "workers": worker_count,
            "active_tasks": active_tasks,
        }
    except Exception as e:
        infra["celery"] = {"status": "unhealthy", "error": str(e)}

    # API
    infra["api"] = {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

    # Table row counts
    tables = {}
    for model, name in [(User, "users"), (Target, "targets"), (Scan, "scans"), (Finding, "findings"), (Identity, "identities"), (Module, "modules")]:
        try:
            count = await db.scalar(select(func.count()).select_from(model))
            tables[name] = {"count": count or 0}
        except Exception:
            tables[name] = {"count": 0}

    # Module health matrix
    modules_result = await db.execute(select(Module))
    modules = modules_result.scalars().all()
    module_health = []
    for m in modules:
        # Count findings per module
        finding_count = await db.scalar(
            select(func.count()).select_from(Finding).where(Finding.module == m.id)
        ) or 0

        # Avg scan duration for scans that included this module
        module_health.append({
            "id": m.id,
            "display_name": m.display_name,
            "layer": m.layer,
            "enabled": m.enabled,
            "implemented": m.id in SCANNER_REGISTRY,
            "health_status": m.health_status or "unknown",
            "last_health": m.last_health.isoformat() if m.last_health else None,
            "findings_count": finding_count,
        })

    # Recent activity
    recent_scans = await db.execute(
        select(Scan).where(Scan.workspace_id == workspace_id)
        .order_by(Scan.created_at.desc()).limit(5)
    )
    recent = []
    for s in recent_scans.scalars().all():
        recent.append({
            "id": str(s.id),
            "status": s.status,
            "modules": s.modules,
            "findings_count": s.findings_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "infrastructure": infra,
        "tables": tables,
        "modules": module_health,
        "recent_scans": recent,
    }


@router.get("/logs")
async def get_system_logs(
    limit: int = 200,
    level: str | None = None,
    container: str | None = None,
    role: str = Depends(require_role("superadmin", "admin")),
):
    """Read structured logs from the Redis ring buffer."""
    from api.services.log_handler import get_logs
    try:
        entries = get_logs(
            redis_url=settings.REDIS_URL,
            limit=min(limit, 1000),
            level=level,
            container=container,
        )
        return {"logs": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {e}")


@router.delete("/logs")
async def clear_system_logs(
    user: User = Depends(get_current_user),
    role: str = Depends(require_role("superadmin", "admin")),
):
    """Clear all logs from the Redis ring buffer."""
    from api.services.log_handler import clear_logs
    try:
        deleted = clear_logs(redis_url=settings.REDIS_URL)
        return {"deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {e}")


@router.post("/recalculate-scores")
async def recalculate_scores(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Re-run score engine for all targets in this workspace."""
    from api.tasks.utils import get_sync_session
    from api.services.layer4.score_engine import compute_score

    targets_result = await db.execute(
        select(Target).where(Target.workspace_id == workspace_id)
    )
    targets = targets_result.scalars().all()

    sync_session = get_sync_session()
    updated = 0
    try:
        for t in targets:
            try:
                score, threat, breakdown = compute_score(t.id, sync_session)
                updated += 1
            except Exception:
                logger.exception("Failed to recompute score for target %s", t.id)
        sync_session.commit()
    finally:
        sync_session.close()

    return {"recalculated": updated, "total": len(targets)}

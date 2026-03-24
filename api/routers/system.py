import logging
import uuid
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
from api.models.user import User, UserWorkspace
from api.models.workspace import Workspace
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
        select(Scan, Target.email)
        .join(Target, Scan.target_id == Target.id, isouter=True)
        .where(Scan.workspace_id == workspace_id)
        .order_by(Scan.created_at.desc()).limit(5)
    )
    recent = []
    for s, email in recent_scans.all():
        recent.append({
            "id": str(s.id),
            "target_id": str(s.target_id),
            "target_email": email,
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
    scan_id: str | None = None,
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
        # Filter by scan_id if provided
        if scan_id:
            entries = [e for e in entries if e.get("scan_id") == scan_id]
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


@router.post("/recalculate-profiles")
async def recalculate_profiles(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Re-run profile aggregation + identity enrichment for all targets."""
    from api.tasks.utils import get_sync_session
    from api.services.layer4.profile_aggregator import aggregate_profile
    from api.services.layer4.identity_enricher import enrich_identity

    targets_result = await db.execute(
        select(Target).where(Target.workspace_id == workspace_id)
    )
    targets = targets_result.scalars().all()

    sync_session = get_sync_session()
    updated = 0
    enriched = 0
    try:
        for t in targets:
            try:
                aggregate_profile(t.id, workspace_id, sync_session)
                updated += 1

                # Re-read target after aggregation
                target = sync_session.execute(
                    select(Target).where(Target.id == t.id)
                ).scalar_one_or_none()
                if target:
                    profile = dict(target.profile_data or {})
                    est = profile.get("identity_estimation", {})
                    if not est.get("gender") or not est.get("age"):
                        updated_est = enrich_identity(profile, target.email)
                        if updated_est and (updated_est.get("gender") or updated_est.get("age")):
                            profile["identity_estimation"] = updated_est
                            target.profile_data = profile
                            enriched += 1
            except Exception:
                logger.exception("Failed to recalculate profile for target %s", t.id)
        sync_session.commit()
    finally:
        sync_session.close()

    return {"recalculated": updated, "enriched": enriched, "total": len(targets)}


@router.post("/recalculate-fingerprints")
async def recalculate_fingerprints(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Re-run fingerprint engine for all targets (recomputes eigenvalues + avatar_seed)."""
    from api.tasks.utils import get_sync_session
    from api.services.layer4.fingerprint_engine import FingerprintEngine
    from api.models.identity import Identity, IdentityLink

    targets_result = await db.execute(
        select(Target).where(Target.workspace_id == workspace_id)
    )
    targets = targets_result.scalars().all()

    sync = get_sync_session()
    fp_engine = FingerprintEngine()
    updated = 0
    try:
        for t in targets:
            try:
                findings = sync.execute(
                    select(Finding).where(Finding.target_id == t.id)
                ).scalars().all()
                identities = sync.execute(
                    select(Identity).where(Identity.target_id == t.id)
                ).scalars().all()
                id_set = set(i.id for i in identities)
                all_links = sync.execute(
                    select(IdentityLink).where(IdentityLink.workspace_id == workspace_id)
                ).scalars().all()
                target_links = [l for l in all_links if l.source_id in id_set or l.dest_id in id_set]

                fp = fp_engine.compute(findings, identities, t.profile_data, t.email, links=target_links)
                profile = dict(t.profile_data or {})
                profile["fingerprint"] = fp
                t.profile_data = profile
                updated += 1
            except Exception:
                logger.exception("Fingerprint recalc failed for %s", t.id)
        sync.commit()
    finally:
        sync.close()

    return {"recalculated": updated, "total": len(targets)}


# ---- Platform Admin (superadmin only) ----

@router.get("/users")
async def list_all_users(
    role: str = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Platform admin: list ALL users with their workspace memberships."""
    users = await db.execute(
        select(User).order_by(User.created_at.desc())
    )

    result = []
    for u in users.scalars().all():
        memberships = await db.execute(
            select(UserWorkspace, Workspace)
            .join(Workspace, UserWorkspace.workspace_id == Workspace.id)
            .where(UserWorkspace.user_id == u.id)
        )
        ws_list = [
            {
                "workspace_id": str(ws.id),
                "workspace_name": ws.name,
                "plan": ws.plan,
                "role": uw.role,
            }
            for uw, ws in memberships.all()
        ]

        result.append({
            "id": str(u.id),
            "email": u.email,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "workspaces": ws_list,
            "workspace_count": len(ws_list),
            "highest_role": ws_list[0]["role"] if ws_list else "none",
        })

    return {"items": result, "total": len(result)}


@router.patch("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    body: dict,
    role: str = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Platform admin: activate/deactivate user, update display name."""
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "is_active" in body:
        user.is_active = body["is_active"]
    if "display_name" in body:
        user.display_name = body["display_name"]

    await db.commit()
    return {"updated": True, "user_id": user_id}


@router.get("/workspaces")
async def list_all_workspaces(
    role: str = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    """Platform admin: list ALL workspaces with stats."""
    workspaces = await db.execute(
        select(Workspace).order_by(Workspace.created_at.desc())
    )

    result = []
    for ws in workspaces.scalars().all():
        member_count = await db.scalar(
            select(func.count()).select_from(UserWorkspace).where(UserWorkspace.workspace_id == ws.id)
        )
        target_count = await db.scalar(
            select(func.count()).select_from(Target).where(Target.workspace_id == ws.id)
        )
        scan_count = await db.scalar(
            select(func.count()).select_from(Scan).where(Scan.workspace_id == ws.id)
        )

        result.append({
            "id": str(ws.id),
            "name": ws.name,
            "slug": ws.slug,
            "plan": ws.plan,
            "owner_id": str(ws.owner_id) if ws.owner_id else None,
            "member_count": member_count or 0,
            "target_count": target_count or 0,
            "scan_count": scan_count or 0,
            "created_at": ws.created_at.isoformat() if ws.created_at else None,
        })

    return {"items": result, "total": len(result)}


# ---- Scraper Health ----

@router.get("/scraper-health")
async def get_scraper_health(
    role: str = Depends(require_role("superadmin", "admin")),
):
    """Get health stats for all scrapers (last 24h) from Redis counters."""
    from api.services.scraper_health import get_scraper_health_instance
    health = get_scraper_health_instance()
    if not health:
        return {"items": [], "error": "Redis unavailable"}
    return {"items": health.get_all_health()}


# ---- Name Blacklist Management ----

@router.get("/name-blacklist")
async def list_blacklist(
    role: str = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all name blacklist entries."""
    from api.models.name_blacklist import NameBlacklist
    entries = await db.execute(select(NameBlacklist).order_by(NameBlacklist.id))
    return {
        "items": [
            {"id": e.id, "pattern": e.pattern, "type": e.type, "reason": e.reason}
            for e in entries.scalars().all()
        ]
    }


@router.post("/name-blacklist", status_code=201)
async def add_blacklist(
    body: dict,
    role: str = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Add a name blacklist entry."""
    from api.models.name_blacklist import NameBlacklist
    pattern = body.get("pattern", "").strip()
    if not pattern:
        raise HTTPException(status_code=400, detail="Pattern is required")
    entry = NameBlacklist(
        pattern=pattern,
        type=body.get("type", "exact"),
        reason=body.get("reason"),
    )
    db.add(entry)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Pattern already exists")
    return {"id": entry.id, "pattern": entry.pattern, "type": entry.type}


@router.delete("/name-blacklist/{entry_id}")
async def remove_blacklist(
    entry_id: int,
    role: str = Depends(require_role("superadmin", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a name blacklist entry."""
    from api.models.name_blacklist import NameBlacklist
    result = await db.execute(select(NameBlacklist).where(NameBlacklist.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
    return {"deleted": True}

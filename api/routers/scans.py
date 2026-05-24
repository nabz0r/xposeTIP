import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func

from api.auth.dependencies import get_current_user, get_current_workspace, get_current_role
from api.database import get_db
from api.models.module import Module
from api.models.scan import Scan
from api.models.target import Target
from api.models.user import User
from api.models.workspace import Workspace
from api.tasks.module_tasks import SCANNER_REGISTRY

router = APIRouter()
logger = logging.getLogger(__name__)


DEFAULT_QUICK_MODULES = [
    "email_validator", "holehe", "emailrep", "gravatar", "epieos", "github_deep", "dns_deep",
    "name_scraper_engine",  # S122e — silent no-op if no name input available yet
    "scraper_engine",       # S199 — dispatches all enabled data-driven scrapers (145 active post-S198)
]


class ScanCreate(BaseModel):
    target_id: uuid.UUID
    modules: list[str] | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_scan(
    body: ScanCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    role: str = Depends(get_current_role),
    db: AsyncSession = Depends(get_db),
):
    # Validate target
    result = await db.execute(
        select(Target).where(Target.id == body.target_id, Target.workspace_id == workspace_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    # Plan enforcement: check scan limit
    ws = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws.scalar_one_or_none()
    plan_name = workspace.plan if workspace else "free"

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scans_this_month = await db.scalar(
        select(func.count()).select_from(Scan)
        .where(Scan.workspace_id == workspace_id, Scan.created_at >= month_start)
    ) or 0

    from api.services.plan_config import check_scan_limit, filter_modules_by_plan
    allowed, msg = check_scan_limit(plan_name, scans_this_month, role)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

    # Resolve modules: use workspace defaults or fallback
    requested_modules = body.modules
    if not requested_modules:
        # Try workspace scan defaults
        ws_defaults = (workspace.settings or {}).get("default_modules") if workspace else None
        requested_modules = ws_defaults or DEFAULT_QUICK_MODULES

    # Filter modules by plan layer restrictions
    all_modules_result = await db.execute(select(Module))
    module_layers = {m.id: m.layer for m in all_modules_result.scalars().all()}
    plan_filtered = filter_modules_by_plan(requested_modules, plan_name, role, module_layers)

    # Validate modules — only keep enabled + implemented ones
    valid_modules = []
    for mod_id in plan_filtered:
        result = await db.execute(select(Module).where(Module.id == mod_id, Module.enabled.is_(True)))
        if not result.scalar_one_or_none():
            continue  # Skip unavailable modules silently (for quick scan)
        if mod_id in SCANNER_REGISTRY:
            valid_modules.append(mod_id)

    if not valid_modules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No implemented scanners selected",
        )

    scan = Scan(
        workspace_id=workspace_id,
        target_id=body.target_id,
        modules=valid_modules,
        module_progress={mod: "queued" for mod in valid_modules},
    )
    db.add(scan)

    # Update target status
    target.status = "scanning"
    await db.commit()
    await db.refresh(scan)

    # Dispatch celery task
    try:
        from api.tasks.scan_orchestrator import launch_scan
        task = launch_scan.delay(str(scan.id))
        scan.celery_task_id = task.id
        await db.commit()
    except Exception as e:
        import logging
        logging.error(f"Failed to dispatch scan task: {e}", exc_info=True)

    return _scan_dict(scan)


@router.get("")
async def list_scans(
    target_id: uuid.UUID | None = None,
    scan_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_filter = select(Scan).where(Scan.workspace_id == workspace_id)
    if target_id:
        base_filter = base_filter.where(Scan.target_id == target_id)
    if scan_status:
        base_filter = base_filter.where(Scan.status == scan_status)

    # Total count
    count_q = select(func.count()).select_from(base_filter.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = select(Scan, Target.email).join(Target, Scan.target_id == Target.id, isouter=True).where(Scan.workspace_id == workspace_id)
    if target_id:
        q = q.where(Scan.target_id == target_id)
    if scan_status:
        q = q.where(Scan.status == scan_status)
    q = q.order_by(Scan.created_at.desc()).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(q)
    items = [_scan_dict(scan, target_email=email) for scan, email in result.all()]
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@router.get("/{scan_id}")
async def get_scan(
    scan_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id, Scan.workspace_id == workspace_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return _scan_dict(scan)


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id, Scan.workspace_id == workspace_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # S153: revoke the whole chord (children + parent), not just the parent.
    try:
        from api.tasks.utils import revoke_scan_tasks
        revoked = revoke_scan_tasks(str(scan.id), scan.celery_task_id)
        logger.info("cancel_scan: revoked %d tasks for scan %s", revoked, scan.id)
    except Exception:
        logger.exception("cancel_scan: revoke chain failed for %s (non-fatal, status flip still happens)", scan.id)

    scan.status = "cancelled"
    scan.completed_at = datetime.now(timezone.utc)
    if scan.cascade_state and scan.cascade_state not in ("done", "failed"):
        scan.cascade_state = "failed"
    await db.commit()
    return _scan_dict(scan)


@router.get("/{scan_id}/scraper-progress")
async def scraper_progress(
    scan_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
):
    """Get scraper sub-progress for a running scan."""
    import json
    import redis as r
    from api.config import settings
    redis = r.from_url(settings.REDIS_URL)
    try:
        key = f"scan:{scan_id}:scraper_progress"
        data = redis.get(key)
        if data:
            return json.loads(data)
        return {"current": 0, "total": 0, "current_name": ""}
    finally:
        redis.close()


def _scan_dict(s: Scan, target_email: str = None) -> dict:
    return {
        "id": str(s.id),
        "target_id": str(s.target_id),
        "target_email": target_email,
        "status": s.status,
        "layer": s.layer,
        "modules": s.modules,
        "module_progress": s.module_progress,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        "duration_ms": s.duration_ms,
        "findings_count": s.findings_count,
        "new_findings": s.new_findings,
        "error_log": s.error_log,
        "cascade_state": s.cascade_state,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }

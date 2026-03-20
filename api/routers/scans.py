import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.module import Module
from api.models.scan import Scan
from api.models.target import Target
from api.models.user import User
from api.tasks.module_tasks import SCANNER_REGISTRY

router = APIRouter()


class ScanCreate(BaseModel):
    target_id: uuid.UUID
    modules: list[str]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_scan(
    body: ScanCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate target
    result = await db.execute(
        select(Target).where(Target.id == body.target_id, Target.workspace_id == workspace_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    # Validate modules — only keep enabled + implemented ones
    valid_modules = []
    for mod_id in body.modules:
        result = await db.execute(select(Module).where(Module.id == mod_id, Module.enabled.is_(True)))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Module '{mod_id}' not found or disabled",
            )
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
    q = select(Scan).where(Scan.workspace_id == workspace_id)
    if target_id:
        q = q.where(Scan.target_id == target_id)
    if scan_status:
        q = q.where(Scan.status == scan_status)
    q = q.order_by(Scan.created_at.desc()).offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(q)
    scans = result.scalars().all()
    return {"items": [_scan_dict(s) for s in scans], "page": page, "per_page": per_page}


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

    if scan.celery_task_id:
        try:
            from api.tasks import celery_app
            celery_app.control.revoke(scan.celery_task_id, terminate=True)
        except Exception:
            pass

    scan.status = "cancelled"
    await db.commit()
    return _scan_dict(scan)


def _scan_dict(s: Scan) -> dict:
    return {
        "id": str(s.id),
        "target_id": str(s.target_id),
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
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }

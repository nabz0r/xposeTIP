import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.finding import Finding
from api.models.user import User

router = APIRouter()


class FindingUpdate(BaseModel):
    status: str  # resolved, false_positive, monitoring, active


@router.get("")
async def list_findings(
    target_id: uuid.UUID | None = None,
    module: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    finding_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Finding).where(Finding.workspace_id == workspace_id)
    if target_id:
        q = q.where(Finding.target_id == target_id)
    if module:
        q = q.where(Finding.module == module)
    if severity:
        q = q.where(Finding.severity == severity)
    if category:
        q = q.where(Finding.category == category)
    if finding_status:
        q = q.where(Finding.status == finding_status)

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q)

    q = q.order_by(Finding.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    findings = result.scalars().all()

    return {"items": [_finding_dict(f, include_data=True) for f in findings], "total": total, "page": page, "per_page": per_page}


@router.get("/stats")
async def findings_stats(
    target_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Finding).where(Finding.workspace_id == workspace_id)
    if target_id:
        base = base.where(Finding.target_id == target_id)

    by_severity = await db.execute(
        select(Finding.severity, func.count())
        .where(Finding.workspace_id == workspace_id)
        .where(Finding.target_id == target_id if target_id else True)
        .group_by(Finding.severity)
    )
    by_category = await db.execute(
        select(Finding.category, func.count())
        .where(Finding.workspace_id == workspace_id)
        .where(Finding.target_id == target_id if target_id else True)
        .group_by(Finding.category)
    )
    by_module = await db.execute(
        select(Finding.module, func.count())
        .where(Finding.workspace_id == workspace_id)
        .where(Finding.target_id == target_id if target_id else True)
        .group_by(Finding.module)
    )

    return {
        "by_severity": dict(by_severity.all()),
        "by_category": dict(by_category.all()),
        "by_module": dict(by_module.all()),
    }


@router.get("/{finding_id}")
async def get_finding(
    finding_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Finding).where(Finding.id == finding_id, Finding.workspace_id == workspace_id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return _finding_dict(finding, include_data=True)


@router.patch("/{finding_id}")
async def update_finding(
    finding_id: uuid.UUID,
    body: FindingUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_statuses = {"active", "resolved", "false_positive", "monitoring"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status must be one of: {valid_statuses}")

    result = await db.execute(
        select(Finding).where(Finding.id == finding_id, Finding.workspace_id == workspace_id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    finding.status = body.status
    await db.commit()
    await db.refresh(finding)
    return _finding_dict(finding)


def _finding_dict(f: Finding, include_data: bool = False) -> dict:
    d = {
        "id": str(f.id),
        "scan_id": str(f.scan_id),
        "target_id": str(f.target_id),
        "module": f.module,
        "layer": f.layer,
        "category": f.category,
        "severity": f.severity,
        "title": f.title,
        "description": f.description,
        "url": f.url,
        "indicator_value": f.indicator_value,
        "indicator_type": f.indicator_type,
        "verified": f.verified,
        "confidence": f.confidence,
        "status": f.status,
        "first_seen": f.first_seen.isoformat() if f.first_seen else None,
        "last_seen": f.last_seen.isoformat() if f.last_seen else None,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }
    if include_data:
        d["data"] = f.data
    return d

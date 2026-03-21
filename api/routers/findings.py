import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.finding import Finding
from api.models.user import User

router = APIRouter()


class FindingUpdate(BaseModel):
    status: str  # resolved, false_positive, monitoring, active


def _dedup_findings(findings):
    """Deduplicate findings: keep latest per (target_id, module, title).

    Uses Python-side dedup instead of SQL — safer across all DB/ORM versions.
    """
    seen = {}
    for f in findings:
        key = (str(f.target_id), f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    return list(seen.values())


@router.get("")
async def list_findings(
    target_id: uuid.UUID | None = None,
    module: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    finding_status: str | None = Query(None, alias="status"),
    deduplicate: bool = Query(True),
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

    q = q.order_by(Finding.created_at.desc())
    result = await db.execute(q)
    all_findings = result.scalars().all()

    if deduplicate:
        all_findings = _dedup_findings(all_findings)
        # Re-sort after dedup
        all_findings.sort(key=lambda f: f.created_at or "", reverse=True)

    total = len(all_findings)
    start = (page - 1) * per_page
    findings = all_findings[start:start + per_page]

    return {"items": [_finding_dict(f, include_data=True) for f in findings], "total": total, "page": page, "per_page": per_page}


@router.get("/stats")
async def findings_stats(
    target_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all findings, dedup in Python, then compute stats
    q = select(Finding).where(Finding.workspace_id == workspace_id)
    if target_id:
        q = q.where(Finding.target_id == target_id)
    result = await db.execute(q)
    all_findings = _dedup_findings(result.scalars().all())

    from collections import Counter
    sev_counter = Counter(f.severity for f in all_findings)
    cat_counter = Counter(f.category for f in all_findings)
    mod_counter = Counter(f.module for f in all_findings)

    return {
        "by_severity": dict(sev_counter),
        "by_category": dict(cat_counter),
        "by_module": dict(mod_counter),
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

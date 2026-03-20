import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.finding import Finding
from api.models.target import Target
from api.models.user import User

router = APIRouter()


class TargetCreate(BaseModel):
    email: EmailStr
    country_code: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class TargetUpdate(BaseModel):
    country_code: str | None = None
    tags: list[str] | None = None
    notes: str | None = None


class BulkImport(BaseModel):
    emails: list[EmailStr]
    country_code: str | None = None
    tags: list[str] | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_target(
    body: TargetCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Target).where(Target.workspace_id == workspace_id, Target.email == body.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target already exists in workspace")

    target = Target(
        workspace_id=workspace_id,
        email=body.email,
        country_code=body.country_code,
        tags=body.tags,
        notes=body.notes,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return _target_dict(target)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_import_targets(
    body: BulkImport,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(body.emails) > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 500 emails per import")

    created = []
    skipped = []
    for email in body.emails:
        existing = await db.execute(
            select(Target).where(Target.workspace_id == workspace_id, Target.email == email)
        )
        if existing.scalar_one_or_none():
            skipped.append(email)
            continue
        target = Target(
            workspace_id=workspace_id,
            email=email,
            country_code=body.country_code,
            tags=body.tags,
        )
        db.add(target)
        created.append(email)

    await db.commit()
    return {"created": len(created), "skipped": len(skipped), "skipped_emails": skipped}


@router.get("")
async def list_targets(
    search: str | None = None,
    target_status: str | None = Query(None, alias="status"),
    min_score: int | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Target).where(Target.workspace_id == workspace_id)
    if search:
        q = q.where(Target.email.ilike(f"%{search}%"))
    if target_status:
        q = q.where(Target.status == target_status)
    if min_score is not None:
        q = q.where(Target.exposure_score >= min_score)
    q = q.order_by(Target.created_at.desc())

    count_q = select(func.count()).select_from(q.subquery())
    total = await db.scalar(count_q)

    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    targets = result.scalars().all()

    return {"items": [_target_dict(t) for t in targets], "total": total, "page": page, "per_page": per_page}


@router.get("/{target_id}")
async def get_target(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await _get_target(db, target_id, workspace_id)

    # Get findings count by severity
    severity_q = (
        select(Finding.severity, func.count())
        .where(Finding.target_id == target_id, Finding.workspace_id == workspace_id)
        .group_by(Finding.severity)
    )
    result = await db.execute(severity_q)
    severity_counts = dict(result.all())

    data = _target_dict(target)
    data["findings_by_severity"] = severity_counts
    return data


@router.get("/{target_id}/profile")
async def get_target_profile(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await _get_target(db, target_id, workspace_id)
    profile = target.profile_data or {}

    # Enrich with live data from target model
    profile["email"] = target.email
    profile["exposure_score"] = target.exposure_score
    profile["score_breakdown"] = target.score_breakdown
    profile["status"] = target.status
    profile["country_code"] = target.country_code
    profile["last_scanned"] = target.last_scanned.isoformat() if target.last_scanned else None
    profile["first_scanned"] = target.first_scanned.isoformat() if target.first_scanned else None

    # Fallback for name/avatar
    if not profile.get("primary_name"):
        profile["primary_name"] = target.display_name
    if not profile.get("primary_avatar"):
        profile["primary_avatar"] = target.avatar_url

    return profile


@router.patch("/{target_id}")
async def update_target(
    target_id: uuid.UUID,
    body: TargetUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await _get_target(db, target_id, workspace_id)
    if body.country_code is not None:
        target.country_code = body.country_code
    if body.tags is not None:
        target.tags = body.tags
    if body.notes is not None:
        target.notes = body.notes
    await db.commit()
    await db.refresh(target)
    return _target_dict(target)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: uuid.UUID,
    confirm: bool = Query(False),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add ?confirm=true to delete")
    target = await _get_target(db, target_id, workspace_id)
    await db.delete(target)
    await db.commit()


async def _get_target(db: AsyncSession, target_id: uuid.UUID, workspace_id: uuid.UUID) -> Target:
    result = await db.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target


def _target_dict(t: Target) -> dict:
    return {
        "id": str(t.id),
        "email": t.email,
        "display_name": t.display_name,
        "country_code": t.country_code,
        "status": t.status,
        "exposure_score": t.exposure_score,
        "score_breakdown": t.score_breakdown,
        "first_scanned": t.first_scanned.isoformat() if t.first_scanned else None,
        "last_scanned": t.last_scanned.isoformat() if t.last_scanned else None,
        "tags": t.tags,
        "notes": t.notes,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

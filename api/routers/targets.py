import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace, get_current_role
from api.database import get_db
from api.models.finding import Finding
from api.models.target import Target
from api.models.user import User
from api.models.workspace import Workspace

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


class BulkImportTarget(BaseModel):
    email: EmailStr
    country_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class BulkImport(BaseModel):
    emails: list[EmailStr] | None = None
    targets: list[BulkImportTarget] | None = None
    country_code: str | None = None
    tags: list[str] | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_target(
    body: TargetCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    role: str = Depends(get_current_role),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Target).where(Target.workspace_id == workspace_id, Target.email == body.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target already exists in workspace")

    # Plan enforcement: check target limit
    ws = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = ws.scalar_one_or_none()
    plan_name = workspace.plan if workspace else "free"
    current_count = await db.scalar(
        select(func.count()).select_from(Target).where(Target.workspace_id == workspace_id)
    ) or 0
    from api.services.plan_config import check_target_limit
    allowed, msg = check_target_limit(plan_name, current_count, role)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

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
    # Support both legacy format (emails list) and new format (targets with names)
    entries = []
    if body.targets:
        entries = [
            {"email": t.email, "country_code": t.country_code or body.country_code,
             "first_name": t.first_name, "last_name": t.last_name}
            for t in body.targets
        ]
    elif body.emails:
        entries = [{"email": e, "country_code": body.country_code, "first_name": None, "last_name": None} for e in body.emails]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide 'emails' or 'targets'")

    if len(entries) > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 500 entries per import")

    created = []
    skipped = []
    for entry in entries:
        email = entry["email"]
        existing = await db.execute(
            select(Target).where(Target.workspace_id == workspace_id, Target.email == email)
        )
        if existing.scalar_one_or_none():
            skipped.append(email)
            continue
        target = Target(
            workspace_id=workspace_id,
            email=email,
            country_code=entry.get("country_code"),
            user_first_name=entry["first_name"].strip()[:100] if entry.get("first_name") else None,
            user_last_name=entry["last_name"].strip()[:100] if entry.get("last_name") else None,
            tags=body.tags,
        )
        if target.user_first_name or target.user_last_name:
            parts = [target.user_first_name, target.user_last_name]
            target.display_name = ' '.join(p for p in parts if p)
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

    # Get deduplicated findings count by severity (Python-side dedup)
    result = await db.execute(
        select(Finding).where(Finding.target_id == target_id, Finding.workspace_id == workspace_id)
    )
    all_findings = result.scalars().all()
    # Dedup: keep latest per (module, title)
    seen = {}
    for f in all_findings:
        key = (f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    deduped = list(seen.values())
    from collections import Counter
    severity_counts = dict(Counter(f.severity for f in deduped))

    data = _target_dict(target)
    data["findings_by_severity"] = severity_counts
    return data


@router.get("/{target_id}/sources")
async def get_target_sources(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get per-source scoring and confidence data for a target."""
    await _get_target(db, target_id, workspace_id)

    # source_scoring uses sync session, run in executor
    from api.services.layer4.source_scoring import compute_source_scores
    from api.tasks.utils import get_sync_session
    import asyncio

    def _compute():
        session = get_sync_session()
        try:
            return compute_source_scores(target_id, session)
        finally:
            session.close()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _compute)
    return result


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
    profile["threat_score"] = target.threat_score
    profile["score_breakdown"] = target.score_breakdown
    profile["status"] = target.status
    profile["country_code"] = target.country_code
    profile["user_first_name"] = target.user_first_name
    profile["user_last_name"] = target.user_last_name
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


class IdentityUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


@router.patch("/{target_id}/identity")
async def update_target_identity(
    target_id: uuid.UUID,
    body: IdentityUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update operator-asserted identity. Set fields to null to clear."""
    target = await _get_target(db, target_id, workspace_id)

    if body.first_name is not None:
        target.user_first_name = body.first_name.strip()[:100] if body.first_name else None
    if body.last_name is not None:
        target.user_last_name = body.last_name.strip()[:100] if body.last_name else None

    # Update display_name immediately when operator sets a name
    if target.user_first_name or target.user_last_name:
        parts = [target.user_first_name, target.user_last_name]
        target.display_name = ' '.join(p for p in parts if p)
    # If both explicitly cleared, don't reset display_name — let next scan re-resolve

    await db.commit()
    await db.refresh(target)
    return {
        "id": str(target.id),
        "user_first_name": target.user_first_name,
        "user_last_name": target.user_last_name,
        "display_name": target.display_name,
    }


class CountryUpdate(BaseModel):
    country_code: str | None = None


@router.patch("/{target_id}/country")
async def update_target_country(
    target_id: uuid.UUID,
    body: CountryUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update target country_code. Set to null to clear."""
    target = await _get_target(db, target_id, workspace_id)

    country_code = body.country_code
    if country_code is not None:
        country_code = country_code.upper().strip()
        if len(country_code) != 2 or not country_code.isalpha():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="country_code must be a 2-letter ISO code or null",
            )

    target.country_code = country_code
    await db.commit()
    await db.refresh(target)
    return {"id": str(target.id), "country_code": target.country_code}


@router.patch("/{target_id}/move")
async def move_target(
    target_id: uuid.UUID,
    body: dict,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Move a target (+ findings + scans + identities) to another workspace."""
    target = await _get_target(db, target_id, workspace_id)
    new_ws_id = uuid.UUID(body["workspace_id"])

    # Verify user has access to destination workspace
    from api.models.user import UserWorkspace
    dest_membership = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == user.id,
            UserWorkspace.workspace_id == new_ws_id,
        )
    )
    dest_member = dest_membership.scalar_one_or_none()
    if not dest_member or dest_member.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Must be admin in destination workspace")

    # Move target + related data
    target.workspace_id = new_ws_id
    await db.execute(
        update(Finding).where(Finding.target_id == target_id).values(workspace_id=new_ws_id)
    )
    from api.models.scan import Scan
    await db.execute(
        update(Scan).where(Scan.target_id == target_id).values(workspace_id=new_ws_id)
    )
    from api.models.identity import Identity
    await db.execute(
        update(Identity).where(Identity.target_id == target_id).values(workspace_id=new_ws_id)
    )

    await db.commit()
    return {"moved": True, "target_id": str(target_id), "new_workspace_id": str(new_ws_id)}


async def _get_target(db: AsyncSession, target_id: uuid.UUID, workspace_id: uuid.UUID) -> Target:
    result = await db.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target


@router.get("/{target_id}/fingerprint")
async def get_fingerprint(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return stored fingerprint (includes eigenvalues + avatar_seed).
    Falls back to live recompute if no stored fingerprint exists."""
    target = await _get_target(db, target_id, workspace_id)

    # First: return stored fingerprint (has avatar_seed from finalize_scan)
    stored_fp = (target.profile_data or {}).get("fingerprint")
    if stored_fp and stored_fp.get("avatar_seed"):
        return stored_fp

    # Fallback: recompute with links (for targets scanned before eigenvalue support)
    import asyncio
    from api.tasks.utils import get_sync_session
    from api.services.layer4.fingerprint_engine import FingerprintEngine

    def _compute():
        session = get_sync_session()
        try:
            from api.models.finding import Finding as F
            from api.models.identity import Identity as I
            from api.models.identity import IdentityLink as IL
            # Deduplicate: latest finding per (module, title) — Python-side
            all_findings = session.execute(
                select(F).where(F.target_id == target_id, F.workspace_id == workspace_id)
            ).scalars().all()
            seen_fp = {}
            for f in all_findings:
                key = (f.module, f.title)
                ex = seen_fp.get(key)
                if ex is None or (f.created_at and (not ex.created_at or f.created_at > ex.created_at)):
                    seen_fp[key] = f
            findings = list(seen_fp.values())
            identities = session.execute(
                select(I).where(I.target_id == target_id, I.workspace_id == workspace_id)
            ).scalars().all()

            # Load links for eigenvalue computation
            id_set = set(i.id for i in identities)
            all_links = session.execute(
                select(IL).where(IL.workspace_id == workspace_id)
            ).scalars().all()
            target_links = [l for l in all_links if l.source_id in id_set or l.dest_id in id_set]

            engine = FingerprintEngine()
            return engine.compute(findings, identities, target.profile_data, target.email, links=target_links)
        finally:
            session.close()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compute)


@router.get("/{target_id}/fingerprint/history")
async def get_fingerprint_history(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return fingerprint snapshots over time."""
    target = await _get_target(db, target_id, workspace_id)
    return {"snapshots": target.fingerprint_history or []}


@router.get("/{target_id}/fingerprint/compare")
async def compare_fingerprints(
    target_id: uuid.UUID,
    with_target: uuid.UUID = Query(..., alias="with"),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare fingerprints of two targets side by side."""
    target_a = await _get_target(db, target_id, workspace_id)
    target_b = await _get_target(db, with_target, workspace_id)

    fp_a = (target_a.profile_data or {}).get("fingerprint")
    fp_b = (target_b.profile_data or {}).get("fingerprint")

    diff = {}
    if fp_a and fp_b:
        axes_a = fp_a.get("axes", {})
        axes_b = fp_b.get("axes", {})
        for key in set(list(axes_a.keys()) + list(axes_b.keys())):
            diff[key] = round((axes_a.get(key, 0) or 0) - (axes_b.get(key, 0) or 0), 3)

    return {
        "target_a": {"id": str(target_id), "email": target_a.email, "fingerprint": fp_a},
        "target_b": {"id": str(with_target), "email": target_b.email, "fingerprint": fp_b},
        "diff": diff,
    }


_QUICK_REJECT_NAMES = {
    "lastpass", "office365", "eventbrite", "spotify", "firefox", "chrome",
    "safari", "office", "1password", "bitwarden", "dashlane", "nordpass",
}


def _target_dict(t: Target) -> dict:
    fp = (t.profile_data or {}).get("fingerprint") if t.profile_data else None
    profile = t.profile_data or {}

    # Operator assertion ALWAYS wins for display name
    if t.user_first_name or t.user_last_name:
        display = ' '.join(p for p in [t.user_first_name, t.user_last_name] if p)
    else:
        display = t.display_name or profile.get("primary_name", "")
        if display and display.strip().lower() in _QUICK_REJECT_NAMES:
            display = None
    # Location data for geo map
    best_location = None
    user_locs = profile.get("user_locations", [])
    if user_locs:
        for ul in user_locs:
            if ul.get("lat") and ul.get("lon"):
                best_location = {
                    "lat": ul["lat"],
                    "lon": ul["lon"],
                    "label": ul.get("city") or ul.get("location") or ul.get("country", ""),
                    "type": "self_reported",
                }
                break
    if not best_location:
        geo_locs = profile.get("geo_locations", [])
        if geo_locs and isinstance(geo_locs, list) and geo_locs[0].get("lat"):
            gl = geo_locs[0]
            label_parts = [gl.get("city", ""), gl.get("country", "")]
            best_location = {
                "lat": gl["lat"],
                "lon": gl["lon"],
                "label": ", ".join(p for p in label_parts if p),
                "type": "server",
            }

    return {
        "id": str(t.id),
        "email": t.email,
        "display_name": display,
        "avatar_url": t.avatar_url,
        "primary_name": display or (profile.get("primary_name") if display else None),
        "country_code": t.country_code,
        "user_first_name": t.user_first_name,
        "user_last_name": t.user_last_name,
        "primary_name_source": "operator" if (t.user_first_name or t.user_last_name) else profile.get("primary_name_source", "auto"),
        "auto_resolved_name": profile.get("_auto_resolved_name"),
        "status": t.status,
        "exposure_score": t.exposure_score,
        "threat_score": t.threat_score,
        "score_breakdown": t.score_breakdown,
        "first_scanned": t.first_scanned.isoformat() if t.first_scanned else None,
        "last_scanned": t.last_scanned.isoformat() if t.last_scanned else None,
        "tags": t.tags,
        "notes": t.notes,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "fingerprint_hash": fp.get("hash") if fp else None,
        "fingerprint_score": fp.get("score") if fp else None,
        "fingerprint_risk": fp.get("risk_level") if fp else None,
        "fingerprint_avatar_seed": fp.get("avatar_seed") if fp else None,
        "fingerprint_axes": fp.get("axes") if fp else None,
        "location_data": best_location,
        "location_label": profile.get("location", ""),
        "geo_locations": profile.get("geo_locations", []),
        "user_locations": profile.get("user_locations", []),
    }

"""Consulting cases router (Sprint 112).

Internal tooling — gated to ``superadmin / admin / consultant`` roles. Generates
Markdown drafts of Play-1 consulting tiers (Quick / Assessment / Deep) from
already-scanned targets in the workspace.

Persistence: rows in the existing ``reports`` table with ``type=consulting_<tier>``.
Files on disk at ``/var/xposetip/consulting/{report_id}.md``.
"""

import logging
import os
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import (
    get_current_user,
    get_current_workspace,
    require_role,
)
from api.database import get_db
from api.models.report import Report
from api.models.target import Target
from api.models.user import User
from api.services.report.consulting_generator import (
    build_deep_investigation,
    build_identity_assessment,
    build_quick_profile,
)

router = APIRouter()
logger = logging.getLogger(__name__)

CONSULTING_DIR = "/var/xposetip/consulting"

TIER_COUNTS = {
    "quick": (1, 1),
    "assessment": (2, 3),
    "deep": (5, 10),
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConsultingCaseCreate(BaseModel):
    tier: str = Field(..., description="quick | assessment | deep")
    client_name: str
    scope: str
    deadline: str  # ISO YYYY-MM-DD
    target_ids: list[uuid.UUID]
    primary_target_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_payload(payload: ConsultingCaseCreate) -> None:
    if payload.tier not in TIER_COUNTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid tier '{payload.tier}'. Expected one of: quick, assessment, deep.",
        )
    if not payload.client_name or not payload.client_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="client_name is required.",
        )
    if not payload.scope or not payload.scope.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="scope is required.",
        )
    try:
        date.fromisoformat(payload.deadline)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="deadline must be ISO YYYY-MM-DD.",
        )

    lo, hi = TIER_COUNTS[payload.tier]
    if not (lo <= len(payload.target_ids) <= hi):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tier '{payload.tier}' requires {lo}-{hi} target_ids "
            f"(got {len(payload.target_ids)}).",
        )

    if payload.primary_target_id and payload.primary_target_id not in payload.target_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="primary_target_id must be one of the supplied target_ids.",
        )


async def _fetch_workspace_targets(
    db: AsyncSession, target_ids: list[uuid.UUID], workspace_id: uuid.UUID
) -> list[Target]:
    if not target_ids:
        return []
    result = await db.execute(
        select(Target).where(
            Target.id.in_(target_ids),
            Target.workspace_id == workspace_id,
        )
    )
    return list(result.scalars().all())


def _dispatch_builder(tier: str, targets: list[Target], case_meta: dict) -> str:
    if tier == "quick":
        return build_quick_profile(targets[0], case_meta)
    if tier == "assessment":
        return build_identity_assessment(targets, case_meta)
    if tier == "deep":
        return build_deep_investigation(targets, case_meta)
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unknown tier '{tier}'.",
    )


def _row_to_summary(row: Report) -> dict:
    sections = row.sections or {}
    return {
        "id": str(row.id),
        "type": row.type,
        "client_name": sections.get("client_name"),
        "target_count": len(sections.get("target_ids") or []),
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
    }


def _row_to_detail(row: Report) -> dict:
    return {
        "id": str(row.id),
        "type": row.type,
        "file_path": row.file_path,
        "file_size": row.file_size,
        "sections": row.sections or {},
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        "target_id": str(row.target_id) if row.target_id else None,
        "workspace_id": str(row.workspace_id) if row.workspace_id else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/cases")
async def create_case(
    payload: ConsultingCaseCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
):
    _validate_payload(payload)

    targets = await _fetch_workspace_targets(db, payload.target_ids, workspace_id)
    found_ids = {t.id for t in targets}
    missing = [str(tid) for tid in payload.target_ids if tid not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Some target_ids not found in this workspace.",
                "missing": missing,
            },
        )

    no_profile = [str(t.id) for t in targets if t.profile_data is None]
    if no_profile:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Some targets have no profile_data — run a scan first.",
                "missing_profile_data": no_profile,
            },
        )

    # Preserve requested order
    by_id = {t.id: t for t in targets}
    targets_ordered = [by_id[tid] for tid in payload.target_ids]

    primary_id = payload.primary_target_id or payload.target_ids[0]
    case_meta = {
        "client_name": payload.client_name.strip(),
        "scope": payload.scope.strip(),
        "deadline": payload.deadline,
        "primary_target_id": str(primary_id),
        "analyst": user.email or str(user.id),
        "analyst_user_id": str(user.id),
    }

    markdown = _dispatch_builder(payload.tier, targets_ordered, case_meta)
    payload_bytes = markdown.encode("utf-8")

    os.makedirs(CONSULTING_DIR, exist_ok=True)
    report_id = uuid.uuid4()
    file_path = os.path.join(CONSULTING_DIR, f"{report_id}.md")
    with open(file_path, "wb") as fh:
        fh.write(payload_bytes)

    sections = {
        "client_name": case_meta["client_name"],
        "scope": case_meta["scope"],
        "deadline": case_meta["deadline"],
        "target_ids": [str(t.id) for t in targets_ordered],
        "primary_target_id": str(primary_id),
        "analyst_user_id": case_meta["analyst_user_id"],
        "analyst_email": user.email,
        "tier": payload.tier,
    }

    # NOTE: type column is VARCHAR(20); 'consulting_assessment' (21 chars) overflows it,
    # and Sprint 112 hard rule #3 forbids any alembic migration. Use the compact
    # 'consult_<tier>' prefix instead — max is 'consult_assessment' = 18 chars.
    row = Report(
        id=report_id,
        workspace_id=workspace_id,
        target_id=primary_id,
        type=f"consult_{payload.tier}",
        file_path=file_path,
        file_size=len(payload_bytes),
        sections=sections,
    )
    db.add(row)
    await db.commit()

    logger.info(
        "Consulting case created: id=%s tier=%s targets=%d analyst=%s",
        report_id,
        payload.tier,
        len(targets_ordered),
        user.email,
    )

    return {
        "report_id": str(report_id),
        "file_path": file_path,
        "file_size": len(payload_bytes),
        "download_url": f"/api/v1/consulting/cases/{report_id}/download",
    }


@router.get("/cases")
async def list_cases(
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Report)
        .where(
            Report.workspace_id == workspace_id,
            Report.type.like("consult_%"),
        )
        .order_by(Report.generated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list(result.scalars().all())
    return [_row_to_summary(r) for r in rows]


@router.get("/cases/{report_id}")
async def get_case(
    report_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.workspace_id == workspace_id,
            Report.type.like("consult_%"),
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return _row_to_detail(row)


@router.get("/cases/{report_id}/download")
async def download_case(
    report_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.workspace_id == workspace_id,
            Report.type.like("consult_%"),
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if not row.file_path or not os.path.isfile(row.file_path):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Case file no longer present on disk.",
        )

    short = str(row.id)[:8]
    filename = f"xposeTIP_{row.type}_{short}.md"

    def _iter():
        with open(row.file_path, "rb") as fh:
            while True:
                chunk = fh.read(8192)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        _iter(),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/cases/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    report_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.workspace_id == workspace_id,
            Report.type.like("consult_%"),
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    file_path = row.file_path
    await db.delete(row)
    await db.commit()

    if file_path:
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            logger.warning("Consulting case file already missing on delete: %s", file_path)
        except OSError as e:
            logger.warning("Failed to unlink consulting file %s: %s", file_path, e)

    return None

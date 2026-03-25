"""PDF report endpoint — generates branded identity reports."""

import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.target import Target
from api.models.workspace import Workspace

router = APIRouter()


@router.get("/targets/{target_id}/report/pdf")
async def generate_pdf_report(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a PDF identity report for a target.

    Tier auto-detected from workspace plan:
    - free: Executive 1-pager (teaser)
    - pro/consultant/enterprise: Full 5-page report
    """
    # Fetch target scoped to workspace
    result = await db.execute(
        select(Target).where(
            Target.id == target_id,
            Target.workspace_id == workspace_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    if not target.profile_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile data available. Run a scan first.",
        )

    # Get workspace plan
    ws_result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = ws_result.scalar_one_or_none()
    tier = workspace.plan if workspace else "free"

    # Generate PDF
    from api.services.report.pdf_generator import generate_identity_report

    profile = target.profile_data or {}
    pdf_bytes = generate_identity_report(target, profile, tier)

    # Build filename
    email_safe = (target.email or "unknown").replace("@", "_at_")
    filename = f"xposeTIP_report_{email_safe}_{date.today()}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

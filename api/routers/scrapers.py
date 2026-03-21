import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.scraper import Scraper
from api.models.user import User

router = APIRouter()


class ScraperCreate(BaseModel):
    name: str
    display_name: str | None = None
    description: str | None = None
    category: str | None = "social"
    url_template: str
    method: str = "GET"
    headers: dict | None = None
    cookies: dict | None = None
    body_template: str | None = None
    input_type: str = "username"
    input_transform: str | None = None
    extraction_rules: list = []
    finding_title_template: str | None = None
    finding_category: str | None = "social_account"
    finding_severity: str | None = "low"
    identity_type: str | None = "username"
    rate_limit_requests: int = 1
    rate_limit_window: int = 2
    success_indicator: str | None = None
    not_found_indicators: list | None = None
    requires_auth: bool = False
    notes: str | None = None


class ScraperUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    category: str | None = None
    url_template: str | None = None
    method: str | None = None
    headers: dict | None = None
    cookies: dict | None = None
    body_template: str | None = None
    input_type: str | None = None
    input_transform: str | None = None
    extraction_rules: list | None = None
    finding_title_template: str | None = None
    finding_category: str | None = None
    finding_severity: str | None = None
    identity_type: str | None = None
    rate_limit_requests: int | None = None
    rate_limit_window: int | None = None
    success_indicator: str | None = None
    not_found_indicators: list | None = None
    notes: str | None = None


class ScraperTest(BaseModel):
    input: str


@router.get("")
async def list_scrapers(
    category: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Scraper).where(
        (Scraper.workspace_id == workspace_id) | (Scraper.workspace_id.is_(None))
    )
    if category:
        q = q.where(Scraper.category == category)
    q = q.order_by(Scraper.category, Scraper.name)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    scrapers = result.scalars().all()

    return {
        "items": [s.to_dict() for s in scrapers],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{scraper_id}")
async def get_scraper(
    scraper_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraper = await _get_scraper(db, scraper_id, workspace_id)
    return scraper.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_scraper(
    body: ScraperCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Scraper).where(Scraper.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Scraper name already exists")

    scraper = Scraper(
        workspace_id=workspace_id,
        **body.model_dump(),
    )
    db.add(scraper)
    await db.commit()
    await db.refresh(scraper)
    return scraper.to_dict()


@router.patch("/{scraper_id}")
async def update_scraper(
    scraper_id: uuid.UUID,
    body: ScraperUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraper = await _get_scraper(db, scraper_id, workspace_id)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scraper, key, value)
    await db.commit()
    await db.refresh(scraper)
    return scraper.to_dict()


@router.delete("/{scraper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scraper(
    scraper_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraper = await _get_scraper(db, scraper_id, workspace_id)
    await db.delete(scraper)
    await db.commit()


@router.post("/{scraper_id}/test")
async def test_scraper(
    scraper_id: uuid.UUID,
    body: ScraperTest,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a scraper against a sample input and return extraction results."""
    scraper = await _get_scraper(db, scraper_id, workspace_id)

    from api.services.scraper_engine import ScraperEngine
    engine = ScraperEngine()
    try:
        result = await engine.execute(scraper.to_dict(), body.input)
    finally:
        await engine.close()

    # Update test status
    scraper.last_tested = datetime.now(timezone.utc)
    if result.get("error"):
        scraper.last_test_status = "broken"
    elif result.get("found"):
        scraper.last_test_status = "working"
    else:
        scraper.last_test_status = "not_found"
    await db.commit()

    return result


@router.post("/{scraper_id}/toggle")
async def toggle_scraper(
    scraper_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraper = await _get_scraper(db, scraper_id, workspace_id)
    scraper.enabled = not scraper.enabled
    await db.commit()
    return {"id": str(scraper.id), "enabled": scraper.enabled}


@router.post("/{scraper_id}/export")
async def export_scraper(
    scraper_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraper = await _get_scraper(db, scraper_id, workspace_id)
    data = scraper.to_dict()
    # Remove internal fields
    for key in ("id", "created_at", "updated_at", "last_tested", "last_test_status"):
        data.pop(key, None)
    return {"xpose_scraper_v1": data}


@router.post("/import")
async def import_scraper(
    body: dict,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.get("xpose_scraper_v1")
    if not data:
        raise HTTPException(status_code=400, detail="Invalid scraper format. Expected xpose_scraper_v1 key.")

    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Scraper name is required.")

    existing = await db.execute(select(Scraper).where(Scraper.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Scraper '{name}' already exists.")

    # Remove fields that shouldn't be imported
    for key in ("id", "created_at", "updated_at", "last_tested", "last_test_status", "workspace_id"):
        data.pop(key, None)

    scraper = Scraper(workspace_id=workspace_id, **data)
    db.add(scraper)
    await db.commit()
    await db.refresh(scraper)
    return scraper.to_dict()


async def _get_scraper(db: AsyncSession, scraper_id: uuid.UUID, workspace_id: uuid.UUID) -> Scraper:
    result = await db.execute(
        select(Scraper).where(
            Scraper.id == scraper_id,
            (Scraper.workspace_id == workspace_id) | (Scraper.workspace_id.is_(None)),
        )
    )
    scraper = result.scalar_one_or_none()
    if not scraper:
        raise HTTPException(status_code=404, detail="Scraper not found")
    return scraper

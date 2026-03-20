from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.database import get_db
from api.models.module import Module
from api.models.user import User

router = APIRouter()


class ModuleUpdate(BaseModel):
    enabled: bool


@router.get("")
async def list_modules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).order_by(Module.layer, Module.id))
    modules = result.scalars().all()
    return [_module_dict(m) for m in modules]


@router.patch("/{module_id}")
async def update_module(
    module_id: str,
    body: ModuleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    module.enabled = body.enabled
    await db.commit()
    await db.refresh(module)
    return _module_dict(module)


def _module_dict(m: Module) -> dict:
    return {
        "id": m.id,
        "display_name": m.display_name,
        "description": m.description,
        "layer": m.layer,
        "category": m.category,
        "enabled": m.enabled,
        "requires_auth": m.requires_auth,
        "rate_limit": m.rate_limit,
        "supported_regions": m.supported_regions,
        "version": m.version,
        "health_status": m.health_status,
        "last_health": m.last_health.isoformat() if m.last_health else None,
    }

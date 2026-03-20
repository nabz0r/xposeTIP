import asyncio
import importlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.database import get_db
from api.models.module import Module
from api.models.user import User
from api.tasks.module_tasks import SCANNER_REGISTRY

router = APIRouter()
logger = logging.getLogger(__name__)


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


def _load_scanner(module_id: str):
    """Load a scanner instance by module_id from SCANNER_REGISTRY."""
    path = SCANNER_REGISTRY.get(module_id)
    if not path:
        return None
    module_path, class_name = path.split(":")
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)()
    except Exception:
        logger.exception("Failed to load scanner %s", module_id)
        return None


@router.post("/{module_id}/health")
async def check_module_health(
    module_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    if module_id not in SCANNER_REGISTRY:
        module.health_status = "unknown"
        module.last_health = datetime.now(timezone.utc)
        await db.commit()
        return {"module_id": module_id, "health_status": "unknown", "reason": "no scanner implemented"}

    scanner = _load_scanner(module_id)
    if not scanner:
        module.health_status = "unhealthy"
        module.last_health = datetime.now(timezone.utc)
        await db.commit()
        return {"module_id": module_id, "health_status": "unhealthy", "reason": "scanner failed to load"}

    try:
        healthy = await scanner.health_check()
        health_status = "healthy" if healthy else "unhealthy"
    except Exception as e:
        logger.exception("Health check failed for %s", module_id)
        health_status = "unhealthy"

    module.health_status = health_status
    module.last_health = datetime.now(timezone.utc)
    await db.commit()

    return {"module_id": module_id, "health_status": health_status}


@router.post("/health-all")
async def check_all_modules_health(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module))
    modules = result.scalars().all()
    results = []

    for module in modules:
        if module.id not in SCANNER_REGISTRY:
            module.health_status = "unknown"
            module.last_health = datetime.now(timezone.utc)
            results.append({"module_id": module.id, "health_status": "unknown"})
            continue

        scanner = _load_scanner(module.id)
        if not scanner:
            module.health_status = "unhealthy"
            module.last_health = datetime.now(timezone.utc)
            results.append({"module_id": module.id, "health_status": "unhealthy"})
            continue

        try:
            healthy = await scanner.health_check()
            health_status = "healthy" if healthy else "unhealthy"
        except Exception:
            health_status = "unhealthy"

        module.health_status = health_status
        module.last_health = datetime.now(timezone.utc)
        results.append({"module_id": module.id, "health_status": health_status})

    await db.commit()
    return {"results": results, "total": len(results)}


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
        "implemented": m.id in SCANNER_REGISTRY,
    }

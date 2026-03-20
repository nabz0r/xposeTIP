import logging
import os
from typing import Optional

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace, require_role
from api.database import get_db
from api.models.module import Module
from api.models.user import User
from api.models.workspace import Workspace

router = APIRouter()
logger = logging.getLogger(__name__)

# Fernet key — reuse SECRET_KEY padded/hashed to 32 bytes for Fernet
_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        from api.config import settings
        import hashlib
        import base64
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        _fernet = Fernet(base64.urlsafe_b64encode(key))
    return _fernet


def _encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


# Key descriptions for known keys
KEY_DESCRIPTIONS = {
    "HIBP_API_KEY": "HaveIBeenPwned — breach + paste detection ($3.50/mo)",
    "MAXMIND_LICENSE": "MaxMind GeoLite2 — IP geolocation database (free tier)",
}


class ApiKeyRequest(BaseModel):
    key_name: str
    key_value: str
    description: str | None = None


class CustomKeyRequest(BaseModel):
    key_name: str
    key_value: str
    description: str = ""


class DefaultsRequest(BaseModel):
    default_modules: list[str] = []
    rate_limit: float = 1.0


# ---- API Keys ----

@router.post("/apikeys")
async def save_api_key(
    body: ApiKeyRequest,
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings_data = dict(ws.settings or {})
    api_keys = dict(settings_data.get("api_keys", {}))
    api_keys[body.key_name] = {
        "encrypted": _encrypt(body.key_value),
        "masked": _mask(body.key_value),
    }
    if body.description:
        api_keys[body.key_name]["description"] = body.description
    settings_data["api_keys"] = api_keys
    ws.settings = settings_data
    await db.commit()

    return {"key_name": body.key_name, "masked": _mask(body.key_value), "valid": None}


@router.get("/apikeys")
async def list_api_keys(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get all modules that require auth
    modules_result = await db.execute(
        select(Module).where(Module.requires_auth == True).order_by(Module.layer, Module.id)
    )
    auth_modules = modules_result.scalars().all()

    api_keys = (ws.settings or {}).get("api_keys", {})
    result = []

    # Build entries from modules that require auth
    seen_keys = set()
    for mod in auth_modules:
        auth_config = mod.auth_config or {}
        key_name = auth_config.get("api_key_env")
        if not key_name:
            continue
        if key_name in seen_keys:
            continue
        seen_keys.add(key_name)

        entry = api_keys.get(key_name)
        description = KEY_DESCRIPTIONS.get(key_name, f"API key for {mod.display_name}")

        if entry:
            result.append({
                "key_name": key_name,
                "module_id": mod.id,
                "module_name": mod.display_name,
                "description": description,
                "masked": entry.get("masked", "****"),
                "valid": entry.get("valid"),
                "last_validated": entry.get("last_validated"),
                "custom": False,
            })
        else:
            env_val = os.environ.get(key_name, "")
            result.append({
                "key_name": key_name,
                "module_id": mod.id,
                "module_name": mod.display_name,
                "description": description,
                "masked": _mask(env_val) if env_val else None,
                "valid": None,
                "last_validated": None,
                "source": "env" if env_val else None,
                "custom": False,
            })

    # Add custom keys (stored in workspace.settings but not tied to a module)
    custom_keys = (ws.settings or {}).get("custom_api_keys", {})
    for key_name, entry in custom_keys.items():
        result.append({
            "key_name": key_name,
            "module_id": None,
            "module_name": None,
            "description": entry.get("description", "Custom API key"),
            "masked": entry.get("masked", "****"),
            "valid": entry.get("valid"),
            "last_validated": entry.get("last_validated"),
            "custom": True,
        })

    return result


@router.post("/apikeys/custom")
async def save_custom_key(
    body: CustomKeyRequest,
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings_data = dict(ws.settings or {})
    custom_keys = dict(settings_data.get("custom_api_keys", {}))
    custom_keys[body.key_name] = {
        "encrypted": _encrypt(body.key_value),
        "masked": _mask(body.key_value),
        "description": body.description,
    }
    settings_data["custom_api_keys"] = custom_keys
    ws.settings = settings_data
    await db.commit()

    return {"key_name": body.key_name, "masked": _mask(body.key_value), "custom": True}


@router.post("/apikeys/{key_name}/validate")
async def validate_api_key(
    key_name: str,
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get actual key value — check both standard and custom keys
    api_keys = (ws.settings or {}).get("api_keys", {})
    custom_keys = (ws.settings or {}).get("custom_api_keys", {})
    entry = api_keys.get(key_name) or custom_keys.get(key_name)
    is_custom = key_name in custom_keys

    if entry:
        try:
            api_key = _decrypt(entry["encrypted"])
        except Exception:
            return {"valid": False, "message": "Failed to decrypt stored key"}
    else:
        api_key = os.environ.get(key_name, "")

    if not api_key:
        return {"valid": False, "message": "Key not configured"}

    valid = False
    message = "Validation not available for this key type"

    if key_name == "HIBP_API_KEY":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://haveibeenpwned.com/api/v3/breachedaccount/test@example.com",
                    headers={"hibp-api-key": api_key, "user-agent": "xpose-tip"},
                    params={"truncateResponse": "true"},
                )
                if resp.status_code == 401:
                    valid = False
                    message = "Invalid API key (401 Unauthorized)"
                elif resp.status_code in (200, 404):
                    valid = True
                    message = "API key is valid"
                else:
                    valid = False
                    message = f"Unexpected response: {resp.status_code}"
        except Exception as e:
            valid = False
            message = f"Connection error: {str(e)}"

    elif key_name == "MAXMIND_LICENSE":
        db_path = os.environ.get("MAXMIND_DB_PATH", "data/maxmind/GeoLite2-City.mmdb")
        if os.path.exists(db_path):
            valid = True
            message = "GeoLite2 database found"
        else:
            valid = False
            message = f"GeoLite2 database not found at {db_path}. Download it with your license key."

    elif is_custom:
        # Custom keys: just check it's non-empty
        valid = bool(api_key)
        message = "Key is stored" if valid else "Key is empty"

    # Store validation result
    from datetime import datetime, timezone
    settings_data = dict(ws.settings or {})
    store_key = "custom_api_keys" if is_custom else "api_keys"
    keys_data = dict(settings_data.get(store_key, {}))
    if key_name in keys_data:
        keys_data[key_name]["valid"] = valid
        keys_data[key_name]["last_validated"] = datetime.now(timezone.utc).isoformat()
        settings_data[store_key] = keys_data
        ws.settings = settings_data
        await db.commit()

    return {"valid": valid, "message": message}


@router.delete("/apikeys/{key_name}")
async def delete_api_key(
    key_name: str,
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings_data = dict(ws.settings or {})

    # Check both standard and custom keys
    api_keys = dict(settings_data.get("api_keys", {}))
    custom_keys = dict(settings_data.get("custom_api_keys", {}))

    if key_name in api_keys:
        del api_keys[key_name]
        settings_data["api_keys"] = api_keys
    elif key_name in custom_keys:
        del custom_keys[key_name]
        settings_data["custom_api_keys"] = custom_keys

    ws.settings = settings_data
    await db.commit()

    return {"deleted": True}


# ---- Scan Defaults ----

@router.get("/defaults")
async def get_defaults(
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings_data = ws.settings or {}
    return {
        "default_modules": settings_data.get("default_modules", ["email_validator", "holehe", "hibp"]),
        "rate_limit": settings_data.get("rate_limit", 1.0),
    }


@router.put("/defaults")
async def update_defaults(
    body: DefaultsRequest,
    role: str = Depends(require_role("superadmin", "admin")),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    workspace = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings_data = dict(ws.settings or {})
    settings_data["default_modules"] = body.default_modules
    settings_data["rate_limit"] = body.rate_limit
    ws.settings = settings_data
    await db.commit()

    return {"default_modules": body.default_modules, "rate_limit": body.rate_limit}


# ---- Helpers for scanners to read workspace API keys ----

def get_workspace_api_key(workspace_id, key_name: str, session) -> Optional[str]:
    """Read an API key from workspace settings (sync, for Celery workers)."""
    workspace = session.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    ).scalar_one_or_none()
    if not workspace:
        return None

    # Check standard api_keys first
    api_keys = (workspace.settings or {}).get("api_keys", {})
    entry = api_keys.get(key_name)
    if entry and "encrypted" in entry:
        try:
            return _decrypt(entry["encrypted"])
        except Exception:
            logger.warning("Failed to decrypt %s for workspace %s", key_name, workspace_id)

    # Check custom_api_keys
    custom_keys = (workspace.settings or {}).get("custom_api_keys", {})
    entry = custom_keys.get(key_name)
    if entry and "encrypted" in entry:
        try:
            return _decrypt(entry["encrypted"])
        except Exception:
            logger.warning("Failed to decrypt custom %s for workspace %s", key_name, workspace_id)

    # Fallback to env var
    return os.environ.get(key_name, "") or None

"""Connected Accounts router — OAuth2 flow for SaaS connectors."""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.account import Account

router = APIRouter()

# Supported providers and their connector classes
PROVIDERS = {
    "google": "api.services.layer3.google_connector:GoogleConnector",
    "microsoft": "api.services.layer3.microsoft_connector:MicrosoftConnector",
}


def _get_connector(provider: str):
    import importlib
    path = PROVIDERS.get(provider)
    if not path:
        return None
    module_path, class_name = path.split(":")
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)()
    except Exception:
        return None


class OAuthStartRequest(BaseModel):
    provider: str
    target_id: str
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    provider: str
    target_id: str
    code: str
    redirect_uri: str


class AccountResponse(BaseModel):
    id: str
    provider: str
    email: str | None
    display_name: str | None
    scopes: list[str] | None
    last_audited: str | None
    created_at: str


@router.get("")
async def list_accounts(
    target_id: str | None = None,
    user=Depends(get_current_user),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List connected accounts, optionally filtered by target."""
    query = select(Account).where(Account.workspace_id == workspace_id)
    if target_id:
        query = query.where(Account.target_id == uuid.UUID(target_id))
    query = query.order_by(Account.created_at.desc())

    result = await db.execute(query)
    accounts = result.scalars().all()

    return {
        "items": [
            {
                "id": str(a.id),
                "provider": a.provider,
                "email": a.email,
                "display_name": a.display_name,
                "scopes": a.scopes or [],
                "last_audited": a.last_audited.isoformat() if a.last_audited else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in accounts
        ],
        "providers": list(PROVIDERS.keys()),
    }


@router.post("/oauth/start")
async def oauth_start(
    req: OAuthStartRequest,
    user=Depends(get_current_user),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Generate OAuth authorization URL for a provider."""
    connector = _get_connector(req.provider)
    if not connector:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")

    # Load OAuth client credentials from workspace settings
    from api.routers.settings import get_workspace_api_key
    from api.tasks.utils import get_sync_session
    sync_session = get_sync_session()
    try:
        client_id = get_workspace_api_key(
            workspace_id,
            f"{req.provider.upper()}_CLIENT_ID",
            sync_session,
        )
        if not client_id:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth client ID not configured for {req.provider}. Add {req.provider.upper()}_CLIENT_ID in Settings.",
            )
    finally:
        sync_session.close()

    state = f"{req.target_id}:{uuid.uuid4().hex[:16]}"

    auth_url = await connector.get_auth_url(
        state=state,
        redirect_uri=req.redirect_uri,
        client_id=client_id,
    )

    return {"auth_url": auth_url, "state": state}


@router.post("/oauth/callback")
async def oauth_callback(
    req: OAuthCallbackRequest,
    user=Depends(get_current_user),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Exchange OAuth code for tokens and store account."""
    connector = _get_connector(req.provider)
    if not connector:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")

    # Load OAuth credentials
    from api.routers.settings import get_workspace_api_key
    from api.tasks.utils import get_sync_session
    sync_session = get_sync_session()
    try:
        client_id = get_workspace_api_key(
            workspace_id, f"{req.provider.upper()}_CLIENT_ID", sync_session,
        )
        client_secret = get_workspace_api_key(
            workspace_id, f"{req.provider.upper()}_CLIENT_SECRET", sync_session,
        )
    finally:
        sync_session.close()

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail=f"OAuth credentials not configured for {req.provider}")

    tokens = await connector.exchange_code(
        code=req.code,
        redirect_uri=req.redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
    )

    if not tokens.get("access_token"):
        raise HTTPException(status_code=400, detail="OAuth token exchange failed")

    # Check if account already exists for this target+provider
    existing = await db.execute(
        select(Account).where(
            Account.workspace_id == workspace_id,
            Account.target_id == uuid.UUID(req.target_id),
            Account.provider == req.provider,
        )
    )
    account = existing.scalar_one_or_none()

    if account:
        # Update tokens
        account.access_token = tokens["access_token"]
        account.refresh_token = tokens.get("refresh_token") or account.refresh_token
        account.token_expires = datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
        account.scopes = tokens.get("scopes", [])
    else:
        account = Account(
            workspace_id=workspace_id,
            target_id=uuid.UUID(req.target_id),
            provider=req.provider,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expires=datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600)),
            scopes=tokens.get("scopes", []),
        )
        db.add(account)

    await db.commit()
    await db.refresh(account)

    return {
        "id": str(account.id),
        "provider": account.provider,
        "status": "connected",
        "scopes": account.scopes,
    }


@router.post("/{account_id}/audit")
async def audit_account(
    account_id: str,
    user=Depends(get_current_user),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an audit on a connected account."""
    result = await db.execute(
        select(Account).where(
            Account.id == uuid.UUID(account_id),
            Account.workspace_id == workspace_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not account.access_token:
        raise HTTPException(status_code=400, detail="No access token — reconnect the account")

    # Check if token is expired, try refresh
    if account.token_expires and account.token_expires < datetime.now(timezone.utc):
        if account.refresh_token:
            connector = _get_connector(account.provider)
            if connector:
                from api.routers.settings import get_workspace_api_key
                from api.tasks.utils import get_sync_session
                sync_session = get_sync_session()
                try:
                    client_id = get_workspace_api_key(
                        workspace_id, f"{account.provider.upper()}_CLIENT_ID", sync_session,
                    )
                    client_secret = get_workspace_api_key(
                        workspace_id, f"{account.provider.upper()}_CLIENT_SECRET", sync_session,
                    )
                finally:
                    sync_session.close()

                new_tokens = await connector.refresh_access_token(
                    account.refresh_token,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                if new_tokens.get("access_token"):
                    account.access_token = new_tokens["access_token"]
                    account.token_expires = datetime.now(timezone.utc) + timedelta(
                        seconds=new_tokens.get("expires_in", 3600)
                    )
                    await db.commit()
                else:
                    raise HTTPException(status_code=400, detail="Token refresh failed — reconnect the account")
        else:
            raise HTTPException(status_code=400, detail="Token expired and no refresh token — reconnect the account")

    connector = _get_connector(account.provider)
    if not connector:
        raise HTTPException(status_code=400, detail=f"No connector for provider: {account.provider}")

    # Run audit
    findings = await connector.audit(
        email=account.email or "",
        access_token=account.access_token,
    )

    # Update account metadata
    account.last_audited = datetime.now(timezone.utc)
    account.audit_summary = {
        "findings_count": len(findings),
        "last_audit": datetime.now(timezone.utc).isoformat(),
    }
    await db.commit()

    return {
        "account_id": str(account.id),
        "provider": account.provider,
        "findings_count": len(findings),
        "findings": [
            {
                "title": f.title,
                "severity": f.severity,
                "category": f.category,
                "description": f.description,
            }
            for f in findings
        ],
    }


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: str,
    user=Depends(get_current_user),
    workspace_id=Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect (delete) a connected account."""
    result = await db.execute(
        select(Account).where(
            Account.id == uuid.UUID(account_id),
            Account.workspace_id == workspace_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await db.delete(account)
    await db.commit()
    return {"status": "disconnected"}

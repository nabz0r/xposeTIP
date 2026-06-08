"""SSO consent verification primitive (S232).

Subject-attested green flag: operator clicks "Request SSO consent" beside a
target's email, subject completes Google SSO on their device, backend verifies
`userinfo.email == target.email`, records a `consent_sso` BfpClaim, and the
email renders a green "Consent verified" badge.

Scopes are LEAN by design — only `openid email profile`. Google documents that
this exact subset does NOT trigger the "unverified app" warning, even for an
unverified OAuth client. Do NOT add sensitive scopes here; the audit connector
(`api/routers/accounts.py`) is intentionally a separate flow because it
requests `drive.metadata.readonly`.

The access token returned by Google is consumed once to fetch userinfo and
then DISCARDED. Nothing is written to the `accounts` table. The only
persistence is one append-only `bfp_claims` row of type `consent_sso`.

Path layout intentionally lives at the FastAPI root (not `/api/v1/...`)
because the OAuth redirect URI must equal an Authorized URI in the Google
Cloud console verbatim, and the demo config registers
`http://localhost:8000/consent/oauth/callback`. `CONSENT_REDIRECT_URI` is the
single source of truth used by BOTH the auth URL construction (start) and the
token exchange (callback) so they cannot drift.
"""
import logging
import os
import urllib.parse
import uuid
from datetime import datetime, timezone

import httpx
import redis as r
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.config import settings
from api.database import get_db
from api.models.bfp_claim import BfpClaim
from api.models.target import Target
from api.routers.settings import get_workspace_api_key
from api.services.bfp.claim_emitter import compute_claim_hash
from api.tasks.utils import get_sync_session

router = APIRouter()
logger = logging.getLogger(__name__)


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
# LEAN — do not add sensitive scopes here; Google's unverified-app warning
# screen is bypassed only for this exact subset.
CONSENT_SCOPES = "openid email profile"
STATE_TTL = 600
CLAIM_TYPE = "consent_sso"
# Backend-owned redirect URI. Used by BOTH start (auth_url) and callback
# (token exchange) so they ALWAYS match — Google rejects mismatches. Must
# EXACTLY equal an Authorized redirect URI in the Google Cloud console.
# This is the BACKEND (uvicorn :8000), NOT the Vite :5173 frontend.
CONSENT_REDIRECT_URI = os.getenv(
    "CONSENT_REDIRECT_URI", "http://localhost:8000/consent/oauth/callback"
)


class ConsentStartRequest(BaseModel):
    target_id: str


def _redis_client():
    return r.from_url(settings.REDIS_URL)


def _html(body: str, status_code: int = 200) -> HTMLResponse:
    """Minimal standalone HTML page rendered to the subject's browser."""
    html = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>xposeTIP — consent</title>"
        "<style>"
        "body{margin:0;min-height:100vh;display:flex;align-items:center;"
        "justify-content:center;background:#0a0a0f;color:#e5e7eb;"
        "font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;}"
        ".card{max-width:480px;padding:32px;background:#12121a;"
        "border:1px solid #1e1e2e;border-radius:12px;text-align:center;}"
        "p{margin:0;font-size:15px;line-height:1.5;}"
        "</style></head>"
        f"<body><div class=\"card\"><p>{body}</p></div></body></html>"
    )
    return HTMLResponse(content=html, status_code=status_code)


@router.post("/consent/oauth/start")
async def start(
    body: ConsentStartRequest,
    user=Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Issue a single-use state nonce + return the Google auth URL.

    Frontend opens auth_url in a new tab; the subject signs into their
    Google account; Google redirects back to `/consent/oauth/callback`.
    """
    try:
        target_uuid = uuid.UUID(body.target_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target_id")

    # Confirm target belongs to the current workspace before issuing state.
    result = await db.execute(
        select(Target).where(
            Target.id == target_uuid, Target.workspace_id == workspace_id
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    sync_session = get_sync_session()
    try:
        client_id = get_workspace_api_key(workspace_id, "GOOGLE_CLIENT_ID", sync_session)
    finally:
        sync_session.close()
    if not client_id:
        raise HTTPException(
            status_code=400, detail="GOOGLE_CLIENT_ID not configured in Settings"
        )

    nonce = uuid.uuid4().hex
    rc = _redis_client()
    try:
        rc.setex(
            f"consent:state:{nonce}",
            STATE_TTL,
            f"{workspace_id}:{target_uuid}",
        )
    finally:
        rc.close()

    params = {
        "client_id": client_id,
        "redirect_uri": CONSENT_REDIRECT_URI,
        "response_type": "code",
        "scope": CONSENT_SCOPES,
        "state": nonce,
        "access_type": "online",
        "prompt": "consent",
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url, "state": nonce}


@router.get("/consent/oauth/callback")
async def callback(code: str | None = None, state: str | None = None, db: AsyncSession = Depends(get_db)):
    """Google redirects the subject's browser here after they consent.

    Unauthenticated — the subject is not logged into xposeTIP. The state
    nonce binds this callback back to the (workspace, target) the operator
    issued the request for, and is single-use (GETDEL).
    """
    if not code or not state:
        return _html("⚠ Lien expiré ou invalide.", status_code=400)

    rc = _redis_client()
    try:
        raw = rc.getdel(f"consent:state:{state}")
    finally:
        rc.close()
    if not raw:
        return _html("⚠ Lien expiré ou invalide.", status_code=400)

    try:
        workspace_id_str, target_id_str = raw.decode().split(":", 1)
        workspace_id = uuid.UUID(workspace_id_str)
        target_uuid = uuid.UUID(target_id_str)
    except Exception:
        return _html("⚠ État invalide.", status_code=400)

    sync_session = get_sync_session()
    try:
        client_id = get_workspace_api_key(workspace_id, "GOOGLE_CLIENT_ID", sync_session)
        client_secret = get_workspace_api_key(
            workspace_id, "GOOGLE_CLIENT_SECRET", sync_session
        )
    finally:
        sync_session.close()
    if not client_id or not client_secret:
        return _html("⚠ Configuration OAuth manquante.", status_code=400)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": CONSENT_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                logger.warning("consent token exchange failed: %s", token_resp.text)
                return _html("⚠ Échec OAuth.", status_code=400)
            access_token = token_resp.json().get("access_token")
            if not access_token:
                return _html("⚠ Échec OAuth.", status_code=400)

            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_resp.status_code != 200:
                return _html("⚠ Échec userinfo.", status_code=400)
            userinfo = userinfo_resp.json()
    except Exception:
        logger.exception("consent OAuth exchange error")
        return _html("⚠ Échec OAuth.", status_code=400)
    # access_token deliberately not persisted — discarded with `client`.

    userinfo_email = (userinfo.get("email") or "").strip().lower()
    if not userinfo_email:
        return _html("⚠ Email Google introuvable.", status_code=400)

    result = await db.execute(
        select(Target).where(
            Target.id == target_uuid, Target.workspace_id == workspace_id
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        return _html("⚠ Target introuvable.", status_code=404)

    if userinfo_email != target.email.strip().lower():
        return _html(
            f"✗ L'email Google ({userinfo_email}) ne correspond pas à la cible. "
            "Consentement non enregistré.",
            status_code=200,
        )

    claim_value = f"google:{userinfo_email}"
    emitted_at = datetime.now(timezone.utc)
    claim_hash = compute_claim_hash(
        target_id=str(target_uuid),
        claim_type=CLAIM_TYPE,
        claim_value=claim_value,
        cross_verification_count=0,
        cross_verification_sources=[],
        verified_at_emission=True,
        emitted_at_iso=emitted_at.isoformat(),
    )
    stmt = (
        pg_insert(BfpClaim)
        .values(
            workspace_id=workspace_id,
            target_id=target_uuid,
            claim_type=CLAIM_TYPE,
            claim_value=claim_value,
            cross_verification_count=0,
            cross_verification_sources=[],
            verified_at_emission=True,
            claim_hash=claim_hash,
            emitted_at=emitted_at,
        )
        .on_conflict_do_nothing(
            index_elements=["target_id", "claim_type", "claim_value"]
        )
    )
    await db.execute(stmt)
    await db.commit()

    return _html(
        "✓ Consentement enregistré. Vous pouvez fermer cet onglet."
    )


@router.get("/consent/{target_id}/status")
async def status(
    target_id: str,
    user=Depends(get_current_user),
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Return the latest consent_sso claim for this target, if any."""
    try:
        target_uuid = uuid.UUID(target_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid target_id")

    result = await db.execute(
        select(BfpClaim)
        .where(
            BfpClaim.workspace_id == workspace_id,
            BfpClaim.target_id == target_uuid,
            BfpClaim.claim_type == CLAIM_TYPE,
        )
        .order_by(BfpClaim.emitted_at.desc())
        .limit(1)
    )
    claim = result.scalar_one_or_none()
    if not claim:
        return {"verified": False, "provider": None, "email": None, "verified_at": None}

    provider, _, email = (claim.claim_value or "").partition(":")
    return {
        "verified": True,
        "provider": provider or None,
        "email": email or None,
        "verified_at": claim.emitted_at.isoformat() if claim.emitted_at else None,
    }

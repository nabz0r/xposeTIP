import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user
from api.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from api.database import get_db
from api.models.user import User, UserWorkspace
from api.models.workspace import Workspace

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    existing_user = existing.scalar_one_or_none()

    if existing_user:
        if existing_user.last_login is not None:
            # Real user who has logged in before — cannot re-register
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered. Try logging in.",
            )
        else:
            # Invited user who never logged in — let them set their own password
            existing_user.password_hash = hash_password(body.password)
            if body.display_name:
                existing_user.display_name = body.display_name
            await db.commit()

            # Get their workspace membership
            result = await db.execute(
                select(UserWorkspace).where(UserWorkspace.user_id == existing_user.id).limit(1)
            )
            membership = result.scalar_one_or_none()
            ws_id = membership.workspace_id if membership else None
            role = membership.role if membership else "user"

            return TokenResponse(
                access_token=create_access_token(existing_user.id, ws_id, role),
                refresh_token=create_refresh_token(existing_user.id),
            )

    # First user = superadmin + enterprise workspace, rest = user + free workspace
    user_count = await db.scalar(select(func.count()).select_from(User))
    is_first = not user_count or user_count == 0

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name or body.email.split("@")[0],
    )
    db.add(user)
    await db.flush()

    if is_first:
        role = "superadmin"
        plan = "enterprise"
        ws_name = "Default"
        ws_slug = "default"
    else:
        role = "user"
        plan = "free"
        ws_name = body.display_name or body.email.split("@")[0]
        ws_slug = ws_name.lower().replace(" ", "-")[:50] + f"-{uuid.uuid4().hex[:6]}"

    workspace = Workspace(
        name=ws_name,
        slug=ws_slug,
        owner_id=user.id,
        plan=plan,
    )
    db.add(workspace)
    await db.flush()

    membership = UserWorkspace(user_id=user.id, workspace_id=workspace.id, role=role)
    db.add(membership)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id, workspace.id, role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    # Get first workspace membership
    result = await db.execute(
        select(UserWorkspace).where(UserWorkspace.user_id == user.id).limit(1)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace access")

    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id, membership.workspace_id, membership.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    result = await db.execute(
        select(UserWorkspace).where(UserWorkspace.user_id == user.id).limit(1)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace access")

    return TokenResponse(
        access_token=create_access_token(user.id, membership.workspace_id, membership.role),
        refresh_token=create_refresh_token(user.id),
    )


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class SwitchWorkspaceRequest(BaseModel):
    workspace_id: str


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None


@router.patch("/profile")
async def update_profile(body: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.display_name is not None:
        current_user.display_name = body.display_name
    await db.commit()
    return {"message": "Profile updated", "display_name": current_user.display_name}


@router.post("/password")
async def change_password(body: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.password_hash or not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")
    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.post("/switch-workspace", response_model=TokenResponse)
async def switch_workspace(body: SwitchWorkspaceRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    workspace_id = uuid.UUID(body.workspace_id)
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == workspace_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this workspace")
    return TokenResponse(
        access_token=create_access_token(current_user.id, workspace_id, membership.role),
        refresh_token=create_refresh_token(current_user.id),
    )


@router.get("/me")
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserWorkspace, Workspace)
        .join(Workspace, UserWorkspace.workspace_id == Workspace.id)
        .where(UserWorkspace.user_id == current_user.id)
    )
    workspaces = [
        {"id": str(ws.id), "name": ws.name, "slug": ws.slug, "role": uw.role, "plan": ws.plan}
        for uw, ws in result.all()
    ]
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "workspaces": workspaces,
    }

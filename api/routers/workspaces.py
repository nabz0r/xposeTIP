import logging
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace, require_role
from api.auth.security import hash_password
from api.database import get_db
from api.models.finding import Finding
from api.models.scan import Scan
from api.models.target import Target
from api.models.user import User, UserWorkspace
from api.models.workspace import Workspace
from api.models.workspace_target import WorkspaceTarget

router = APIRouter()
logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug or 'workspace'


class CreateWorkspaceRequest(BaseModel):
    name: str


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    settings: dict | None = None


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "user"


class UpdateRoleRequest(BaseModel):
    role: str


class ShareTargetRequest(BaseModel):
    target_id: str
    role: str = "viewer"  # viewer|editor


# ---- Workspace CRUD ----

@router.get("")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserWorkspace, Workspace)
        .join(Workspace, UserWorkspace.workspace_id == Workspace.id)
        .where(UserWorkspace.user_id == current_user.id)
    )
    workspaces = []
    for uw, ws in result.all():
        # Get counts
        member_count = await db.scalar(
            select(func.count()).select_from(UserWorkspace).where(UserWorkspace.workspace_id == ws.id)
        ) or 0
        target_count = await db.scalar(
            select(func.count()).select_from(Target).where(Target.workspace_id == ws.id)
        ) or 0
        workspaces.append({
            "id": str(ws.id),
            "name": ws.name,
            "slug": ws.slug,
            "role": uw.role,
            "plan": ws.plan,
            "member_count": member_count,
            "target_count": target_count,
            "created_at": ws.created_at.isoformat() if ws.created_at else None,
        })
    return workspaces


@router.post("")
async def create_workspace(
    body: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    role: str = Depends(require_role("superadmin", "admin", "consultant")),
    db: AsyncSession = Depends(get_db),
):
    slug = _slugify(body.name)
    # Ensure unique slug
    existing = await db.execute(select(Workspace).where(Workspace.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    workspace = Workspace(name=body.name, slug=slug, owner_id=current_user.id)
    db.add(workspace)
    await db.flush()

    # Inherit the role from current workspace (superadmin stays superadmin)
    membership = UserWorkspace(user_id=current_user.id, workspace_id=workspace.id, role=role)
    db.add(membership)
    await db.commit()

    return {
        "id": str(workspace.id),
        "name": workspace.name,
        "slug": workspace.slug,
        "plan": workspace.plan,
    }


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    # Check membership with admin+ role
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Must be admin of this workspace")

    workspace = await db.execute(select(Workspace).where(Workspace.id == ws_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if body.name is not None:
        ws.name = body.name
    if body.settings is not None:
        ws.settings = body.settings
    await db.commit()

    return {"id": str(ws.id), "name": ws.name, "slug": ws.slug, "plan": ws.plan}


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    role: str = Depends(require_role("superadmin")),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    workspace = await db.execute(select(Workspace).where(Workspace.id == ws_id))
    ws = workspace.scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    await db.delete(ws)
    await db.commit()
    return {"deleted": True}


# ---- Members ----

@router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    # Verify caller is a member
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    result = await db.execute(
        select(UserWorkspace, User)
        .join(User, UserWorkspace.user_id == User.id)
        .where(UserWorkspace.workspace_id == ws_id)
    )
    members = []
    for uw, u in result.all():
        members.append({
            "user_id": str(u.id),
            "email": u.email,
            "display_name": u.display_name,
            "role": uw.role,
            "joined_at": uw.joined_at.isoformat() if uw.joined_at else None,
        })
    return members


@router.post("/{workspace_id}/invite")
async def invite_member(
    workspace_id: str,
    body: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    # Check caller is admin
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Must be admin to invite members")

    valid_roles = {"superadmin", "admin", "consultant", "client", "user"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    # Find or create user
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        import secrets
        temp_password = secrets.token_urlsafe(16)
        user = User(
            email=body.email,
            password_hash=hash_password(temp_password),
            display_name=body.email.split("@")[0],
        )
        db.add(user)
        await db.flush()

    # Check not already a member
    existing = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already a member of this workspace")

    uw = UserWorkspace(user_id=user.id, workspace_id=ws_id, role=body.role)
    db.add(uw)
    await db.commit()

    return {"invited": True, "user_id": str(user.id), "email": body.email, "role": body.role}


@router.patch("/{workspace_id}/members/{user_id}")
async def update_member_role(
    workspace_id: str,
    user_id: str,
    body: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    target_uid = uuid.UUID(user_id)

    # Check caller is admin
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Must be admin to change roles")

    # Update target user's role
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == target_uid,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    target_membership = result.scalar_one_or_none()
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")

    target_membership.role = body.role
    await db.commit()

    return {"user_id": user_id, "role": body.role}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    target_uid = uuid.UUID(user_id)

    # Check caller is admin
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Must be admin to remove members")

    # Don't allow removing yourself
    if target_uid == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == target_uid,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    target_membership = result.scalar_one_or_none()
    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(target_membership)
    await db.commit()

    return {"removed": True}


# ---- Shared Targets ----

@router.get("/{workspace_id}/targets")
async def list_shared_targets(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    # Verify caller is a member
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    # Get shared targets (via workspace_targets) + owned targets
    owned = await db.execute(select(Target).where(Target.workspace_id == ws_id))
    owned_targets = owned.scalars().all()

    shared = await db.execute(
        select(WorkspaceTarget, Target)
        .join(Target, WorkspaceTarget.target_id == Target.id)
        .where(WorkspaceTarget.workspace_id == ws_id)
    )
    shared_items = []
    for wt, t in shared.all():
        shared_items.append({
            "id": str(t.id),
            "email": t.email,
            "display_name": t.display_name,
            "exposure_score": t.exposure_score,
            "status": t.status,
            "shared": True,
            "role": wt.role,
            "home_workspace_id": str(t.workspace_id),
        })

    owned_items = [{
        "id": str(t.id),
        "email": t.email,
        "display_name": t.display_name,
        "exposure_score": t.exposure_score,
        "status": t.status,
        "shared": False,
        "role": "owner",
    } for t in owned_targets]

    return {"owned": owned_items, "shared": shared_items}


@router.post("/{workspace_id}/targets")
async def share_target(
    workspace_id: str,
    body: ShareTargetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    target_id = uuid.UUID(body.target_id)

    # Check caller is admin of destination workspace
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin", "consultant"):
        raise HTTPException(status_code=403, detail="Must be admin or consultant to share targets")

    # Check target exists
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Check not already shared
    existing = await db.execute(
        select(WorkspaceTarget).where(
            WorkspaceTarget.workspace_id == ws_id,
            WorkspaceTarget.target_id == target_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Target already shared to this workspace")

    wt = WorkspaceTarget(
        workspace_id=ws_id,
        target_id=target_id,
        added_by=current_user.id,
        role=body.role,
    )
    db.add(wt)
    await db.commit()

    return {"shared": True, "target_id": str(target_id), "workspace_id": str(ws_id)}


@router.delete("/{workspace_id}/targets/{target_id}")
async def unshare_target(
    workspace_id: str,
    target_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_id = uuid.UUID(workspace_id)
    tid = uuid.UUID(target_id)

    # Check caller is admin
    result = await db.execute(
        select(UserWorkspace).where(
            UserWorkspace.user_id == current_user.id,
            UserWorkspace.workspace_id == ws_id,
        )
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in ("superadmin", "admin", "consultant"):
        raise HTTPException(status_code=403, detail="Must be admin or consultant")

    result = await db.execute(
        select(WorkspaceTarget).where(
            WorkspaceTarget.workspace_id == ws_id,
            WorkspaceTarget.target_id == tid,
        )
    )
    wt = result.scalar_one_or_none()
    if not wt:
        raise HTTPException(status_code=404, detail="Shared target not found")

    await db.delete(wt)
    await db.commit()

    return {"unshared": True}

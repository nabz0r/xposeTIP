import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.dependencies import get_current_user, get_current_workspace
from api.database import get_db
from api.models.identity import Identity, IdentityLink
from api.models.target import Target
from api.models.user import User

router = APIRouter()


@router.get("/{target_id}")
async def get_graph(
    target_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify target belongs to workspace
    result = await db.execute(
        select(Target).where(Target.id == target_id, Target.workspace_id == workspace_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    # Fetch nodes
    result = await db.execute(
        select(Identity).where(
            Identity.workspace_id == workspace_id,
            Identity.target_id == target_id,
        )
    )
    identities = result.scalars().all()

    identity_ids = {i.id for i in identities}

    # Fetch edges
    result = await db.execute(
        select(IdentityLink).where(
            IdentityLink.workspace_id == workspace_id,
            IdentityLink.source_id.in_(identity_ids) | IdentityLink.dest_id.in_(identity_ids),
        )
    )
    links = result.scalars().all()

    nodes = [
        {
            "id": str(i.id),
            "type": i.type,
            "value": i.value,
            "platform": i.platform,
            "source_module": i.source_module,
            "confidence": i.confidence,
            "metadata": i.metadata_ or {},
        }
        for i in identities
    ]

    edges = [
        {
            "source": str(l.source_id),
            "dest": str(l.dest_id),
            "type": l.link_type,
            "confidence": l.confidence,
            "source_module": l.source_module,
        }
        for l in links
    ]

    # Count unique clusters (connected components approximation)
    clusters = len(set(n["type"] for n in nodes)) if nodes else 0

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "clusters": clusters,
        },
    }

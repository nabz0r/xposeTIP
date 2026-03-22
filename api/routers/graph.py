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

    # Build transition probability map for edge weighting
    from collections import defaultdict
    outgoing = defaultdict(list)
    for l in links:
        outgoing[l.source_id].append((l.dest_id, l.confidence or 0.5))
    transition_map = {}
    for src_id, dests in outgoing.items():
        total = sum(w for _, w in dests)
        if total > 0:
            for dest_id, w in dests:
                transition_map[(str(src_id), str(dest_id))] = round(w / total, 4)

    edges = [
        {
            "source": str(l.source_id),
            "dest": str(l.dest_id),
            "type": l.link_type,
            "confidence": l.confidence,
            "source_module": l.source_module,
            "transition_probability": transition_map.get((str(l.source_id), str(l.dest_id)), 0),
        }
        for l in links
    ]

    # Build graph clusters via BFS
    id_set = {i.id for i in identities}
    adj = defaultdict(set)
    for l in links:
        if l.source_id in id_set and l.dest_id in id_set:
            adj[l.source_id].add(l.dest_id)
            adj[l.dest_id].add(l.source_id)

    visited = set()
    graph_clusters = []
    cluster_idx = 0
    node_cluster_map = {}

    for start_id in id_set:
        if start_id in visited:
            continue
        component = set()
        queue = [start_id]
        while queue:
            n = queue.pop(0)
            if n in visited:
                continue
            visited.add(n)
            component.add(n)
            for neighbor in adj.get(n, []):
                if neighbor not in visited and neighbor in id_set:
                    queue.append(neighbor)

        if len(component) >= 2:
            for n in component:
                node_cluster_map[str(n)] = cluster_idx
            avg_conf = sum((i.confidence or 0) for i in identities if i.id in component) / len(component)
            graph_clusters.append({
                "id": cluster_idx,
                "node_count": len(component),
                "confidence": round(avg_conf, 4),
            })
            cluster_idx += 1

    # Annotate nodes with cluster_id
    for n in nodes:
        n["cluster_id"] = node_cluster_map.get(n["id"])

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "clusters": len(graph_clusters),
        },
        "graph_clusters": graph_clusters,
    }

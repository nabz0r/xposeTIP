"""PageRank-inspired confidence propagation across the identity graph.

Propagates confidence from the seed email node through edges, weighted by
source reliability. High-connectivity nodes with multiple independent paths
accumulate more confidence.
"""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.identity import Identity, IdentityLink

logger = logging.getLogger(__name__)

DAMPING = 0.85
ITERATIONS = 20
MIN_DELTA = 0.001  # Convergence threshold


def propagate_confidence(target_id, workspace_id, session: Session) -> dict:
    """Run PageRank-style confidence propagation on the identity graph.

    Returns dict: {identity_id: propagated_confidence}
    """
    # Load graph
    identities = session.execute(
        select(Identity).where(
            Identity.target_id == target_id,
            Identity.workspace_id == workspace_id,
        )
    ).scalars().all()

    links = session.execute(
        select(IdentityLink).where(
            IdentityLink.workspace_id == workspace_id,
        )
    ).scalars().all()

    if not identities:
        return {}

    # Build adjacency structure
    id_map = {i.id: i for i in identities}
    id_set = set(id_map.keys())

    # Filter links to only those connecting our target's nodes
    relevant_links = [l for l in links if l.source_id in id_set and l.dest_id in id_set]

    # Outgoing edges per node: node_id -> [(dest_id, weight)]
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for l in relevant_links:
        weight = l.confidence or 0.5
        outgoing[l.source_id].append((l.dest_id, weight))
        incoming[l.dest_id].append((l.source_id, weight))

    # Initialize scores
    n = len(identities)
    if n == 0:
        return {}

    # Find seed node (email type = highest initial confidence)
    scores = {}
    for i in identities:
        if i.type == "email":
            scores[i.id] = 1.0  # Email is the anchor
        else:
            scores[i.id] = i.confidence or 0.5

    # PageRank iterations
    iteration = 0
    for iteration in range(ITERATIONS):
        new_scores = {}
        max_delta = 0.0

        for node_id in id_set:
            # Base score (1 - damping) spread equally + damping * incoming weighted sum
            incoming_sum = 0.0
            for src_id, weight in incoming.get(node_id, []):
                src_out_count = len(outgoing.get(src_id, []))
                if src_out_count > 0:
                    # Source distributes its confidence across its outgoing edges
                    # weighted by edge confidence
                    total_out_weight = sum(w for _, w in outgoing[src_id])
                    if total_out_weight > 0:
                        incoming_sum += scores.get(src_id, 0) * (weight / total_out_weight)

            new_score = (1.0 - DAMPING) / n + DAMPING * incoming_sum

            # Clamp to [0, 1]
            new_score = min(1.0, max(0.0, new_score))

            delta = abs(new_score - scores.get(node_id, 0))
            max_delta = max(max_delta, delta)
            new_scores[node_id] = new_score

        scores = new_scores

        # Check convergence
        if max_delta < MIN_DELTA:
            logger.debug("PageRank converged after %d iterations (delta=%.4f)", iteration + 1, max_delta)
            break

    # Normalize: scale so max = 1.0
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: round(v / max_score, 4) for k, v in scores.items()}

    # Update identity nodes in DB with propagated confidence
    for identity in identities:
        if identity.id in scores:
            identity.confidence = scores[identity.id]

    session.commit()

    logger.info(
        "Confidence propagated for target %s: %d nodes, %d edges, %d iterations",
        target_id, len(identities), len(relevant_links), min(iteration + 1, ITERATIONS),
    )

    return scores

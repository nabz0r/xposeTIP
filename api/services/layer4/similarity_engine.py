"""Similarity engine — compute and persist pairwise behavioral + name similarity
between workspace targets.

Post-S146: the stored `similarity` column is the COMBINED score
(cosine × name_similarity when names are available, else raw cosine). The
0.70 storage threshold gates on this combined score.

Both directions (A->B and B->A) stored as separate rows in target_similarities.
axis_diffs is computed from target_a perspective (axes_a - axes_b); signs are
reversed in the reverse-direction row.

`first_detected` is preserved across recomputes: a pair already known keeps its
original timestamp; a newly-detected pair gets now().
"""
from __future__ import annotations

import logging
import math
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.models.target import Target
from api.models.target_similarity import TargetSimilarity

# Common particles / connectors filtered out of name token sets to avoid them
# dominating Jaccard scores. Lowercase, post-normalization.
_NAME_PARTICLES: set[str] = {
    "de", "la", "le", "du", "des", "del", "della", "der", "den", "van",
    "von", "el", "al", "bin", "ben", "ibn", "and", "et", "of", "the",
}


def _build_name_string(target: Target) -> str:
    """Return the best available name string for `target`. Priority:
    1. user_first_name + user_last_name (most reliable when set by the pipeline)
    2. display_name (auto-extracted by scrapers; may be a username, accept anyway)
    3. email local-part with `. _ -` tokenized (catches firstname.lastname
       corporate convention even when name resolution didn't run).
    Returns "" when nothing usable is available.
    """
    fn = (target.user_first_name or "").strip()
    ln = (target.user_last_name or "").strip()
    if fn or ln:
        combined = f"{fn} {ln}".strip()
        if len(combined) >= 2:
            return combined
    if target.display_name and len(target.display_name.strip()) >= 2:
        return target.display_name.strip()
    if target.email:
        local = target.email.split("@", 1)[0]
        local = local.replace(".", " ").replace("_", " ").replace("-", " ")
        if len(local.strip()) >= 2:
            return local
    return ""


def _normalize_name_tokens(s: str) -> set[str]:
    """Normalize a name string and return the set of meaningful tokens.

    NFD strips accents (Sébastien → Sebastien), lowercases, removes
    non-alphanumeric, drops single letters (initials) and common particles.
    """
    if not s:
        return set()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = "".join(c if c.isalnum() else " " for c in s)
    return {
        t for t in s.split()
        if len(t) >= 2 and t not in _NAME_PARTICLES
    }


def _name_similarity(target_a: Target, target_b: Target) -> float | None:
    """Compute name match score in [0.0, 1.0] via token-set Jaccard.

    Returns None when comparison is not meaningful — at least one target has
    no resolvable name string, or normalization yields zero tokens on either
    side. Callers SHOULD treat None as "do not multiply" (use raw cosine).
    """
    name_a = _build_name_string(target_a)
    name_b = _build_name_string(target_b)
    if not name_a or not name_b:
        return None
    tokens_a = _normalize_name_tokens(name_a)
    tokens_b = _normalize_name_tokens(name_b)
    if not tokens_a or not tokens_b:
        return None
    union = tokens_a | tokens_b
    if not union:
        return None
    return round(len(tokens_a & tokens_b) / len(union), 4)

logger = logging.getLogger(__name__)

# 11 normalized axes (0..1) produced by FingerprintEngine._normalize()
FINGERPRINT_AXES: list[str] = [
    "accounts",
    "platforms",
    "username_reuse",
    "breaches",
    "geo_spread",
    "data_leaked",
    "email_age",
    "security",
    "public_exposure",
    "formal_records",
    "network_signature",
]

# Pairs below this threshold are NOT persisted (storage hygiene)
STORAGE_THRESHOLD = 0.7


def _extract_axes(target: Target) -> list[float] | None:
    """Pull the 9-axis vector from a target's stored fingerprint.

    Returns None when the target hasn't been scanned, fingerprint is malformed,
    or the vector is all-zero (failed scan).
    """
    fp = (target.profile_data or {}).get("fingerprint")
    if not fp:
        return None
    axes = fp.get("axes")
    if not isinstance(axes, dict):
        return None
    vector = [float(axes.get(k, 0) or 0) for k in FINGERPRINT_AXES]
    if all(v == 0 for v in vector):
        return None
    return vector


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length non-zero vectors. Returns 0..1."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(dot / (norm_a * norm_b), 4)


def _axis_diffs(a: list[float], b: list[float]) -> dict[str, float]:
    """Per-axis signed delta (a - b)."""
    return {axis: round(a[i] - b[i], 3) for i, axis in enumerate(FINGERPRINT_AXES)}


def _reversed_diffs(diffs: dict[str, float]) -> dict[str, float]:
    """Sign-flip every axis (for the reverse-direction row)."""
    return {k: round(-v, 3) for k, v in diffs.items()}


def recompute_for_target(
    session: Session,
    target_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> dict[str, Any]:
    """Recompute and persist similarity pairs for `target_id` against every
    other workspace target with a fingerprint.

    1. SELECT existing rows touching target_id (both directions) to harvest
       `first_detected` timestamps per (unordered) pair.
    2. DELETE existing rows touching target_id (both directions).
    3. Compute fresh similarities; INSERT pairs >= STORAGE_THRESHOLD in both
       directions, carrying forward the earliest `first_detected` per pair.

    Returns a small stats dict. Caller handles rollback on exception.
    """
    # Load source target
    source = session.execute(
        select(Target).where(
            Target.id == target_id,
            Target.workspace_id == workspace_id,
        )
    ).scalar_one_or_none()

    if source is None:
        logger.warning("similarity.recompute: target %s not found", target_id)
        return {"matches": 0, "skipped": "target_not_found"}

    source_vec = _extract_axes(source)
    if source_vec is None:
        # Wipe any stale rows for this target (its fingerprint is gone/zero now)
        session.execute(
            delete(TargetSimilarity).where(
                (TargetSimilarity.target_a_id == target_id)
                | (TargetSimilarity.target_b_id == target_id)
            )
        )
        session.commit()
        return {"matches": 0, "skipped": "no_fingerprint"}

    # 1. Harvest existing first_detected per (a,b) — both directions
    existing_rows = session.execute(
        select(TargetSimilarity).where(
            (TargetSimilarity.target_a_id == target_id)
            | (TargetSimilarity.target_b_id == target_id)
        )
    ).scalars().all()

    first_detected_map: dict[tuple[str, str], datetime] = {}
    for row in existing_rows:
        key = tuple(sorted([str(row.target_a_id), str(row.target_b_id)]))
        existing_fd = first_detected_map.get(key)
        if existing_fd is None or row.first_detected < existing_fd:
            first_detected_map[key] = row.first_detected

    # 2. DELETE all rows touching target_id
    session.execute(
        delete(TargetSimilarity).where(
            (TargetSimilarity.target_a_id == target_id)
            | (TargetSimilarity.target_b_id == target_id)
        )
    )

    # 3. Compute fresh similarities against all other workspace targets
    candidates = session.execute(
        select(Target).where(
            Target.workspace_id == workspace_id,
            Target.id != target_id,
        )
    ).scalars().all()

    now = datetime.now(timezone.utc)
    matches = 0

    for cand in candidates:
        cand_vec = _extract_axes(cand)
        if cand_vec is None:
            continue
        cosine_sim = _cosine(source_vec, cand_vec)
        name_sim = _name_similarity(source, cand)        # may be None
        if name_sim is not None:
            combined = round(cosine_sim * name_sim, 4)
        else:
            combined = cosine_sim                         # no name signal — defer to cosine

        if combined < STORAGE_THRESHOLD:
            continue

        diffs_a = _axis_diffs(source_vec, cand_vec)
        diffs_b = _reversed_diffs(diffs_a)
        pair_key = tuple(sorted([str(target_id), str(cand.id)]))
        fd = first_detected_map.get(pair_key, now)

        # A->B row
        session.add(TargetSimilarity(
            workspace_id=workspace_id,
            target_a_id=target_id,
            target_b_id=cand.id,
            similarity=combined,
            cosine_similarity=cosine_sim,
            name_similarity=name_sim,
            axis_diffs=diffs_a,
            first_detected=fd,
            last_computed=now,
        ))
        # B->A row (mirror — reversed diffs, same similarity, same first_detected)
        session.add(TargetSimilarity(
            workspace_id=workspace_id,
            target_a_id=cand.id,
            target_b_id=target_id,
            similarity=combined,
            cosine_similarity=cosine_sim,
            name_similarity=name_sim,
            axis_diffs=diffs_b,
            first_detected=fd,
            last_computed=now,
        ))
        matches += 1

    session.commit()

    # Invalidate Redis cache for this workspace's similarity reads (best-effort)
    try:
        from api.services.cache import cache
        cache.invalidate_pattern(f"similarity:v1:{workspace_id}:*")
    except Exception:
        logger.warning("similarity.recompute: cache invalidation failed (non-fatal)")

    logger.info("similarity.recompute: target %s -> %d matches", target_id, matches)
    return {"matches": matches, "skipped": None}

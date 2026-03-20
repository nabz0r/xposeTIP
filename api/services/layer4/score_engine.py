import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.target import Target

logger = logging.getLogger(__name__)

SCORE_WEIGHTS = {
    "breach": 0.25,
    "social_account": 0.20,
    "tracking": 0.15,
    "geolocation": 0.12,
    "data_broker": 0.10,
    "metadata": 0.08,
    "domain_registration": 0.05,
    "paste": 0.05,
}

SEVERITY_MULTIPLIER = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
}

# Max raw score per finding before normalization
MAX_FINDINGS_PER_CATEGORY = 20


def compute_score(target_id, session: Session) -> tuple[int, dict]:
    """Compute exposure score 0-100 and category breakdown for a target."""
    findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.status == "active",
        )
    ).scalars().all()

    # Group by category
    category_scores = defaultdict(float)
    category_counts = defaultdict(int)

    for f in findings:
        cat = f.category
        mult = SEVERITY_MULTIPLIER.get(f.severity, 1)
        category_scores[cat] += mult
        category_counts[cat] += 1

    # Normalize each category to 0-100
    breakdown = {}
    for cat, raw in category_scores.items():
        # Normalize: cap at MAX_FINDINGS * highest multiplier, then scale to 100
        max_raw = MAX_FINDINGS_PER_CATEGORY * SEVERITY_MULTIPLIER["critical"]
        normalized = min(100, int((raw / max_raw) * 100))
        breakdown[cat] = normalized

    # Weighted total
    total = 0.0
    for cat, weight in SCORE_WEIGHTS.items():
        total += breakdown.get(cat, 0) * weight

    # Also add any categories not in weights at a small default weight
    known_cats = set(SCORE_WEIGHTS.keys())
    for cat, score in breakdown.items():
        if cat not in known_cats:
            total += score * 0.03

    final_score = min(100, max(0, int(total)))

    # Update target
    target = session.execute(
        select(Target).where(Target.id == target_id)
    ).scalar_one_or_none()

    if target:
        target.exposure_score = final_score
        target.score_breakdown = breakdown
        session.commit()

    logger.info(
        "Score computed for target %s: %d (breakdown: %s)",
        target_id, final_score, breakdown,
    )

    return final_score, breakdown

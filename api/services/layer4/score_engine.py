"""Exposure score engine v2.

Computes a 0-100 exposure score for a target based on findings,
weighted by confidence and source reliability.
"""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.target import Target
from api.services.layer4.source_scoring import get_source_reliability

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

# Bonus/penalty score factors applied to the final score
SCORE_FACTORS = {
    "breach_with_passwords": 15,    # Critical: passwords were leaked
    "credentials_leaked": 10,        # High: creds confirmed leaked
    "email_security_weak": 5,        # Medium: SPF/DMARC issues
    "multiple_username_matches": 3,  # Low: username reuse across platforms
    "account_proliferation": 2,      # Per account beyond 5
    "cross_verified": -2,            # Bonus: verified data is more actionable (lower is better managed)
}

# Max raw score per category before normalization
MAX_FINDINGS_PER_CATEGORY = 20


def _compute_bonus_factors(findings: list) -> int:
    """Compute bonus/penalty points from special conditions."""
    bonus = 0

    breach_findings = [f for f in findings if f.category == "breach"]
    social_findings = [f for f in findings if f.category == "social_account"]

    # Check for breaches with passwords
    for f in breach_findings:
        data = f.data or {}
        data_classes = data.get("DataClasses", data.get("data_classes", []))
        if any("password" in dc.lower() for dc in data_classes):
            bonus += SCORE_FACTORS["breach_with_passwords"]
            break  # Only count once

    # Check for credentials leaked
    for f in findings:
        data = f.data or {}
        if data.get("credentials_leaked") or data.get("has_password"):
            bonus += SCORE_FACTORS["credentials_leaked"]
            break

    # Check for weak email security (missing SPF/DMARC)
    for f in findings:
        if f.module == "dns_deep":
            data = f.data or {}
            if data.get("security_score") is not None and data["security_score"] < 2:
                bonus += SCORE_FACTORS["email_security_weak"]
                break

    # Username reuse across platforms (more than 3 username_hunter findings)
    username_findings = [f for f in findings if f.module in ("username_hunter", "sherlock")]
    if len(username_findings) > 3:
        bonus += SCORE_FACTORS["multiple_username_matches"]

    # Account proliferation (more than 5 social accounts)
    if len(social_findings) > 5:
        extra = len(social_findings) - 5
        bonus += min(extra * SCORE_FACTORS["account_proliferation"], 10)

    return bonus


def compute_score(target_id, session: Session) -> tuple[int, dict]:
    """Compute exposure score 0-100 and category breakdown for a target.

    v2: Each finding weighted by confidence * source_reliability.
    """
    # Deduplicate: keep latest finding per (module, title) — Python-side
    all_findings = session.execute(
        select(Finding).where(
            Finding.target_id == target_id,
            Finding.status == "active",
        )
    ).scalars().all()
    seen = {}
    for f in all_findings:
        key = (f.module, f.title)
        existing = seen.get(key)
        if existing is None or (f.created_at and (not existing.created_at or f.created_at > existing.created_at)):
            seen[key] = f
    findings = list(seen.values())

    # Group by category
    category_scores = defaultdict(float)
    category_counts = defaultdict(int)

    for f in findings:
        cat = f.category
        sev_mult = SEVERITY_MULTIPLIER.get(f.severity, 1)
        confidence = f.confidence if f.confidence is not None else 1.0
        source_rel = get_source_reliability(f.module)

        # v2: effective score = severity * confidence * source_reliability
        effective = sev_mult * confidence * source_rel
        category_scores[cat] += effective
        category_counts[cat] += 1

    # Normalize each category to 0-100
    breakdown = {}
    for cat, raw in category_scores.items():
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

    # Apply bonus factors
    bonus = _compute_bonus_factors(findings)
    total += bonus

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
        "Score computed for target %s: %d (bonus=%d, breakdown=%s)",
        target_id, final_score, bonus, breakdown,
    )

    return final_score, breakdown

"""Pass 2 — Public Exposure Enricher.

After Pass 1 resolves a primary_name, this service runs name-based scrapers
(GDELT news, etc.) to find media mentions, press coverage, and public exposure.

Only runs if primary_name looks like a real human name (not a username).
"""
import logging
import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.target import Target

logger = logging.getLogger(__name__)

# Common first names — if the first part matches, it's likely a real name
COMMON_FIRST_NAMES = {
    "james", "john", "robert", "michael", "david", "william", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "mark", "donald", "steven", "paul", "andrew", "joshua",
    "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth",
    "susan", "jessica", "sarah", "karen", "lisa", "nancy", "betty",
    "margaret", "sandra", "ashley", "dorothy", "kimberly", "emily",
    "donna", "michelle", "carol", "amanda", "melissa", "deborah",
    # French
    "jean", "pierre", "nicolas", "benjamin", "mickael", "laurent",
    "philippe", "stephane", "christophe", "nathalie", "sophie", "marie",
    "isabelle", "catherine", "valerie", "sylvie", "sandrine", "caroline",
    # German
    "hans", "klaus", "peter", "stefan", "andreas", "thomas", "markus",
    "martin", "steffen", "matthias", "sabine", "petra", "monika",
    # Spanish
    "carlos", "miguel", "jose", "antonio", "francisco", "pedro",
    "pablo", "luis", "jorge", "maria", "carmen", "rosa",
}

# Max scrapers per pass 2
MAX_PASS2_SCRAPERS = 3
PASS2_SLEEP = 1.0  # seconds between scraper calls


def _is_real_name(name: str) -> bool:
    """Check if a name looks like a real human name (not a username).

    Rejects:
    - Single words (usernames)
    - Contains underscores or dots (username patterns)
    - All lowercase single word
    - Less than 4 characters
    """
    if not name or len(name.strip()) < 4:
        return False

    name = name.strip()

    # Must contain a space (first + last)
    if " " not in name:
        return False

    # No underscores (username pattern)
    if "_" in name:
        return False

    parts = name.split()
    if len(parts) < 2:
        return False

    # Each part should be >= 2 chars
    if any(len(p) < 2 for p in parts):
        return False

    # First part should start with uppercase (or be a known name)
    first = parts[0]
    if not first[0].isupper() and first.lower() not in COMMON_FIRST_NAMES:
        return False

    return True


def compute_name_match_confidence(article_text: str, target_name: str) -> float:
    """Compute how likely an article mention matches our target.

    Returns 0.0-1.0 confidence score.
    """
    if not article_text or not target_name:
        return 0.0

    text_lower = article_text.lower()
    name_lower = target_name.lower()
    parts = target_name.split()

    # Exact full name match
    if name_lower in text_lower:
        return 0.95

    # All parts present (possibly in different order)
    all_parts_found = all(p.lower() in text_lower for p in parts)
    if all_parts_found:
        return 0.80

    # Last name + first initial
    if len(parts) >= 2:
        last = parts[-1].lower()
        first_initial = parts[0][0].lower()
        if last in text_lower and f"{first_initial}." in text_lower:
            return 0.65

    # Only last name (common, lower confidence)
    if len(parts) >= 2 and parts[-1].lower() in text_lower:
        return 0.40

    return 0.0


def enrich_public_exposure(target_id, session: Session) -> dict:
    """Pass 2 enrichment: run name-based scrapers after primary_name is resolved.

    Returns: {
        "scrapers_run": 2,
        "findings_created": 5,
        "skipped_reason": None,
    }
    """
    result = {"scrapers_run": 0, "findings_created": 0, "skipped_reason": None}

    target = session.execute(
        select(Target).where(Target.id == target_id)
    ).scalar_one_or_none()

    if not target:
        result["skipped_reason"] = "target_not_found"
        return result

    profile = target.profile_data or {}
    primary_name = profile.get("primary_name")

    if not primary_name:
        result["skipped_reason"] = "no_primary_name"
        logger.debug("PASS2: Skipping %s — no primary_name", target_id)
        return result

    if not _is_real_name(primary_name):
        result["skipped_reason"] = "username_like_name"
        logger.debug("PASS2: Skipping %s — name '%s' looks like username", target_id, primary_name)
        return result

    logger.info("PASS2: Running public exposure enrichment for '%s' (target %s)", primary_name, target_id)

    # Find public_exposure scrapers
    try:
        from api.models.scraper import Scraper
        scrapers = session.execute(
            select(Scraper).where(
                Scraper.category == "public_exposure",
                Scraper.enabled == True,
            )
        ).scalars().all()
    except Exception:
        logger.exception("PASS2: Failed to load public_exposure scrapers")
        result["skipped_reason"] = "scraper_load_error"
        return result

    if not scrapers:
        result["skipped_reason"] = "no_public_exposure_scrapers"
        return result

    # Run up to MAX_PASS2_SCRAPERS
    from api.services.scraper_engine import run_scraper

    scrapers_to_run = scrapers[:MAX_PASS2_SCRAPERS]

    for scraper in scrapers_to_run:
        try:
            # Build input based on scraper input_type
            if scraper.input_type == "name":
                input_value = primary_name
            elif scraper.input_type == "name_quoted":
                input_value = f'"{primary_name}"'
            else:
                logger.debug("PASS2: Skipping scraper %s — unsupported input_type %s",
                             scraper.name, scraper.input_type)
                continue

            logger.info("PASS2: Running scraper '%s' with name '%s'", scraper.name, input_value)

            findings_data = run_scraper(
                scraper=scraper,
                input_value=input_value,
                target=target,
                session=session,
            )

            if findings_data:
                created = 0
                for fd in findings_data:
                    # Compute match confidence
                    text = fd.get("description", "") or fd.get("title", "")
                    confidence = compute_name_match_confidence(text, primary_name)

                    if confidence < 0.60:
                        logger.debug("PASS2: Skipping low-confidence match (%.2f): %s",
                                     confidence, fd.get("title", "")[:80])
                        continue

                    # Create finding
                    finding = Finding(
                        workspace_id=target.workspace_id,
                        scan_id=None,  # Pass 2 findings are not tied to a specific scan
                        target_id=target_id,
                        module="scraper_engine",
                        layer=4,
                        category="public_exposure",
                        severity=fd.get("severity", "info"),
                        title=fd.get("title", f"Media mention: {primary_name}"),
                        description=fd.get("description"),
                        data=fd.get("data", {}),
                        url=fd.get("url"),
                        indicator_value=fd.get("url") or fd.get("title", ""),
                        indicator_type="media_mention",
                        verified=False,
                        confidence=round(confidence, 3),
                    )
                    session.add(finding)
                    created += 1

                if created > 0:
                    session.commit()
                    result["findings_created"] += created
                    logger.info("PASS2: Scraper '%s' created %d findings", scraper.name, created)

            result["scrapers_run"] += 1

            # Sleep between scraper calls
            if scraper != scrapers_to_run[-1]:
                time.sleep(PASS2_SLEEP)

        except Exception:
            logger.exception("PASS2: Scraper '%s' failed", scraper.name)
            continue

    logger.info(
        "PASS2: Completed for target %s — %d scrapers, %d findings",
        target_id, result["scrapers_run"], result["findings_created"],
    )
    return result

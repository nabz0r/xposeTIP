import asyncio
import logging
import re

from api.services.base import BaseScanner, ScanResult
from api.services.scraper_engine import ScraperEngine
from api.services.layer4.username_validator import is_valid_username

logger = logging.getLogger(__name__)


class ScraperScanner(BaseScanner):
    """
    Meta-scanner that executes all enabled scraper definitions from DB.
    Replaces individual scanner files for simple scraping tasks.
    """

    MODULE_ID = "scraper_engine"
    LAYER = 1
    CATEGORY = "social"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        # Import here to avoid circular deps
        from api.tasks.utils import get_sync_session
        from api.models.scraper import Scraper
        from sqlalchemy import select

        session = get_sync_session()
        try:
            scrapers = session.execute(
                select(Scraper).where(
                    Scraper.enabled == True,
                    Scraper.input_type.in_(["email", "username", "domain", "first_name", "phone", "crypto_wallet"]),
                )
            ).scalars().all()

            if not scrapers:
                return results

            engine = ScraperEngine()
            _email_lhs = email.split("@")[0]
            # S129: gate username dispatch with is_valid_username to match Pass 1.5's
            # validation — don't waste requests on strict-schema platforms (HN, Reddit,
            # GitHub, etc.) for email LHSs that aren't plausibly a single handle.
            username = _email_lhs if is_valid_username(_email_lhs) else None
            domain = email.split("@")[-1] if "@" in email else email
            cleaned_prefix = re.sub(r"\d+", "", _email_lhs)
            name_parts = re.split(r"[._]", cleaned_prefix)
            first_name = name_parts[0].lower() if name_parts else _email_lhs
            # Get secondary identifiers from profile_data (populated by A1.5)
            _phones = []
            _wallets = []
            try:
                from api.models.target import Target
                _tgt = session.execute(select(Target).where(Target.email == email)).scalars().first()
                if _tgt and _tgt.profile_data:
                    _phones = _tgt.profile_data.get("phones", [])
                    _wallets = _tgt.profile_data.get("crypto_wallets", [])
            except Exception:
                pass

            inputs = {
                "email": email,
                "username": username,
                "domain": domain,
                "first_name": first_name,
                "phone": _phones[0] if _phones else None,
                "crypto_wallet": _wallets[0]["address"] if _wallets else None,
            }

            # Write scraper progress to Redis
            scan_id = kwargs.get("scan_id")
            redis_client = None
            if scan_id:
                try:
                    import redis as r
                    from api.config import settings
                    import json as _json
                    redis_client = r.from_url(settings.REDIS_URL)
                except Exception:
                    pass

            total_scrapers = len(scrapers)
            attempt_log = {}  # scraper_name -> status (S122-obs)
            for idx, scraper in enumerate(scrapers):
                input_value = inputs.get(scraper.input_type)
                if input_value is None:
                    attempt_log[scraper.name] = "no_input"
                    continue  # Skip scrapers whose input isn't available

                # Update Redis progress
                if redis_client and scan_id:
                    try:
                        redis_client.setex(
                            f"scan:{scan_id}:scraper_progress",
                            300,
                            _json.dumps({"current": idx + 1, "total": total_scrapers, "current_name": scraper.display_name or scraper.name}),
                        )
                    except Exception:
                        pass

                try:
                    result = await engine.execute(scraper.to_dict(), input_value)
                except Exception as e:
                    logger.debug("Scraper %s failed: %s", scraper.name, e)
                    attempt_log[scraper.name] = "exception"
                    continue

                if not result.get("found"):
                    sc = result.get("status_code")
                    reason = result.get("not_found_reason")
                    # S128: explicit miss signals (the service told us the entity
                    # doesn't exist, or we hit a known block surface) are NOT errors —
                    # they're legitimate "no data we can pull" outcomes.
                    if reason in ("explicit_not_found", "blocked_403", "implicit_not_found"):
                        attempt_log[scraper.name] = "no_data"
                    elif isinstance(sc, int) and sc >= 400:
                        attempt_log[scraper.name] = f"error_{sc}"
                    else:
                        attempt_log[scraper.name] = "no_data"
                    continue

                attempt_log[scraper.name] = "success"
                extracted = result.get("extracted", {})

                # Build finding title from template
                try:
                    title = (scraper.finding_title_template or "{service}: profile found").format(
                        service=scraper.display_name or scraper.name,
                        **{k: v for k, v in extracted.items() if v is not None},
                    )
                except (KeyError, IndexError):
                    title = f"{scraper.display_name or scraper.name}: profile found"

                # S159: safer fallback — when scraper.identity_type is unspecified,
                # default to input_type. A DNS scraper given a domain should write
                # 'domain' findings, not pretend it produced a 'username'.
                indicator_type = scraper.identity_type or scraper.input_type

                # S260 (Bug 2): when the scraper's input IS the handle
                # (input_type="username"), the URL was already built from
                # input_value — the slug IS the canonical username. The scraped
                # display_name (og:title) is page-title noise ("william | Linktree",
                # "Telegram: Contact @aevyrie", "Arthur DeWaal - Croonwolter…").
                # Keep the scraped text in `data.extracted` + the title template,
                # never as the username indicator.
                if indicator_type == "username" and scraper.input_type == "username":
                    resolved_indicator = input_value
                else:
                    resolved_indicator = (
                        extracted.get("display_name") or
                        extracted.get("username") or
                        input_value
                    )

                # S159: writer guard — skip materializing "tried, found nothing" as
                # a finding. Real telemetry of attempts lives in scan.module_progress.
                if not resolved_indicator or not str(resolved_indicator).strip():
                    continue  # don't materialize empty findings

                results.append(ScanResult(
                    module=scraper.name,
                    layer=self.LAYER,
                    category=scraper.finding_category or "social_account",
                    severity=scraper.finding_severity or "low",
                    title=title,
                    description=f"Data extracted from {scraper.display_name or scraper.name}",
                    url=result.get("url"),
                    data={
                        "scraper": scraper.name,
                        "platform": scraper.name.replace("_profile", "").replace("_scraper", ""),
                        "extracted": extracted,
                        "status_code": result.get("status_code"),
                    },
                    indicator_value=resolved_indicator,
                    indicator_type=indicator_type,
                ))

                # Wait between scrapers to respect rate limits
                await asyncio.sleep(scraper.rate_limit_window / max(scraper.rate_limit_requests, 1))

            # Persist per-scraper attempt log to scan.module_progress (S122-obs)
            if scan_id:
                try:
                    from api.models.scan import Scan
                    from sqlalchemy.orm.attributes import flag_modified
                    persist_sess = get_sync_session()
                    try:
                        sc_row = persist_sess.execute(
                            select(Scan).where(Scan.id == scan_id)
                        ).scalar_one_or_none()
                        if sc_row is not None:
                            mp = dict(sc_row.module_progress or {})
                            mp["scraper_engine_attempts"] = attempt_log
                            sc_row.module_progress = mp
                            flag_modified(sc_row, "module_progress")
                            persist_sess.commit()
                    finally:
                        persist_sess.close()
                except Exception:
                    logger.exception("Failed to persist scraper_engine_attempts")

            await engine.close()

        except Exception:
            logger.exception("ScraperScanner failed")
        finally:
            session.close()

        return results

    async def health_check(self) -> bool:
        return True

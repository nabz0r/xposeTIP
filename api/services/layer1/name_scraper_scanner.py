import asyncio
import logging

from api.services.base import BaseScanner, ScanResult
from api.services.scraper_engine import ScraperEngine

logger = logging.getLogger(__name__)


class NameScraperScanner(BaseScanner):
    """
    Meta-scanner that executes all enabled scrapers with input_type='name'.
    Reads the resolved person name from target.profile_data._auto_resolved_name
    or operator-asserted target.user_first_name + target.user_last_name.

    If no name is available, silently returns empty results (logged).
    Persists per-scraper attempt status to scan.module_progress.name_scraper_engine_attempts.
    """

    MODULE_ID = "name_scraper_engine"
    LAYER = 1
    CATEGORY = "identity"

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        results = []

        from sqlalchemy import select

        from api.models.scan import Scan
        from api.models.scraper import Scraper
        from api.models.target import Target
        from api.tasks.utils import get_sync_session

        scan_id = kwargs.get("scan_id")
        session = get_sync_session()
        try:
            target = None
            if scan_id:
                sc_row = session.execute(select(Scan).where(Scan.id == scan_id)).scalar_one_or_none()
                if sc_row is not None:
                    target = session.execute(
                        select(Target).where(Target.id == sc_row.target_id)
                    ).scalar_one_or_none()

            if target is None:
                # Email can be duplicated across workspaces — pick most recently created
                target = session.execute(
                    select(Target).where(Target.email == email).order_by(Target.created_at.desc())
                ).scalars().first()

            if target is None:
                logger.warning("name_scraper_engine: target not found for scan_id=%s", scan_id)
                return results

            operator_name = " ".join(
                p for p in [getattr(target, "user_first_name", None), getattr(target, "user_last_name", None)] if p
            ).strip()
            auto_name = (target.profile_data or {}).get("_auto_resolved_name") or ""
            name_input = operator_name or auto_name.strip()

            if not name_input:
                logger.info(
                    "name_scraper_engine: no name input available for target %s — skipping name scrapers",
                    target.id,
                )
                if scan_id:
                    self._persist_attempts(session, scan_id, {"_skipped": "no_name_input"})
                return results

            scrapers = session.execute(
                select(Scraper).where(
                    Scraper.enabled == True,
                    Scraper.input_type == "name",
                )
            ).scalars().all()

            if not scrapers:
                logger.info("name_scraper_engine: no enabled name-input scrapers in DB")
                return results

            logger.info(
                "name_scraper_engine: dispatching %d name-input scrapers with name=%r (source=%s)",
                len(scrapers), name_input, "operator" if operator_name else "auto",
            )

            engine = ScraperEngine()
            attempt_log = {}

            for scraper in scrapers:
                try:
                    result = await engine.execute(scraper.to_dict(), name_input)
                except Exception as e:
                    logger.debug("name scraper %s failed: %s", scraper.name, e)
                    attempt_log[scraper.name] = "exception"
                    continue

                if not result.get("found"):
                    sc = result.get("status_code")
                    if isinstance(sc, int) and sc >= 400:
                        attempt_log[scraper.name] = f"error_{sc}"
                    else:
                        attempt_log[scraper.name] = "no_data"
                    continue

                attempt_log[scraper.name] = "success"
                extracted = result.get("extracted", {})

                try:
                    title = (scraper.finding_title_template or "{service}: hit on {name}").format(
                        service=scraper.display_name or scraper.name,
                        name=name_input,
                        **{k: v for k, v in extracted.items() if v is not None},
                    )
                except (KeyError, IndexError):
                    title = f"{scraper.display_name or scraper.name}: hit on {name_input}"

                results.append(ScanResult(
                    module=scraper.name,
                    layer=self.LAYER,
                    category=scraper.finding_category or "identity",
                    severity=scraper.finding_severity or "high",
                    title=title,
                    description=f"Name match for {name_input!r} on {scraper.display_name or scraper.name}",
                    url=result.get("url"),
                    indicator_type=scraper.input_type,
                    indicator_value=name_input,
                    data={
                        "scraper": scraper.name,
                        "platform": scraper.name,
                        "name_queried": name_input,
                        "name_source": "operator" if operator_name else "auto",
                        "extracted": extracted,
                        "status_code": result.get("status_code"),
                    },
                ))

                await asyncio.sleep(
                    scraper.rate_limit_window / max(scraper.rate_limit_requests, 1)
                )

            if scan_id:
                self._persist_attempts(session, scan_id, attempt_log)

            await engine.close()

        except Exception:
            logger.exception("name_scraper_engine: unexpected failure")
        finally:
            session.close()

        return results

    @staticmethod
    def _persist_attempts(session, scan_id, attempt_log):
        """Persist per-scraper attempts to scan.module_progress.name_scraper_engine_attempts."""
        from sqlalchemy import select
        from sqlalchemy.orm.attributes import flag_modified

        from api.models.scan import Scan

        try:
            sc_row = session.execute(select(Scan).where(Scan.id == scan_id)).scalar_one_or_none()
            if sc_row is not None:
                mp = dict(sc_row.module_progress or {})
                mp["name_scraper_engine_attempts"] = attempt_log
                sc_row.module_progress = mp
                flag_modified(sc_row, "module_progress")
                session.commit()
        except Exception:
            logger.exception("Failed to persist name_scraper_engine_attempts")

    async def health_check(self) -> bool:
        return True

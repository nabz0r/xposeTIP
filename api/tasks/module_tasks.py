import asyncio
import importlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

logger = logging.getLogger(__name__)

SCANNER_REGISTRY = {
    "email_validator": "api.services.layer1.email_validator:EmailValidatorScanner",
    "holehe": "api.services.layer1.holehe_scanner:HoleheScanner",
    "hibp": "api.services.layer1.hibp_scanner:HIBPScanner",
    "sherlock": "api.services.layer1.sherlock_scanner:SherlockScanner",
    "gravatar": "api.services.layer1.gravatar_scanner:GravatarScanner",
    "social_enricher": "api.services.layer1.social_enricher:SocialEnricherScanner",
    "google_profile": "api.services.layer1.google_scanner:GoogleScanner",
    "whois_lookup": "api.services.layer2.whois_scanner:WhoisScanner",
    "maxmind_geo": "api.services.layer2.maxmind_scanner:MaxmindScanner",
    "geoip": "api.services.layer2.geoip_scanner:GeoIPScanner",
    "emailrep": "api.services.layer1.emailrep_scanner:EmailRepScanner",
    "epieos": "api.services.layer1.epieos_scanner:EpieosScanner",
    "fullcontact": "api.services.layer1.fullcontact_scanner:FullContactScanner",
    "github_deep": "api.services.layer1.github_scanner:GitHubDeepScanner",
    "username_hunter": "api.services.layer1.username_scanner:UsernameScannerPlugin",
    "leaked_domains": "api.services.layer2.leaked_scanner:LeakedScanner",
    "dns_deep": "api.services.layer2.dns_scanner:DNSDeepScanner",
    # Layer 2 — Premium (requires API keys)
    "virustotal": "api.services.layer2.virustotal_scanner:VirusTotalScanner",
    "shodan": "api.services.layer2.shodan_scanner:ShodanScanner",
    "intelx": "api.services.layer2.intelx_scanner:IntelXScanner",
    "hunter": "api.services.layer2.hunter_scanner:HunterScanner",
    "dehashed": "api.services.layer2.dehashed_scanner:DehashedScanner",
}


def _get_scanner(module_id: str):
    path = SCANNER_REGISTRY.get(module_id)
    if not path:
        logger.info("No scanner implemented for %s", module_id)
        return None
    module_path, class_name = path.split(":")
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)()
    except Exception:
        logger.exception("Failed to load scanner %s from %s", class_name, module_path)
        return None


def _update_progress(session, scan_id: str, module_id: str, status: str):
    from api.models.scan import Scan
    scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
    if scan:
        progress = dict(scan.module_progress or {})
        progress[module_id] = status
        scan.module_progress = progress
        session.commit()


@celery_app.task(name="api.tasks.module_tasks.run_module", bind=True)
def run_module(self, scan_id: str, module_id: str, email: str):
    from api.models.scan import Scan
    from api.models.finding import Finding
    from api.models.identity import Identity

    session = get_sync_session()
    try:
        _update_progress(session, scan_id, module_id, "running")

        scanner = _get_scanner(module_id)
        if not scanner:
            _update_progress(session, scan_id, module_id, "skipped")
            return {"module": module_id, "skipped": True, "reason": "no scanner implemented"}

        # Fetch scan record first (needed for workspace_id)
        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return {"error": "Scan not found"}

        # Load workspace API keys for scanners that need them
        scanner_kwargs = {}
        if module_id in ("hibp",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "HIBP_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("maxmind_geo",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "MAXMIND_LICENSE", session)
            if key:
                scanner_kwargs["license_key"] = key
        elif module_id in ("fullcontact",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "FULLCONTACT_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("github_deep",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "GITHUB_TOKEN", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("virustotal",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "VIRUSTOTAL_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("shodan",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "SHODAN_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("intelx",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "INTELX_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("hunter",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "HUNTER_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key
        elif module_id in ("dehashed",):
            from api.routers.settings import get_workspace_api_key
            key = get_workspace_api_key(scan.workspace_id, "DEHASHED_API_KEY", session)
            if key:
                scanner_kwargs["api_key"] = key

        # Run async scanner in sync context
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(scanner.scan(email, **scanner_kwargs))
        finally:
            loop.close()

        created = 0
        for result in results:
            # Check for duplicate
            existing = session.execute(
                select(Finding).where(
                    Finding.target_id == scan.target_id,
                    Finding.module == result.module,
                    Finding.title == result.title,
                    Finding.indicator_value == result.indicator_value,
                )
            ).scalar_one_or_none()

            if existing:
                existing.last_seen = datetime.now(timezone.utc)
            else:
                finding = Finding(
                    workspace_id=scan.workspace_id,
                    scan_id=scan.id,
                    target_id=scan.target_id,
                    module=result.module,
                    layer=result.layer,
                    category=result.category,
                    severity=result.severity,
                    title=result.title,
                    description=result.description,
                    data=result.data,
                    url=result.url,
                    indicator_value=result.indicator_value,
                    indicator_type=result.indicator_type,
                    verified=result.verified,
                )
                # Compute confidence based on source reliability
                from api.services.layer4.source_scoring import compute_finding_confidence
                finding.confidence = compute_finding_confidence(finding)
                session.add(finding)
                session.flush()
                created += 1

                # Create identity node if indicator exists
                if result.indicator_value and result.indicator_type:
                    existing_identity = session.execute(
                        select(Identity).where(
                            Identity.workspace_id == scan.workspace_id,
                            Identity.target_id == scan.target_id,
                            Identity.type == result.indicator_type,
                            Identity.value == result.indicator_value,
                        )
                    ).scalar_one_or_none()

                    if not existing_identity:
                        identity = Identity(
                            workspace_id=scan.workspace_id,
                            target_id=scan.target_id,
                            type=result.indicator_type,
                            value=result.indicator_value,
                            platform=result.title.split(" on ")[-1] if " on " in result.title else None,
                            source_module=result.module,
                            source_finding=finding.id,
                        )
                        session.add(identity)

        session.commit()
        _update_progress(session, scan_id, module_id, "completed")

        return {"module": module_id, "results": len(results), "new_findings": created}

    except Exception as e:
        session.rollback()
        logger.exception("Module %s failed for scan %s", module_id, scan_id)
        _update_progress(session, scan_id, module_id, "failed")
        return {"error": str(e)}
    finally:
        session.close()

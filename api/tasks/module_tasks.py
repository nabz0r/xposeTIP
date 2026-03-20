import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.tasks import celery_app
from api.tasks.utils import get_sync_session

SCANNER_MAP = {
    "holehe": "api.services.layer1.holehe_scanner.HoleheScanner",
    "email_validator": "api.services.layer1.email_validator.EmailValidatorScanner",
}


def _get_scanner(module_id: str):
    path = SCANNER_MAP.get(module_id)
    if not path:
        return None
    module_path, class_name = path.rsplit(".", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)()


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
            _update_progress(session, scan_id, module_id, "failed")
            return {"error": f"No scanner for module {module_id}"}

        # Run async scanner in sync context
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(scanner.scan(email))
        finally:
            loop.close()

        scan = session.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id))).scalar_one_or_none()
        if not scan:
            return {"error": "Scan not found"}

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
        _update_progress(session, scan_id, module_id, "failed")
        return {"error": str(e)}
    finally:
        session.close()

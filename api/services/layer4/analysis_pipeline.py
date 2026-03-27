"""Analysis Pipeline — automated intelligence analysis on scan results.

After all scanners complete and profile is aggregated, this pipeline
runs a series of analyzers that cross-reference findings to produce
new intelligence-grade insights (category="intelligence").

Called from finalize_scan after profile aggregation.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models.finding import Finding
from api.models.identity import Identity

logger = logging.getLogger(__name__)


def _analyzer_confidence(result: dict) -> float:
    """Map analyzer severity to confidence. Intelligence findings are inferences,
    not direct discoveries — they should rank below platform-confirmed data."""
    severity = result.get("severity", "info")
    if severity == "critical":
        return 0.85
    if severity == "high":
        return 0.75
    if severity == "medium":
        return 0.65
    if severity == "low":
        return 0.50
    return 0.40  # info


class AnalysisPipeline:
    """Orchestrates all intelligence analyzers."""

    def run(self, target_id, workspace_id, scan_id, session: Session) -> int:
        """Run all analyzers synchronously (called from Celery worker).

        Returns count of new intelligence findings created.
        """
        # Load all findings and identities for this target
        findings = session.execute(
            select(Finding).where(
                Finding.target_id == target_id,
                Finding.workspace_id == workspace_id,
                Finding.status == "active",
            )
        ).scalars().all()

        identities = session.execute(
            select(Identity).where(
                Identity.target_id == target_id,
                Identity.workspace_id == workspace_id,
            )
        ).scalars().all()

        if not findings:
            return 0

        # Import analyzers lazily to avoid circular imports
        from api.services.layer4.analyzers.ip_analyzer import IPAnalyzer
        from api.services.layer4.analyzers.domain_analyzer import DomainAnalyzer
        from api.services.layer4.analyzers.username_correlator import UsernameCorrelator
        from api.services.layer4.analyzers.breach_correlator import BreachCorrelator
        from api.services.layer4.analyzers.risk_assessor import RiskAssessor

        analyzers = [
            IPAnalyzer(),
            DomainAnalyzer(),
            UsernameCorrelator(),
            BreachCorrelator(),
            RiskAssessor(),
        ]

        new_count = 0
        for analyzer in analyzers:
            try:
                results = analyzer.analyze(findings, identities)
                for result in results:
                    # Check for duplicate intelligence finding
                    existing = session.execute(
                        select(Finding).where(
                            Finding.target_id == target_id,
                            Finding.module == "intelligence",
                            Finding.title == result["title"],
                        )
                    ).scalar_one_or_none()

                    if existing:
                        # Update data if changed
                        existing.data = result.get("data", {})
                        existing.description = result.get("description", "")
                        existing.severity = result.get("severity", "info")
                        continue

                    finding = Finding(
                        workspace_id=workspace_id,
                        scan_id=uuid.UUID(scan_id) if isinstance(scan_id, str) else scan_id,
                        target_id=target_id,
                        module="intelligence",
                        layer=4,
                        category=result.get("category", "intelligence"),
                        severity=result.get("severity", "info"),
                        title=result["title"],
                        description=result.get("description", ""),
                        data=result.get("data", {}),
                        indicator_value=result.get("indicator_value"),
                        indicator_type=result.get("indicator_type"),
                        verified=result.get("verified", True),
                        confidence=_analyzer_confidence(result),
                    )
                    session.add(finding)
                    new_count += 1

            except Exception:
                logger.exception("Analyzer %s failed", analyzer.__class__.__name__)

        if new_count > 0:
            session.commit()
            logger.info(
                "Intelligence pipeline created %d findings for target %s",
                new_count, target_id,
            )

        return new_count

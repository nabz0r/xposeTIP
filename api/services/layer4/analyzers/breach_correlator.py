"""Breach Correlator — cross-reference breach data for patterns.

Detects password reuse risk, exposure timeline, and data type aggregation.
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class BreachCorrelator:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        breach_findings = [f for f in findings if f.category == "breach"]

        if not breach_findings:
            return results

        # 1. Data type aggregation across all breaches
        all_data_types = set()
        password_breaches = []
        breach_dates = []
        breach_names = []

        for f in breach_findings:
            data = f.data or {}
            breach_name = data.get("Name") or data.get("breach_name") or f.title
            breach_names.append(breach_name)

            # Collect data classes
            data_classes = data.get("DataClasses") or data.get("data_classes") or []
            for dc in data_classes:
                all_data_types.add(dc)
                if "password" in dc.lower() or "credential" in dc.lower():
                    password_breaches.append(breach_name)

            # Collect dates
            breach_date = data.get("BreachDate") or data.get("date")
            if breach_date:
                breach_dates.append(breach_date)

        # Data exposure summary
        if all_data_types:
            results.append({
                "title": f"Data exposure: {len(all_data_types)} data types across {len(breach_findings)} breaches",
                "description": f"Exposed data types: {', '.join(sorted(all_data_types))}",
                "category": "intelligence",
                "severity": "critical" if len(password_breaches) > 1 else "high",
                "data": {
                    "analyzer": "breach_correlator",
                    "data_types": sorted(all_data_types),
                    "data_type_count": len(all_data_types),
                    "total_breaches": len(breach_findings),
                    "breach_names": breach_names[:20],
                    "password_breaches": password_breaches,
                },
            })

        # 2. Password reuse risk
        if len(password_breaches) > 1:
            results.append({
                "title": f"Password exposed in {len(password_breaches)} separate breaches",
                "description": (
                    "Multiple password exposures dramatically increase credential stuffing risk. "
                    f"Breaches with passwords: {', '.join(password_breaches[:5])}. "
                    "Immediate password change recommended on all platforms."
                ),
                "category": "intelligence",
                "severity": "critical",
                "data": {
                    "analyzer": "breach_correlator",
                    "risk": "password_reuse",
                    "breach_count": len(password_breaches),
                    "breaches": password_breaches,
                    "remediation": "Change passwords on all platforms immediately and enable 2FA",
                },
            })

        # 3. Exposure timeline
        if len(breach_dates) > 1:
            sorted_dates = sorted(breach_dates)
            earliest = sorted_dates[0]
            latest = sorted_dates[-1]
            results.append({
                "title": f"Breach exposure timeline: {earliest} to {latest}",
                "description": (
                    f"Data has been exposed in breaches from {earliest} to {latest}. "
                    f"{len(breach_findings)} breaches over this period indicate sustained exposure."
                ),
                "category": "intelligence",
                "severity": "medium",
                "data": {
                    "analyzer": "breach_correlator",
                    "earliest_breach": earliest,
                    "latest_breach": latest,
                    "breach_count": len(breach_findings),
                    "timeline": sorted_dates,
                },
            })

        return results

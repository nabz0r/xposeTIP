"""Code Leak Analyzer — classify severity of code/paste exposure findings.

Scans finding data for sensitive patterns: API keys, passwords, .env files,
database URLs, private keys, tokens.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate high-severity leaks
_SENSITIVE_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]", "API key"),
    (r"(?i)(secret|password|passwd|pwd)\s*[:=]", "password/secret"),
    (r"(?i)(access[_-]?token|auth[_-]?token|bearer)\s*[:=]", "access token"),
    (r"(?i)(private[_-]?key|ssh[_-]?key|rsa)", "private key"),
    (r"(?i)(database_url|db_url|postgres://|mysql://|mongodb://)", "database URL"),
    (r"(?i)(aws[_-]?access|aws[_-]?secret|AKIA[A-Z0-9])", "AWS credential"),
    (r"(?i)(stripe[_-]?key|sk_live_|pk_live_)", "Stripe key"),
    (r"(?i)(sendgrid|mailgun|twilio)[_-]?(api|key|token)", "service API key"),
    (r"\.env|\.env\.local|\.env\.production", ".env file"),
    (r"(?i)(BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY)", "private key block"),
]


class CodeLeakAnalyzer:
    def analyze(self, findings: list, identities: list) -> list:
        results = []

        code_findings = [
            f for f in findings
            if f.category == "code_leak" or (f.data and isinstance(f.data, dict) and f.data.get("first_snippet"))
        ]

        if not code_findings:
            return results

        # Aggregate stats
        total_files = 0
        sensitive_leaks = []
        repos = set()

        for f in code_findings:
            data = f.data if isinstance(f.data, dict) else {}
            extracted = data.get("extracted", data)

            count = extracted.get("total_count")
            if count and isinstance(count, (int, str)):
                try:
                    total_files += int(count)
                except (ValueError, TypeError):
                    pass

            repo = extracted.get("first_repo")
            if repo:
                repos.add(repo)

            # Check snippet for sensitive patterns
            snippet = extracted.get("first_snippet", "")
            file_path = extracted.get("first_file", "")
            check_text = f"{snippet} {file_path}"

            for pattern, label in _SENSITIVE_PATTERNS:
                if re.search(pattern, check_text):
                    sensitive_leaks.append({
                        "type": label,
                        "repo": repo or "unknown",
                        "file": file_path,
                        "source": getattr(f, "module", "unknown"),
                    })

        # Generate intelligence findings
        if total_files > 0:
            severity = "critical" if sensitive_leaks else "high" if total_files > 5 else "medium"
            results.append({
                "title": f"Code exposure: email/username found in {total_files} public file(s)",
                "description": (
                    f"Found across {len(repos)} repositories. "
                    + (f"Contains {len(sensitive_leaks)} potentially sensitive leak(s): "
                       f"{', '.join(set(s['type'] for s in sensitive_leaks[:5]))}. "
                       if sensitive_leaks else "")
                    + "Public code references increase exposure to targeted attacks."
                ),
                "category": "intelligence",
                "severity": severity,
                "data": {
                    "analyzer": "code_leak_analyzer",
                    "total_files": total_files,
                    "repos": sorted(repos)[:10],
                    "sensitive_leaks": sensitive_leaks[:10],
                    "risk": "credential_exposure" if sensitive_leaks else "information_disclosure",
                },
            })

        if sensitive_leaks:
            # Individual critical finding per sensitive leak type
            leak_types = set(s["type"] for s in sensitive_leaks)
            for lt in list(leak_types)[:3]:  # Max 3 separate findings
                examples = [s for s in sensitive_leaks if s["type"] == lt]
                results.append({
                    "title": f"Sensitive leak detected: {lt}",
                    "description": (
                        f"Found {len(examples)} instance(s) of {lt} in public code. "
                        f"Repos: {', '.join(set(e['repo'] for e in examples[:3]))}. "
                        "Rotate this credential immediately."
                    ),
                    "category": "intelligence",
                    "severity": "critical",
                    "data": {
                        "analyzer": "code_leak_analyzer",
                        "leak_type": lt,
                        "instances": examples[:5],
                    },
                })

        return results

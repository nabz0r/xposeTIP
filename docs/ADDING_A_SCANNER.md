# Contributing to xpose

## Adding a New Scanner

Every scanner inherits from `BaseScanner` and follows a 4-step process.

### 1. Create the Scanner Class

```python
# api/services/layer{N}/my_scanner.py
from api.services.base_scanner import BaseScanner, ScanResult, Finding

class MyScanner(BaseScanner):
    MODULE_ID = "my_scanner"
    LAYER = 1  # 1=passive, 2=public_db, 3=self_audit
    CATEGORY = "social_account"  # breach, metadata, social_account, geolocation, etc.

    async def scan(self, target_email: str, **kwargs) -> ScanResult:
        findings = []

        # Your scanner logic here
        # Use self.session for HTTP requests (aiohttp)
        # Respect rate limits

        findings.append(Finding(
            title="Found something",
            description="Details about what was found",
            severity="medium",  # critical, high, medium, low, info
            data={"raw": "response data"},  # stored as JSONB forever
        ))

        return ScanResult(
            module=self.MODULE_ID,
            findings=findings,
        )

    async def health_check(self) -> dict:
        """Return {"status": "healthy"} or {"status": "unhealthy", "error": "..."}"""
        return {"status": "healthy"}
```

### 2. Register in SCANNER_REGISTRY

```python
# api/tasks/module_tasks.py
SCANNER_REGISTRY = {
    # ...existing scanners...
    "my_scanner": "api.services.layer1.my_scanner:MyScanner",
}
```

If your scanner needs an API key, add loading logic in `run_module()`:
```python
elif module_id == "my_scanner":
    kwargs["api_key"] = keys.get("MY_SERVICE_API_KEY", "")
```

### 3. Add Module to Seed Script

```python
# scripts/seed_modules.py — add to MODULES list
{
    "id": "my_scanner",
    "display_name": "My Scanner",
    "description": "What this scanner does",
    "layer": 1,
    "category": "social_account",
    "enabled": True,
    "requires_auth": False,
    "rate_limit": {"rpm": 30, "cooldown_sec": 2},
    "supported_regions": ["*"],
    "version": "1.0.0",
},
```

### 4. Add Source Reliability Score

```python
# api/services/layer4/source_scoring.py
SOURCE_RELIABILITY = {
    # ...existing...
    "my_scanner": 0.70,  # 0.50-0.95 based on data quality
}
```

Then re-seed:
```bash
docker compose exec api python scripts/seed_modules.py
```

## Code Style

- **Backend**: Python 3.11+, type hints, async/await
- **Frontend**: React 18, functional components, Tailwind CSS
- **Database**: SQLAlchemy 2.0 `mapped_column`, UUID PKs, TIMESTAMPTZ
- **All DB queries** must be scoped to `workspace_id`
- **All external calls** go through Celery workers, never in the API process
- **Raw tool output** stored in `findings.data` JSONB — never discard

## Scanner Guidelines

- Rate limit every external API call
- Handle timeouts gracefully (return partial results)
- Never store plaintext passwords — breach names + hash prefixes only
- GeoIP findings = mail server location, NOT user location (label accordingly)
- Return `ScanResult` even on failure (empty findings, error in metadata)

## Pull Request Process

1. Branch from `main`
2. One scanner per PR
3. Include health_check implementation
4. Test with `docker compose exec api python -c "from api.services.layer1.my_scanner import MyScanner; print('OK')"`
5. Re-seed and verify module appears in `/api/v1/modules`

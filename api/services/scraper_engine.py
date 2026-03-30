import asyncio
import hashlib
import json
import logging
import re
import time as _time

import httpx

logger = logging.getLogger(__name__)

# Lazy-loaded scraper health instance
_health_instance = None


def _get_health():
    global _health_instance
    if _health_instance is None:
        try:
            from api.services.scraper_health import get_scraper_health_instance
            _health_instance = get_scraper_health_instance()
        except Exception:
            pass
    return _health_instance


class ScraperEngine:
    """
    Executes scraper definitions against targets.
    Each scraper is a DB record with URL template + extraction rules.
    No API keys. Just HTTP requests + regex/JSONPath = data.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )

    async def execute(self, scraper: dict, input_value: str) -> dict:
        """Execute a single scraper definition against an input value."""
        url = ""
        try:
            from urllib.parse import quote as url_quote

            transformed = self._transform_input(input_value, scraper)
            domain = input_value.split("@")[-1] if "@" in input_value else input_value

            # Derive name-based placeholders from email prefix
            prefix = input_value.split("@")[0] if "@" in input_value else input_value
            cleaned_prefix = re.sub(r"\d+", "", prefix)
            name_parts = re.split(r"[._]", cleaned_prefix)
            first_name = name_parts[0].lower() if name_parts else prefix
            fullname = " ".join(p for p in name_parts if len(p) > 1).strip() or prefix

            email_md5 = hashlib.md5(input_value.lower().strip().encode()).hexdigest() if "@" in input_value else ""

            fmt_kwargs = dict(
                email=input_value,
                username=transformed,
                domain=domain,
                input=input_value,
                first_name=first_name,
                fullname=fullname,
                fullname_encoded=url_quote(fullname),
                email_md5=email_md5,
            )

            url = scraper["url_template"].format(**fmt_kwargs)

            headers = {**dict(self.client.headers), **(scraper.get("headers") or {})}

            _t0 = _time.time()
            response = None
            for _attempt in range(3):
                if scraper.get("method", "GET").upper() == "POST":
                    body = (scraper.get("body_template") or "").format(**fmt_kwargs)
                    response = await self.client.post(url, content=body, headers=headers)
                else:
                    response = await self.client.get(url, headers=headers)
                if response.status_code == 429:
                    _retry = min(int(response.headers.get("Retry-After", 2 ** _attempt)), 10)
                    logger.info("429 on %s, retry in %ds (%d/3)", scraper.get("name"), _retry, _attempt + 1)
                    await asyncio.sleep(_retry)
                    continue
                break
            _elapsed_ms = int((_time.time() - _t0) * 1000)

            # Record health metric (fire-and-forget)
            _h = _get_health()
            if _h:
                _h.record(scraper.get("name", "unknown"), response.status_code, _elapsed_ms)

            content = response.text
            found = self._check_found(content, response.status_code, scraper)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "SCRAPER_DEBUG %s: status=%d, found=%s, content_len=%d, preview=%s",
                    scraper.get("name"), response.status_code, found,
                    len(content), content[:300].replace('\n', ' '),
                )

            if not found:
                return {"found": False, "url": url, "status_code": response.status_code, "error": None}

            extracted = {}
            for rule in scraper.get("extraction_rules") or []:
                value = self._extract(content, rule)
                if value is not None:
                    extracted[rule["field"]] = value

            return {
                "found": True,
                "extracted": extracted,
                "url": url,
                "status_code": response.status_code,
                "raw_html": content[:5000],
                "error": None,
            }

        except httpx.TimeoutException:
            return {"found": False, "error": "timeout", "url": url}
        except Exception as e:
            logger.debug("Scraper %s failed: %s", scraper.get("name"), e)
            return {"found": False, "error": str(e), "url": url}

    async def close(self):
        await self.client.aclose()

    def _transform_input(self, input_value: str, scraper: dict) -> str:
        transform = scraper.get("input_transform")
        if not transform:
            if "@" in input_value:
                return input_value.split("@")[0]
            return input_value

        if transform == "email_to_username":
            return input_value.split("@")[0]
        elif transform == "email_to_domain":
            return input_value.split("@")[-1]
        elif transform == "email_to_first_name":
            prefix = input_value.split("@")[0] if "@" in input_value else input_value
            cleaned = re.sub(r"\d+", "", prefix)
            parts = re.split(r"[._]", cleaned)
            first = parts[0] if parts else cleaned
            return first.lower() if first else prefix

        elif transform == "email_to_fullname":
            prefix = input_value.split("@")[0] if "@" in input_value else input_value
            cleaned = re.sub(r"\d+", "", prefix)
            parts = re.split(r"[._]", cleaned)
            return " ".join(p for p in parts if len(p) > 1).strip() or prefix

        elif transform == "url_encode":
            from urllib.parse import quote
            return quote(input_value)

        elif transform.startswith("regex:"):
            pattern = transform[6:]
            match = re.search(pattern, input_value)
            return match.group(1) if match else input_value

        return input_value

    def _check_found(self, content: str, status_code: int, scraper: dict) -> bool:
        if status_code in (404, 410, 429):
            return False

        success = scraper.get("success_indicator")
        not_found = scraper.get("not_found_indicators") or []
        content_lower = content.lower()

        # Check success_indicator FIRST — if it specifically matches, profile exists
        if success and re.search(success, content, re.IGNORECASE):
            # Double-check against SPECIFIC not_found signals (>= 10 chars)
            # Short/broad terms like "Snapchat", "404" can appear on valid pages
            for indicator in not_found:
                if len(indicator) >= 10 and indicator.lower() in content_lower:
                    return False
            return True

        # 403 without success match = blocked
        if status_code == 403:
            return False

        # No success match — check all not_found indicators
        for indicator in not_found:
            if indicator.lower() in content_lower:
                return False

        # Fallback: 200 = found
        return status_code == 200

    def _extract(self, content: str, rule: dict):
        rule_type = rule.get("type", "regex")
        pattern = rule.get("pattern", "")

        try:
            if rule_type == "regex":
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    group = rule.get("group", 1)
                    value = match.group(group)
                    return self._apply_transform(value, rule.get("transform"))

            elif rule_type == "jsonpath":
                try:
                    from jsonpath_ng import parse as jsonpath_parse
                    data = json.loads(content)
                    matches = jsonpath_parse(pattern).find(data)
                    if matches:
                        return self._apply_transform(str(matches[0].value), rule.get("transform"))
                except ImportError:
                    logger.debug("jsonpath_ng not installed, falling back to json_key")
                    return self._extract(content, {**rule, "type": "json_key"})

            elif rule_type == "json_key":
                data = json.loads(content)
                keys = pattern.split(".")
                for key in keys:
                    if isinstance(data, dict):
                        data = data.get(key)
                    elif isinstance(data, list) and key.isdigit():
                        idx = int(key)
                        data = data[idx] if idx < len(data) else None
                    else:
                        return rule.get("default")
                    if data is None:
                        return rule.get("default")
                return self._apply_transform(str(data), rule.get("transform")) if data is not None else rule.get("default")

        except Exception as e:
            logger.debug("Extraction failed for %s: %s", rule.get("field"), e)

        return rule.get("default")

    def _apply_transform(self, value: str, transform: str) -> str | int:
        if not transform or not value:
            return value
        if transform == "lowercase":
            return value.lower()
        if transform == "strip_html":
            return re.sub(r"<[^>]+>", "", value).strip()
        if transform == "parse_int":
            nums = re.findall(r"\d+", str(value))
            return int(nums[0]) if nums else 0
        if transform == "strip":
            return value.strip().strip('"').strip("'")
        if transform == "url_last_segment":
            return value.rstrip("/").rsplit("/", 1)[-1].strip()
        return value

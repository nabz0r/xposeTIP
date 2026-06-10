import asyncio
import hashlib
import html
import json
import logging
import os
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

            # Phone/crypto placeholders
            phone = input_value if scraper.get("input_type") == "phone" else ""
            phone_clean = phone.replace("+", "") if phone else ""
            crypto_address = input_value if scraper.get("input_type") == "crypto_wallet" else ""

            fmt_kwargs = dict(
                email=input_value,
                username=transformed,
                domain=domain,
                input=input_value,
                first_name=first_name,
                fullname=fullname,
                fullname_encoded=url_quote(fullname),
                email_md5=email_md5,
                phone=phone,
                phone_clean=phone_clean,
                crypto_address=crypto_address,
                # S217: env-var substitution for scraper API keys.
                # url_template placeholders like {API_NINJAS_KEY} are resolved
                # at format-time from the container environment (loaded from .env
                # via docker-compose env_file).
                API_NINJAS_KEY=os.environ.get("API_NINJAS_KEY", ""),
                VERIPHONE_API_KEY=os.environ.get("VERIPHONE_API_KEY", ""),
                NUMVERIFY_API_KEY=os.environ.get("NUMVERIFY_API_KEY", ""),
                ABSTRACTAPI_PHONE_KEY=os.environ.get("ABSTRACTAPI_PHONE_KEY", ""),
            )

            url = scraper["url_template"].format(**fmt_kwargs)

            # S217: guard against seeded `placeholder` strings reaching remote.
            # A scraper config that ships with `=placeholder` in its url_template
            # and isn't paired with a matching env-var rotation lands here.
            # Empty env vars (missing .env) produce URLs with `=` followed by
            # nothing — that's NOT caught here (it's a different failure mode,
            # surfaces as auth-rejected 401/403 from the remote).
            if "placeholder" in url.lower():
                logger.warning(
                    "S217 placeholder-guard: scraper %s url_template contains literal "
                    "'placeholder' after substitution — likely missing env-var rotation. "
                    "Skipping dispatch to avoid sending unauth requests.",
                    scraper.get("name", "<unknown>"),
                )
                return {"found": False, "status_code": None, "url": url, "extracted": {}}

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
            found, found_reason = self._check_found(content, response.status_code, scraper)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "SCRAPER_DEBUG %s: status=%d, found=%s, reason=%s, content_len=%d, preview=%s",
                    scraper.get("name"), response.status_code, found, found_reason,
                    len(content), content[:300].replace('\n', ' '),
                )

            if not found:
                return {
                    "found": False,
                    "url": url,
                    "status_code": response.status_code,
                    "error": None,
                    "not_found_reason": found_reason,
                }

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

    def _check_found(self, content: str, status_code: int, scraper: dict) -> tuple[bool, str]:
        """Return (found, reason). Reasons:
          success            — found=True, response matched success_indicator
          explicit_not_found — found=False, a not_found_indicator matched the body
                               (clean miss, even if status >= 400 — many APIs return
                               400/422 for "user not found")
          blocked_403        — found=False, status 403 without success match (bot block)
          implicit_not_found — found=False, status in (404, 410, 429)
          not_2xx            — found=False, status not 2xx and no other classification applied
        """
        if status_code in (404, 410, 429):
            return (False, "implicit_not_found")

        success = scraper.get("success_indicator")
        not_found = scraper.get("not_found_indicators") or []
        content_lower = content.lower()

        # Check success_indicator FIRST — if it specifically matches, profile exists
        if success and re.search(success, content, re.IGNORECASE):
            # Double-check against SPECIFIC not_found signals (>= 10 chars)
            # Short/broad terms like "Snapchat", "404" can appear on valid pages
            for indicator in not_found:
                if len(indicator) >= 10 and indicator.lower() in content_lower:
                    return (False, "explicit_not_found")
            return (True, "success")

        # 403 without success match = blocked
        if status_code == 403:
            return (False, "blocked_403")

        # No success match — check all not_found indicators
        for indicator in not_found:
            if indicator.lower() in content_lower:
                return (False, "explicit_not_found")

        # Fallback: 200 = found, otherwise not_2xx
        if status_code == 200:
            return (True, "success")
        return (False, "not_2xx")

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
        # S260 (Bug 2): unescape + strip every string value at the single
        # exit point of extraction (regex / jsonpath / json_key all route
        # through here). Cleans &#39; / &amp; etc. once for the whole
        # pipeline -- display_name, titles, bios.
        if isinstance(value, str):
            value = html.unescape(value).strip()
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

"""Native press-index search (S264-0g) — deterministic AR-0 press retrieval.

Queries a press site's OWN search index (not DDG's ranking of it) so the article
that names the corporate person is reached deterministically, run-to-run. Adapter
registry in press_adapters.json. Currently: paperjam.lu via its public, search-only
Algolia index.

SECURITY NOTE — the `search_api_key` in press_adapters.json is an Algolia
SEARCH-ONLY key, PUBLIC BY DESIGN: paperjam serves it in the `__NEXT_DATA__` of
every page to drive its own client-side search SPA. It is NOT a secret — do not
treat it as one, do not gate on it. It may rotate at any time → this adapter is
FAIL-SOFT everywhere (returns [] → caller degrades to DDG-only; a false-negative is
safe, never a crash).

Determinism knob (proven by sampling — do NOT relax):
    advancedSyntax=True + query='"<company>"' (exact phrase) + typoTolerance=False
A loose query returns ~1000 fuzzy noise hits (matches "Technologies" etc.); the
exact phrase returns the company footprint — "Pluton Technologies" → 2 hits, #1 =
the article carrying `Eric Lox (Pluton Technologies). (Photo: …)`, the caption the
person_extractor (S264-0 B) already reads. corp_press_site ONLY — the multi-domain
broad press query stays on DDG (no single-index determinism gain there).
"""
import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_REGISTRY = None


def _registry() -> dict:
    global _REGISTRY
    if _REGISTRY is None:
        p = Path(__file__).parent / "press_adapters.json"
        try:
            _REGISTRY = json.loads(p.read_text())
        except Exception as e:
            logger.warning("press_adapters.json unreadable: %s", e)
            _REGISTRY = {}
    return _REGISTRY


class PressNativeSearch:
    """Deterministic per-press native-index search. Fail-soft to [] everywhere."""

    _TIMEOUT = 12

    def search(self, press_domain: str, company: str) -> list[dict]:
        if not press_domain or not company:
            return []
        cfg = _registry().get(press_domain.lower().lstrip("www."))
        if not cfg:
            return []  # no adapter → caller degrades to DDG-only (zero regression)
        if cfg.get("type") == "algolia":
            return self._algolia(cfg, company)
        return []

    def _algolia(self, cfg: dict, company: str) -> list[dict]:
        app = cfg["app_id"]
        key = cfg["search_api_key"]
        idx = cfg["index"]
        url = f"https://{app}-dsn.algolia.net/1/indexes/{idx}/query"
        body = {
            "query": f'"{company}"',          # exact phrase
            "advancedSyntax": True,            # honour the quotes
            "typoTolerance": False,            # no fuzzy → company footprint, not noise
            "hitsPerPage": int(cfg.get("hits_per_page", 8)),
        }
        try:
            r = requests.post(
                url, timeout=self._TIMEOUT,
                headers={
                    "X-Algolia-Application-Id": app,
                    "X-Algolia-API-Key": key,
                    "Content-Type": "application/json",
                },
                data=json.dumps(body),
            )
            if r.status_code != 200:
                logger.warning("press_native(%s): HTTP %d", app, r.status_code)
                return []
            hits = (r.json() or {}).get("hits", []) or []
        except Exception as e:
            logger.warning("press_native(%s) failed: %s", app, e)
            return []

        tmpl = cfg.get("article_url_template", "")
        out = []
        for i, h in enumerate(hits):
            slug = h.get("slug")
            if not slug or not tmpl:
                continue
            out.append({
                "url": tmpl.format(slug=slug),
                "title": (h.get("title") or "").strip(),
                "snippet": (h.get("slugline") or h.get("surTitle") or "").strip(),
                "position": i + 1,
                "source": "press_native",      # provenance, for the dedupe/merge in pipeline
            })
        logger.info("press_native(%s): %d hits for '%s'", app, len(out), company[:60])
        return out

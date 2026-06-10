"""Entity-scoped name matching for legal/corporate register scrapers.

Shared by bodacc_search + uk_gazette_search (S256), and the intended
home for SEC EDGAR / Companies House adoption (Bug 12 Axe C). Replaces
the per-scraper token-co-occurrence matcher that scored 0.85 whenever
all name tokens appeared ANYWHERE in a concatenated multi-field haystack
(S256: guillaume.a.perrin -> 84 phantom BODACC records).

Principle (S238 / Bug 12 Axe C lineage): a scraped row matches the
subject only when the full name appears contiguously within ONE
name-bearing field -- not when its tokens merely co-occur across the row.
"""
import re

_SPLIT_RE = re.compile(r"[^\w]+", re.UNICODE)


def _tokens(s: str) -> list[str]:
    return [t for t in _SPLIT_RE.split(s.lower()) if t]


def name_match_confidence(field_values: list[str], target_name: str) -> float:
    """Confidence (0.0-0.95) that target_name names an entity in one of
    field_values. PER-FIELD: scattered tokens never combine.

    Tiers:
      0.95  full name contiguous in a field        ("guillaume perrin")
      0.90  reversed-order contiguous              ("perrin guillaume")
      0.82  all tokens within a window of n+1       ("GILLES Marie-Paule",
            consecutive field tokens                 extra middle name)
      0.00  otherwise (incl. single-token names -- too noisy)
    """
    if not target_name:
        return 0.0
    target_parts = _tokens(target_name)
    if len(target_parts) < 2:          # single-token names too noisy
        return 0.0
    full = " ".join(target_parts)
    rev = " ".join(reversed(target_parts))
    n = len(target_parts)
    want = set(target_parts)

    best = 0.0
    for raw in field_values:
        if not raw:
            continue
        f_tokens = _tokens(raw)
        if not f_tokens:
            continue
        joined = " ".join(f_tokens)
        if full in joined:
            return 0.95
        if rev in joined:
            best = max(best, 0.90)
            continue
        window = n + 1
        for i in range(0, max(1, len(f_tokens) - window + 1)):
            if want.issubset(set(f_tokens[i:i + window])):
                best = max(best, 0.82)
                break
    return best

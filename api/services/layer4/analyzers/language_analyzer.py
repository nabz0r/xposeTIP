"""Language detection from free-text fields in findings (S237 + S238 trust gate).

Uses lingua-language-detector — Rust-backed Python wrapper, no external API,
strong on short text. The detector is built once at module import with a
restricted language set (~25 common languages) to keep worker memory + cold
start light; the full Lingua catalog is 75 languages and far heavier.

Honesty contract:
- Falls back to {languages: [], primary: None, reliable: False} when input is
  too short (< 30 chars). A 15-char bio is not a language signal.
- `reliable=True` only above 80 chars AND only when the input came from
  cross-verified findings — unverified-source results are NEVER reliable.
- ONLY user-authored free text is sampled (bio / description / about /
  summary / status / caption). Finding `title` is NOT included — those are
  system-generated strings ("Email reputation: high") that would skew the
  whole corpus toward English.

S238 trust gate — TIERED:
  Tier 1 (preferred): only findings with `cross_verification_count >= 1`
    (the indicator is corroborated by at least one other module). This is
    the same trust primitive S167 / S168 use for BFP claims.
  Tier 2 (fallback): if Tier 1 yields < _MIN_BLOB chars, fall back to
    all-text but flip `verified_source=False`. The UI then hedges instead
    of showing a confident percentage.
  Tier 2 ensures the feature degrades to an honest hedge — never to a
  confident wrong claim from handle-collision noise.
"""
from lingua import Language, LanguageDetectorBuilder

_LANGS = [
    Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.SPANISH,
    Language.ITALIAN, Language.DUTCH, Language.PORTUGUESE, Language.RUSSIAN,
    Language.ARABIC, Language.CHINESE, Language.JAPANESE, Language.KOREAN,
    Language.TURKISH, Language.POLISH, Language.SWEDISH, Language.DANISH,
    Language.FINNISH, Language.CZECH, Language.ROMANIAN, Language.GREEK,
    Language.HEBREW, Language.HINDI, Language.UKRAINIAN, Language.BOKMAL,
    Language.HUNGARIAN,
]
_detector = LanguageDetectorBuilder.from_languages(*_LANGS).build()

_TEXT_FIELDS = ("bio", "description", "about", "summary", "status", "caption")
_MIN_FRAGMENT = 15   # per-field char floor — skip nameplate-length strings
_MIN_BLOB = 30       # below this we return nothing reliable at all
_RELIABLE_BLOB = 80  # above this we flag the result as reliable


def _collect(findings, require_verified: bool) -> list[str]:
    texts: list[str] = []
    for f in findings:
        if require_verified and getattr(f, "cross_verification_count", 0) < 1:
            continue
        d = f.data if isinstance(f.data, dict) else None
        if not d:
            continue
        for k in _TEXT_FIELDS:
            v = d.get(k)
            if isinstance(v, str) and len(v.strip()) >= _MIN_FRAGMENT:
                texts.append(v.strip())
    return texts


def analyze_languages(findings: list) -> dict | None:
    # Tier 1 — cross-verified findings only.
    blob = " ".join(_collect(findings, require_verified=True))
    verified_source = True
    if len(blob) < _MIN_BLOB:
        # Tier 2 — fall back to all text, but mark the source unverified.
        blob = " ".join(_collect(findings, require_verified=False))
        verified_source = False

    if len(blob) < _MIN_BLOB:
        return {
            "languages": [],
            "primary": None,
            "sample_chars": len(blob),
            "reliable": False,
            "verified_source": False,
        }

    conf = _detector.compute_language_confidence_values(blob)
    langs = [
        {
            "code": c.language.iso_code_639_1.name.lower(),
            "name": c.language.name.title(),
            "confidence": round(c.value, 2),
        }
        for c in conf
        if c.value >= 0.15
    ][:4]
    return {
        "languages": langs,
        "primary": langs[0]["code"] if langs else None,
        "sample_chars": len(blob),
        # Unverified-source results are NEVER reliable, regardless of length.
        "reliable": verified_source and len(blob) >= _RELIABLE_BLOB,
        "verified_source": verified_source,
    }

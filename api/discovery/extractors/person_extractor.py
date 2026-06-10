"""Corporate-person extractor (S264-0 AR-0).

Resolves the real person behind a corporate email from free business-press pages.
The name lives in image CAPTIONS, not the article prose — and trafilatura drops
captions, so we parse the RAW HTML. Measured shapes on paperjam.lu (locked):

  <img ... alt="Eric Lox (Pluton Technologies). (Photo: Julian Pierrot/Paperjam)">
  <p title="Ekaterina Zaychenkova et Eric Lox (Pluton Technologies)." class="picture-legend__caption ...">
  "caption":"Eric Lox (Pluton Technologies).","credits":"(Photo: ...)"

Pattern: `Name(s) (Company).` — capture names + company; split names on et/and/&/comma.
The company co-occurrence filter (names must belong to the TARGET's company) runs in
`extract_all`, which has the seed email — this extractor is stateless and emits every
`Name (Company)` pair it finds, with the company carried in `context`.
"""
import re

from .base import BaseExtractor, RawLead

# Carriers that hold caption text in the raw HTML (trafilatura strips these).
_ALT_RE = re.compile(r'\balt="([^"]{4,200})"', re.I)
_TITLE_RE = re.compile(r'\btitle="([^"]{4,200})"', re.I)
_JSON_CAP_RE = re.compile(r'"caption"\s*:\s*"([^"]{4,200})"')

# A caption: leading name(s), then "(Company)", optional trailing ". (Photo: …)".
_CAPTION_RE = re.compile(r'^\s*(?P<names>[^()<>]{3,120}?)\s*\((?P<company>[^()<>]{2,60})\)')

# Split a multi-person caption: "Ekaterina Zaychenkova et Eric Lox" / "A and B" / "A, B".
_NAME_SPLIT_RE = re.compile(r'\s+(?:et|and)\s+|\s*&\s*|\s*,\s*', re.I)

# A plausible human name token sequence: 2-4 capitalized words (accents allowed).
_NAME_OK_RE = re.compile(r"^[A-ZÀ-Ý][\w’'\-]+(?:\s+[A-ZÀ-Ý][\w’'\-]+){1,3}$")

# Photo-credit fragment that sometimes leaks into the names group → reject.
_CREDIT_RE = re.compile(r'\bphoto\b|©|getty|paperjam|reuters|afp', re.I)


class PersonExtractor(BaseExtractor):
    name = "person_caption"
    reliability = 0.85

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        if not html:
            return []
        # late import — avoids a hard dep cycle at module load
        from api.services.layer4.collision_guard import is_junk_name_token

        captions = set()
        for rx in (_ALT_RE, _TITLE_RE, _JSON_CAP_RE):
            for m in rx.findall(html):
                cap = m.replace("&amp;", "&").replace("&#39;", "'").replace("&#x27;", "'").strip()
                if cap:
                    captions.add(cap)

        leads = []
        seen = set()
        for cap in captions:
            m = _CAPTION_RE.match(cap)
            if not m:
                continue
            company = re.sub(r"\s+", " ", m.group("company")).strip()
            names_blob = re.sub(r"\s+", " ", m.group("names")).strip()
            if not company or _CREDIT_RE.search(company):
                continue
            for nm in _NAME_SPLIT_RE.split(names_blob):
                nm = nm.strip(" .·–-")
                if not nm or len(nm) < 5:
                    continue
                if _CREDIT_RE.search(nm) or is_junk_name_token(nm):
                    continue
                if not _NAME_OK_RE.match(nm):
                    continue
                key = nm.lower()
                if key in seen:
                    continue
                seen.add(key)
                leads.append(RawLead(
                    lead_type="corporate_person",
                    value=nm,
                    extractor_type=self.name,
                    confidence=self.reliability,
                    # context carries the caption company → co-occurrence filter +
                    # the emitted finding's data.company downstream.
                    context=company,
                ))
        return leads

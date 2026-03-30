from dataclasses import dataclass, field


@dataclass
class RawLead:
    """A lead extracted from a web page. Not yet a DB object."""
    lead_type: str        # email, username, url, name, document, mention
    value: str
    extractor_type: str   # which extractor found it
    confidence: float     # extractor reliability (before depth penalty)
    context: str = ""     # ~50 chars around the extraction point


class BaseExtractor:
    name: str = "base"
    reliability: float = 0.5

    def extract(self, url: str, text: str, html: str) -> list[RawLead]:
        raise NotImplementedError

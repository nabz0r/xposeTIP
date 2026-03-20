from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScanResult:
    module: str
    layer: int
    category: str
    severity: str          # info|low|medium|high|critical
    title: str
    description: str
    data: dict             # raw output — forensic archive
    url: Optional[str] = None
    indicator_value: Optional[str] = None
    indicator_type: Optional[str] = None
    verified: bool = False


class BaseScanner:
    MODULE_ID: str = ""
    LAYER: int = 0
    CATEGORY: str = ""
    SUPPORTED_REGIONS: list[str] = ["*"]

    async def scan(self, email: str, **kwargs) -> list[ScanResult]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError

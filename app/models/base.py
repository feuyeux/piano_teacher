from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class JsonModel:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


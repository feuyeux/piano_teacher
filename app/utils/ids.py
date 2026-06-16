from __future__ import annotations

import hashlib
from pathlib import Path

from app.utils.time_utils import utc_now


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def session_id(piece_id: str) -> str:
    compact_time = utc_now().replace("-", "").replace(":", "").replace(".", "")
    return f"{piece_id}-{compact_time}"


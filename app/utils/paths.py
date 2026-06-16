from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "untitled-score"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def relative_to_project(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(project_root()))
    except ValueError:
        return str(resolved)


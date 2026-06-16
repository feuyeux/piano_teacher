from __future__ import annotations

from pathlib import Path

from app.utils.json_io import read_json, write_json


class ProfileRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def get(self, piece_id: str) -> dict | None:
        path = self.root / f"{piece_id}.json"
        if not path.exists():
            return None
        return read_json(path)

    def save(self, profile: dict) -> None:
        write_json(self.root / f"{profile['piece_id']}.json", profile)


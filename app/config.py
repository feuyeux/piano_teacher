from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.utils.paths import project_root


@dataclass
class Settings:
    score_library_path: str = "scores"
    session_output_path: str = "sessions"
    profile_output_path: str = "profiles"
    musicxml_converter_command: str = "audiveris -batch -export {input}"
    score_import_review_command: str | None = None
    practice_feedback_command: str | None = None
    midi_input_device: str | None = None
    default_tempo_tolerance_ms: int = 180
    default_pitch_tolerance: int = 0

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        if path is None:
            path = project_root() / "app" / "settings.json"
        settings_path = Path(path)
        if not settings_path.exists():
            return cls()
        with settings_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return cls(**{**cls().__dict__, **data})

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else project_root() / path

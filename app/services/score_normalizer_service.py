from __future__ import annotations

from pathlib import Path

from app.tools.musicxml_reader import MusicXmlReader
from app.utils.json_io import write_json


class ScoreNormalizerService:
    def __init__(self) -> None:
        self.reader = MusicXmlReader()

    def normalize(self, piece_id: str, musicxml_path: str | Path, output_path: str | Path) -> dict:
        normalized = self.reader.normalize(piece_id, musicxml_path)
        write_json(output_path, normalized)
        return normalized


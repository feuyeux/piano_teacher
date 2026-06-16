from __future__ import annotations

from pathlib import Path

from app.utils.json_io import read_json, write_json


class PieceRepository:
    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)

    def list_pieces(self) -> list[dict]:
        if not self.index_path.exists():
            return []
        return read_json(self.index_path).get("pieces", [])

    def save_all(self, pieces: list[dict]) -> None:
        write_json(self.index_path, {"pieces": pieces})

    def get_piece(self, piece_id: str) -> dict | None:
        for piece in self.list_pieces():
            if piece.get("piece_id") == piece_id:
                return piece
        return None


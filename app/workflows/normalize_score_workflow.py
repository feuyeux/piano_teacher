from __future__ import annotations

from pathlib import Path

from app.repositories.piece_repository import PieceRepository
from app.services.score_normalizer_service import ScoreNormalizerService
from app.utils.json_io import write_json


class NormalizeScoreWorkflow:
    def __init__(self, score_root: str | Path) -> None:
        self.score_root = Path(score_root)
        self.pieces = PieceRepository(self.score_root / "piece_index.json")
        self.normalizer = ScoreNormalizerService()

    def run(self, piece_id: str) -> dict:
        piece = self.pieces.get_piece(piece_id)
        if not piece:
            raise ValueError(f"Piece not found: {piece_id}")
        musicxml_path = piece.get("primary_musicxml_path")
        if not musicxml_path:
            raise ValueError(f"Piece has no MusicXML: {piece_id}")
        output_path = self.score_root / piece_id / "normalized_score.json"
        normalized = self.normalizer.normalize(piece_id, musicxml_path, output_path)
        piece["score_revision_id"] = normalized["score_revision_id"]
        piece["measure_count"] = normalized["measure_count"]
        all_pieces = [normalized_piece if normalized_piece["piece_id"] != piece_id else piece for normalized_piece in self.pieces.list_pieces()]
        self.pieces.save_all(all_pieces)
        write_json(output_path, normalized)
        return {"status": "completed", "piece": piece, "normalized_score_path": str(output_path), "normalized_score": normalized}


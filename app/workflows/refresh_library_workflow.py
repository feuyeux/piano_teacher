from __future__ import annotations

from pathlib import Path

from app.repositories.piece_repository import PieceRepository
from app.services.score_library_service import ScoreLibraryService


class RefreshLibraryWorkflow:
    def __init__(self, score_root: str | Path) -> None:
        score_root = Path(score_root)
        self.service = ScoreLibraryService(score_root, PieceRepository(score_root / "piece_index.json"))

    def run(self) -> dict:
        pieces = self.service.refresh_index()
        return {"status": "completed", "piece_count": len(pieces), "pieces": pieces}


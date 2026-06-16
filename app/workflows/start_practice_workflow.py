from __future__ import annotations

from pathlib import Path

from app.repositories.piece_repository import PieceRepository
from app.repositories.session_repository import SessionRepository
from app.services.midi_recording_service import MidiRecordingService


class StartPracticeWorkflow:
    def __init__(self, score_root: str | Path, session_root: str | Path) -> None:
        self.score_root = Path(score_root)
        self.piece_repo = PieceRepository(self.score_root / "piece_index.json")
        self.recording = MidiRecordingService(SessionRepository(session_root), session_root)

    def run(self, piece_id: str, user_command: str | None = None) -> dict:
        piece = self.piece_repo.get_piece(piece_id)
        if not piece:
            raise ValueError(f"Piece not found: {piece_id}")
        normalized_path = self.score_root / piece_id / "normalized_score.json"
        if not normalized_path.exists():
            raise ValueError(f"Normalized score not found: {normalized_path}")
        session = self.recording.start(piece, str(normalized_path), user_command=user_command)
        return {"status": "recording", "session": session}


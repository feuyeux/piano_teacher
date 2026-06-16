from __future__ import annotations

from pathlib import Path

from app.repositories.piece_repository import PieceRepository
from app.repositories.session_repository import SessionRepository
from app.services.midi_recording_service import MidiRecordingService
from app.utils.json_io import read_json, write_json


class ListenMockPracticeWorkflow:
    def __init__(self, score_root: str | Path, session_root: str | Path) -> None:
        self.score_root = Path(score_root)
        self.session_root = Path(session_root)
        self.piece_repo = PieceRepository(self.score_root / "piece_index.json")
        self.session_repo = SessionRepository(self.session_root)
        self.recording = MidiRecordingService(self.session_repo, self.session_root)

    def run(
        self,
        piece_id: str,
        session_id: str | None = None,
        midi_log_path: str | None = None,
        mock_mode: str = "rough",
        max_notes: int = 96,
        user_command: str | None = None,
    ) -> dict:
        piece = self.piece_repo.get_piece(piece_id)
        if not piece:
            raise ValueError(f"Piece not found: {piece_id}")
        normalized_path = self.score_root / piece_id / "normalized_score.json"
        if not normalized_path.exists():
            raise ValueError(f"Normalized score not found: {normalized_path}")

        if session_id:
            session = self.session_repo.load(session_id)
        else:
            session = self.recording.start(piece, str(normalized_path), user_command=user_command or "mock MIDI listening")
            session_id = session["session_id"]

        if not midi_log_path:
            midi_log_path = str(self._write_mock_midi(session_id, normalized_path, mock_mode, max_notes))

        session = self.recording.attach_midi_log(session_id, midi_log_path)
        return {
            "status": "mock_recording_ready_for_analysis",
            "session": session,
            "midi_log_path": midi_log_path,
            "mock_mode": mock_mode,
            "max_notes": max_notes,
        }

    def _write_mock_midi(self, session_id: str, normalized_score_path: Path, mock_mode: str, max_notes: int) -> Path:
        score = read_json(normalized_score_path)
        events = []
        for index, note in enumerate(self._playable_notes(score)[:max_notes], start=1):
            pitch = note.get("pitch_midi")
            start_ms = self._expected_start_ms(score, note)
            duration_ms = max(120, int(note.get("duration_division", 1) / max(score.get("division_unit") or 1, 1) * 500))

            if mock_mode in {"rough", "pitch_errors"} and index % 13 == 0 and pitch is not None:
                pitch += 1
            if mock_mode in {"rough", "timing_errors"} and index % 9 == 0:
                start_ms += 260
            if mock_mode == "missed_notes" and index % 11 == 0:
                continue

            events.append(
                {
                    "event_id": f"mock-event-{index}",
                    "type": "note",
                    "pitch_midi": pitch,
                    "velocity": 72,
                    "start_ms": start_ms,
                    "end_ms": start_ms + duration_ms,
                    "channel": 0,
                }
            )

        output_path = self.session_root / session_id / "mock_midi_log.json"
        write_json(
            output_path,
            {
                "session_id": session_id,
                "ticks_per_beat": None,
                "events": events,
                "mock": {
                    "mode": mock_mode,
                    "source_normalized_score_path": str(normalized_score_path),
                },
            },
        )
        return output_path

    def _playable_notes(self, score: dict) -> list[dict]:
        notes = []
        for measure in score.get("measures", []):
            for note in measure.get("notes", []):
                if not note.get("is_rest"):
                    notes.append({**note, "measure_number": measure["measure_number"]})
        return sorted(notes, key=lambda item: (item["measure_number"], item["onset_division"], item["note_id"]))

    def _expected_start_ms(self, score: dict, note: dict) -> int:
        divisions = max(int(score.get("division_unit") or 1), 1)
        return int(((note["measure_number"] - 1) * 4 + note.get("onset_division", 0) / divisions) * 500)

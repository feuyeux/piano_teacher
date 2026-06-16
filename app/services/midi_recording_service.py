from __future__ import annotations

from pathlib import Path

from app.models.practice_session import PracticeSession
from app.repositories.session_repository import SessionRepository
from app.tools.midi_recorder import MidiRecorder
from app.utils.ids import session_id
from app.utils.time_utils import utc_now


class MidiRecordingService:
    def __init__(self, repository: SessionRepository, session_root: str | Path) -> None:
        self.repository = repository
        self.session_root = Path(session_root)
        self.recorder = MidiRecorder()

    def start(self, piece: dict, normalized_score_path: str, practice_mode: str = "full_run", user_command: str | None = None) -> dict:
        now = utc_now()
        sid = session_id(piece["piece_id"])
        session = PracticeSession(
            session_id=sid,
            piece_id=piece["piece_id"],
            session_status="recording",
            started_at=now,
            ended_at=None,
            score_revision_id=piece.get("score_revision_id"),
            musicxml_snapshot_path=piece.get("primary_musicxml_path"),
            normalized_score_path=normalized_score_path,
            midi_input_device=None,
            midi_log_path=None,
            raw_event_count=0,
            tempo_target_bpm=None,
            practice_mode=practice_mode,
            section_start_measure=None,
            section_end_measure=None,
            user_command=user_command,
            analysis_status="pending",
            analysis_path=None,
            analysis_summary=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        ).to_dict()
        self.recorder.start(sid)
        self.repository.save(session)
        return session

    def attach_midi_log(self, session_id_value: str, midi_log_path: str) -> dict:
        session = self.repository.load(session_id_value)
        session["midi_log_path"] = midi_log_path
        session["session_status"] = "stopped"
        session["ended_at"] = utc_now()
        session["updated_at"] = utc_now()
        self.repository.save(session)
        return session


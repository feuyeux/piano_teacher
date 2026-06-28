from __future__ import annotations

from pathlib import Path

from app.repositories.piece_repository import PieceRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.session_repository import SessionRepository
from app.services.alignment_service import AlignmentService
from app.services.analysis_service import AnalysisService
from app.services.feedback_service import FeedbackService
from app.services.midi_parsing_service import MidiParsingService
from app.services.midi_recording_service import MidiRecordingService
from app.services.profile_service import ProfileService
from app.utils.json_io import read_json, write_json
from app.utils.time_utils import utc_now


class FinishPracticeWorkflow:
    def __init__(self, score_root: str | Path, session_root: str | Path, profile_root: str | Path) -> None:
        self.score_root = Path(score_root)
        self.session_repo = SessionRepository(session_root)
        self.recording = MidiRecordingService(self.session_repo, session_root)
        self.piece_repo = PieceRepository(self.score_root / "piece_index.json")
        self.profile_service = ProfileService(ProfileRepository(profile_root))
        self.midi_parser = MidiParsingService()
        self.alignment = AlignmentService()
        self.analysis = AnalysisService()
        self.feedback = FeedbackService()

    def run(self, session_id: str, midi_log_path: str | None = None) -> dict:
        session = self.session_repo.load(session_id)
        self.recording.stop(session_id)
        if midi_log_path:
            session["midi_log_path"] = midi_log_path
        if not session.get("midi_log_path"):
            raise ValueError("Session has no midi_log_path.")
        session["session_status"] = "analyzing"
        session["analysis_status"] = "running"
        session["updated_at"] = utc_now()
        self.session_repo.save(session)

        performance = self.midi_parser.parse(session["midi_log_path"])
        alignment = self.alignment.align(session["normalized_score_path"], performance)
        normalized_score = read_json(session["normalized_score_path"])
        expected_count = sum(1 for measure in normalized_score["measures"] for note in measure["notes"] if not note["is_rest"])
        performed_count = len([event for event in performance["events"] if event.get("type") == "note"])
        analysis = self.analysis.analyze(session["session_id"], session["piece_id"], alignment, expected_count, performed_count)
        analysis_path = self.session_repo.save_analysis(session["session_id"], analysis)
        profile = self.profile_service.update_from_analysis(session["piece_id"], analysis)
        piece = self.piece_repo.get_piece(session["piece_id"]) or {"piece_id": session["piece_id"], "title": session["piece_id"]}
        feedback = self.feedback.generate(piece, session, analysis, profile)
        write_json(Path(analysis_path).parent / "feedback.json", feedback)

        session["session_status"] = "completed"
        session["analysis_status"] = "completed"
        session["analysis_path"] = analysis_path
        session["analysis_summary"] = feedback["summary"]
        session["raw_event_count"] = performed_count
        session["ended_at"] = session.get("ended_at") or utc_now()
        session["updated_at"] = utc_now()
        self.session_repo.save(session)
        return {"status": "completed", "session": session, "analysis": analysis, "profile": profile, "feedback": feedback}

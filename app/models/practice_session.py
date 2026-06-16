from __future__ import annotations

from dataclasses import dataclass

from app.models.base import JsonModel


@dataclass
class PracticeSession(JsonModel):
    session_id: str
    piece_id: str
    session_status: str
    started_at: str
    ended_at: str | None
    score_revision_id: str | None
    musicxml_snapshot_path: str | None
    normalized_score_path: str | None
    midi_input_device: str | None
    midi_log_path: str | None
    raw_event_count: int
    tempo_target_bpm: int | None
    practice_mode: str
    section_start_measure: int | None
    section_end_measure: int | None
    user_command: str | None
    analysis_status: str
    analysis_path: str | None
    analysis_summary: str | None
    error_message: str | None
    created_at: str
    updated_at: str


from __future__ import annotations

from dataclasses import dataclass, field

from app.models.base import JsonModel


@dataclass
class PracticeAnalysis(JsonModel):
    analysis_id: str
    session_id: str
    piece_id: str
    generated_at: str
    analysis_version: str
    alignment_status: str
    aligned_note_count: int
    expected_note_count: int
    performed_note_count: int
    overall_score: float | None
    pitch_accuracy: float | None
    rhythm_accuracy: float | None
    timing_stability: float | None
    tempo_stability: float | None
    missed_notes_count: int
    extra_notes_count: int
    repeated_note_count: int
    pedal_event_count: int | None
    estimated_tempo_bpm: int | None
    best_measure_range: list[int]
    worst_measure_range: list[int]
    problem_measures: list[dict] = field(default_factory=list)
    problem_hands: dict = field(default_factory=dict)
    issue_summary_tags: list[str] = field(default_factory=list)
    recommended_focus_measures: list[int] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


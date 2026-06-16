from __future__ import annotations

from dataclasses import dataclass, field

from app.models.base import JsonModel


@dataclass
class PieceProgressProfile(JsonModel):
    piece_id: str
    stage_label: str
    practice_count: int
    total_practice_minutes: int
    last_practiced_at: str | None
    best_stable_tempo_bpm: int | None
    latest_tempo_bpm: int | None
    recent_issue_patterns: list[str] = field(default_factory=list)
    worst_measures: list[int] = field(default_factory=list)
    improving_measures: list[int] = field(default_factory=list)
    plateau_measures: list[int] = field(default_factory=list)
    last_three_scores: list[float] = field(default_factory=list)
    current_goal: str | None = None
    next_goal: str | None = None
    last_feedback_digest: str | None = None
    teacher_focus_tags: list[str] = field(default_factory=list)
    updated_at: str = ""


from __future__ import annotations

from app.models.piece_progress_profile import PieceProgressProfile
from app.repositories.profile_repository import ProfileRepository
from app.utils.time_utils import utc_now


class ProfileService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    def get_profile(self, piece_id: str) -> dict | None:
        return self.repository.get(piece_id)

    def update_from_analysis(self, piece_id: str, analysis: dict) -> dict:
        profile = self.repository.get(piece_id) or PieceProgressProfile(
            piece_id=piece_id,
            stage_label="note_learning",
            practice_count=0,
            total_practice_minutes=0,
            last_practiced_at=None,
            best_stable_tempo_bpm=None,
            latest_tempo_bpm=None,
            updated_at=utc_now(),
        ).to_dict()

        profile["practice_count"] += 1
        profile["last_practiced_at"] = utc_now()
        score = analysis.get("overall_score")
        if score is not None:
            profile["last_three_scores"] = (profile.get("last_three_scores", []) + [score])[-3:]
        profile["worst_measures"] = analysis.get("recommended_focus_measures", [])
        profile["recent_issue_patterns"] = analysis.get("issue_summary_tags", [])
        profile["next_goal"] = (analysis.get("recommended_next_steps") or [None])[0]
        profile["teacher_focus_tags"] = analysis.get("issue_summary_tags", [])
        profile["updated_at"] = utc_now()
        self.repository.save(profile)
        return profile

    def update_memory(
        self,
        piece_id: str,
        note: str | None = None,
        stage_label: str | None = None,
        current_goal: str | None = None,
        next_goal: str | None = None,
        teacher_focus_tags: list[str] | None = None,
    ) -> dict:
        profile = self.repository.get(piece_id) or PieceProgressProfile(
            piece_id=piece_id,
            stage_label=stage_label or "note_learning",
            practice_count=0,
            total_practice_minutes=0,
            last_practiced_at=None,
            best_stable_tempo_bpm=None,
            latest_tempo_bpm=None,
            updated_at=utc_now(),
        ).to_dict()
        if stage_label:
            profile["stage_label"] = stage_label
        if current_goal:
            profile["current_goal"] = current_goal
        if next_goal:
            profile["next_goal"] = next_goal
        if teacher_focus_tags is not None:
            profile["teacher_focus_tags"] = teacher_focus_tags
        if note:
            profile["last_feedback_digest"] = note
        profile["updated_at"] = utc_now()
        self.repository.save(profile)
        return profile

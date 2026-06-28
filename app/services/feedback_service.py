from __future__ import annotations

import os

from app.config import Settings
from app.agents.piano_teacher_agent import PianoTeacherAgent
from app.services.theory_knowledge_service import TheoryKnowledgeService
from app.utils.paths import project_root


class FeedbackService:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or Settings.load()
        prompt_path = project_root() / "app" / "prompts" / "practice_feedback_system_prompt.txt"
        review_command = os.getenv("PIANO_TEACHER_FEEDBACK_COMMAND") or settings.practice_feedback_command
        self.teacher = PianoTeacherAgent(prompt_path=prompt_path, review_command=review_command)
        self.theory = TheoryKnowledgeService()

    def generate(self, piece: dict, session: dict, analysis: dict, profile: dict | None) -> dict:
        return self.teacher.generate_feedback(
            {
                "piece": {
                    "piece_id": piece.get("piece_id"),
                    "title": piece.get("title"),
                    "composer": piece.get("composer"),
                    "current_stage": piece.get("current_stage"),
                },
                "session": {
                    "session_id": session.get("session_id"),
                    "practice_mode": session.get("practice_mode"),
                    "tempo_target_bpm": session.get("tempo_target_bpm"),
                },
                "analysis": analysis,
                "profile": profile,
                "theory_context": self.theory.for_practice_context(analysis),
            }
        )

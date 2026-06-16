from __future__ import annotations

from app.services.feedback_service import FeedbackService


class GenerateFeedbackWorkflow:
    def __init__(self) -> None:
        self.feedback = FeedbackService()

    def run(self, piece: dict, session: dict, analysis: dict, profile: dict | None) -> dict:
        return self.feedback.generate(piece, session, analysis, profile)


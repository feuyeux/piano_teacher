from __future__ import annotations

from pathlib import Path

from app.agents.score_import_review_agent import ScoreImportReviewAgent


class PdfToMusicXmlTool:
    def __init__(self, audiveris_command: str) -> None:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "score_import_review_system_prompt.txt"
        self.agent = ScoreImportReviewAgent(audiveris_command=audiveris_command, prompt_path=prompt_path)

    def convert_and_review(self, piece_id: str, pdf_path: str, output_dir: str) -> dict:
        return self.agent.run(piece_id=piece_id, pdf_path=pdf_path, output_dir=output_dir)

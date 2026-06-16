from __future__ import annotations

from app.tools.score_aligner import ScoreAligner
from app.utils.json_io import read_json


class AlignmentService:
    def __init__(self) -> None:
        self.aligner = ScoreAligner()

    def load_score(self, normalized_score_path: str) -> dict:
        score = read_json(normalized_score_path)
        notes = []
        for measure in score.get("measures", []):
            for note in measure.get("notes", []):
                if not note.get("is_rest"):
                    notes.append({**note, "measure_number": measure["measure_number"]})
        return {
            "piece_id": score["piece_id"],
            "score_revision_id": score["score_revision_id"],
            "measure_count": score["measure_count"],
            "notes": notes,
            "raw_score": score,
        }

    def align(self, normalized_score_path: str, performance: dict, timing_tolerance_ms: int = 180) -> dict:
        score = read_json(normalized_score_path)
        return self.aligner.align(score, performance, {"timing_tolerance_ms": timing_tolerance_ms})


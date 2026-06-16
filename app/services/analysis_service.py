from __future__ import annotations

from collections import Counter, defaultdict

from app.models.practice_analysis import PracticeAnalysis
from app.utils.time_utils import utc_now


class AnalysisService:
    def analyze(self, session_id: str, piece_id: str, alignment: dict, expected_note_count: int, performed_note_count: int) -> dict:
        matches = alignment.get("note_matches", [])
        matched = [item for item in matches if item.get("match_type") == "matched"]
        missed = [item for item in matches if item.get("match_type") == "missed"]
        extra = [item for item in matches if item.get("match_type") == "extra"]
        pitch_errors = [item for item in matches if item.get("match_type") == "pitch_error"]
        timing_errors = [item for item in matches if item.get("match_type") == "timing_error"]

        denominator = max(expected_note_count, 1)
        pitch_accuracy = max(0.0, 1.0 - (len(missed) + len(pitch_errors)) / denominator)
        rhythm_accuracy = max(0.0, 1.0 - len(timing_errors) / denominator)
        overall_score = round((pitch_accuracy * 0.65 + rhythm_accuracy * 0.35) * 100, 1)

        by_measure: dict[int, Counter] = defaultdict(Counter)
        by_measure_hand: dict[int, Counter] = defaultdict(Counter)
        hand_counts = {"left": Counter(), "right": Counter(), "unknown": Counter()}
        for item in matches:
            match_type = item.get("match_type")
            if match_type == "matched":
                continue
            measure_number = item.get("measure_number")
            if isinstance(measure_number, int):
                by_measure[measure_number][match_type] += 1
                by_measure_hand[measure_number][item.get("hand", "unknown")] += 1
            hand_counts[item.get("hand", "unknown")][match_type] += 1

        problem_measures = []
        for measure_number, counter in sorted(by_measure.items(), key=lambda pair: (-sum(pair[1].values()), pair[0]))[:8]:
            issue_tags = sorted(counter.keys())
            count = sum(counter.values())
            problem_measures.append(
                {
                    "measure_number": measure_number,
                    "severity": "high" if count >= 3 else "medium" if count >= 2 else "low",
                    "issue_tags": issue_tags,
                    "left_hand_issue_count": by_measure_hand[measure_number].get("left", 0),
                    "right_hand_issue_count": by_measure_hand[measure_number].get("right", 0),
                    "notes": ", ".join(issue_tags),
                }
            )

        recommended_focus = [item["measure_number"] for item in problem_measures[:3]]
        issue_tags = sorted({tag for item in problem_measures for tag in item["issue_tags"]})
        analysis = PracticeAnalysis(
            analysis_id=f"{session_id}-analysis",
            session_id=session_id,
            piece_id=piece_id,
            generated_at=utc_now(),
            analysis_version="0.1.0",
            alignment_status=alignment.get("alignment_status", "failed"),
            aligned_note_count=len(matched),
            expected_note_count=expected_note_count,
            performed_note_count=performed_note_count,
            overall_score=overall_score,
            pitch_accuracy=round(pitch_accuracy, 3),
            rhythm_accuracy=round(rhythm_accuracy, 3),
            timing_stability=round(rhythm_accuracy, 3),
            tempo_stability=None,
            missed_notes_count=len(missed),
            extra_notes_count=len(extra),
            repeated_note_count=0,
            pedal_event_count=None,
            estimated_tempo_bpm=None,
            best_measure_range=[],
            worst_measure_range=[recommended_focus[0], recommended_focus[0]] if recommended_focus else [],
            problem_measures=problem_measures,
            problem_hands={
                hand: {"issue_count": sum(counter.values()), "dominant_tags": [tag for tag, _ in counter.most_common(3)]}
                for hand, counter in hand_counts.items()
            },
            issue_summary_tags=issue_tags,
            recommended_focus_measures=recommended_focus,
            recommended_next_steps=self._next_steps(recommended_focus, issue_tags),
            warnings=alignment.get("warnings", []),
        )
        return analysis.to_dict()

    def _next_steps(self, measures: list[int], issue_tags: list[str]) -> list[str]:
        if not measures:
            return ["保持当前速度完整弹奏一遍，并记录是否仍能稳定。"]
        measure_text = "、".join(str(item) for item in measures)
        if "pitch_error" in issue_tags or "missed" in issue_tags:
            return [f"先分手慢练第 {measure_text} 小节，连续三遍音高无错后再合手。"]
        if "timing_error" in issue_tags:
            return [f"用节拍器慢练第 {measure_text} 小节，确认每个起音都贴住拍点。"]
        return [f"循环第 {measure_text} 小节，先稳定准确率，再考虑提速。"]

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


class PianoTeacherAgent:
    def __init__(self, prompt_path: str | Path | None = None, review_command: str | None = None) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else None
        self.review_command = review_command or os.getenv("PIANO_TEACHER_FEEDBACK_COMMAND")

    def generate_feedback(self, payload: dict) -> dict:
        if self.review_command and os.getenv("PIANO_TEACHER_USE_HERMES_SUBAGENTS") == "1":
            model_feedback = self._generate_with_command(payload)
            if model_feedback:
                return model_feedback
        return self._generate_deterministic_feedback(payload)

    def _generate_with_command(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        system_prompt = ""
        if self.prompt_path and self.prompt_path.exists():
            system_prompt = self.prompt_path.read_text(encoding="utf-8")
        request = {"system_prompt": system_prompt, "payload": payload}
        try:
            completed = subprocess.run(
                shlex.split(self.review_command),
                input=json.dumps(request, ensure_ascii=False),
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            if completed.returncode != 0:
                return None
            result = json.loads(completed.stdout)
        except Exception:
            return None
        required = {"summary", "key_issues", "practice_plan", "progress_note", "next_focus", "confidence"}
        if required.issubset(result.keys()):
            return result
        return None

    def _generate_deterministic_feedback(self, payload: dict) -> dict:
        analysis = payload["analysis"]
        profile = payload.get("profile") or {}
        piece = payload.get("piece") or {}
        score = analysis.get("overall_score")
        warnings = analysis.get("warnings", [])
        problem_measures = analysis.get("problem_measures", [])[:3]

        if problem_measures:
            first = problem_measures[0]
            summary = f"这次《{piece.get('title', piece.get('piece_id', '这首曲子'))}》最需要处理的是第 {first['measure_number']} 小节附近的问题。"
        else:
            summary = f"这次《{piece.get('title', piece.get('piece_id', '这首曲子'))}》整体比较稳定。"
        if score is not None:
            summary += f" 结构化评分为 {score}。"

        key_issues = [
            {
                "title": "小节问题",
                "measure_range": str(item["measure_number"]),
                "description": f"检测到 {', '.join(item.get('issue_tags', []))}，严重程度 {item.get('severity')}。",
            }
            for item in problem_measures
        ]
        practice_plan = [
            {"step": step, "target": "连续三遍稳定后再进入下一步"}
            for step in (analysis.get("recommended_next_steps") or ["完整弹奏一遍并保持稳定速度。"])[:3]
        ]
        return {
            "summary": summary,
            "key_issues": key_issues,
            "practice_plan": practice_plan,
            "progress_note": self._progress_note(profile),
            "next_focus": (analysis.get("recommended_next_steps") or [None])[0],
            "confidence": "medium" if warnings else "high",
        }

    def _progress_note(self, profile: dict) -> str | None:
        scores = profile.get("last_three_scores") or []
        if len(scores) < 2:
            return None
        if scores[-1] > scores[-2]:
            return "比上一次更稳定，可以在保持准确的前提下小幅提速。"
        return "最近问题还没有明显消退，先不要急着提速。"

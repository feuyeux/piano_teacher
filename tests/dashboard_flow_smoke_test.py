from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.conductor_agent import ConductorAgent


def main() -> int:
    agent = ConductorAgent()
    piece_id = "minimal-piano-fixture"

    prepared = agent.handle_command("prepare_piece", piece_id=piece_id)
    assert prepared["status"] == "prepared"
    assert prepared["normalized"]["normalized_score"]["measure_count"] >= 1

    memory = agent.handle_command(
        "update_teacher_memory",
        piece_id=piece_id,
        note="Dashboard smoke test memory note.",
        current_goal="mock dashboard practice",
        teacher_focus_tags=["dashboard", "mock_midi"],
    )
    assert memory["status"] == "memory_updated"
    assert memory["profile"]["current_goal"] == "mock dashboard practice"

    listened = agent.handle_command(
        "listen_mock_practice",
        piece_id=piece_id,
        mock_mode="rough",
        max_notes=32,
        user_command="dashboard smoke test",
    )
    assert listened["status"] == "completed"
    assert listened["analysis"]["overall_score"] is not None
    assert listened["feedback"]["summary"]

    print(
        json.dumps(
            {
                "status": "ok",
                "piece_id": listened["session"]["piece_id"],
                "session_id": listened["session"]["session_id"],
                "score": listened["analysis"]["overall_score"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

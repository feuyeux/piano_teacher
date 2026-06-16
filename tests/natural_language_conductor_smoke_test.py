from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_command(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "app.main", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> int:
    prepared = run_command("ask", "准备 minimal-piano-fixture")
    assert prepared["status"] == "prepared"

    started = run_command("ask", "开始练习 minimal-piano-fixture")
    assert started["status"] == "recording"
    assert started["session"]["session_id"]

    midi_log_path = str(ROOT / "scores" / "minimal-piano-fixture" / "performance_fixture.json")
    finished = run_command("ask", f"结束 minimal-piano-fixture 练习，midi 在 {midi_log_path}")
    assert finished["status"] == "completed"
    assert finished["session"]["session_id"] == started["session"]["session_id"]
    assert finished["analysis"]["overall_score"] is not None
    assert finished["feedback"]["summary"]

    listened = run_command("ask", "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式")
    assert listened["status"] == "completed"
    assert listened["analysis"]["overall_score"] is not None
    assert listened["feedback"]["summary"]

    progress = run_command("ask", "查看 minimal-piano-fixture 的学习进度和计划")
    assert progress["status"] == "found"
    assert progress["profile"]["practice_count"] >= 1

    memory = run_command(
        "ask",
        "请记住 minimal-piano-fixture：目标是慢速稳定，下次目标是保持当前速度完整弹奏，重点关注 left_hand timing",
    )
    assert memory["status"] == "memory_updated"
    assert memory["profile"]["current_goal"] == "慢速稳定"
    assert memory["profile"]["next_goal"] == "保持当前速度完整弹奏"
    assert memory["profile"]["teacher_focus_tags"] == ["left_hand", "timing"]

    library = run_command("ask", "列出曲库里有哪些曲子")
    assert library["status"] == "completed"
    assert library["piece_count"] >= 1

    help_result = run_command("ask", "你能做什么")
    assert help_result["status"] == "help"
    assert "更新老师记忆/profile" in help_result["capabilities"]

    print(
        json.dumps(
            {
                "status": "ok",
                "session_id": listened["session"]["session_id"],
                "score": listened["analysis"]["overall_score"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

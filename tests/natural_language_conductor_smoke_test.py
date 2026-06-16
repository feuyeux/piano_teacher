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

    listened = run_command("ask", "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式")
    assert listened["status"] == "completed"
    assert listened["analysis"]["overall_score"] is not None
    assert listened["feedback"]["summary"]

    progress = run_command("ask", "查看 minimal-piano-fixture 的学习进度和计划")
    assert progress["status"] == "found"
    assert progress["profile"]["practice_count"] >= 1

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

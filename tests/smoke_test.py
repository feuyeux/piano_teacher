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
    refreshed = run_command("refresh-library")
    assert refreshed["piece_count"] >= 1

    normalized = run_command("normalize-score", "minimal-piano-fixture")
    assert normalized["normalized_score"]["measure_count"] == 1

    started = run_command("start-practice", "minimal-piano-fixture")
    session_id = started["session"]["session_id"]

    midi_log_path = str(ROOT / "scores" / "minimal-piano-fixture" / "performance_fixture.json")
    finished = run_command("finish-practice", session_id, "--midi-log-path", midi_log_path)
    assert finished["analysis"]["overall_score"] is not None
    assert finished["feedback"]["summary"]
    print(json.dumps({"status": "ok", "session_id": session_id, "score": finished["analysis"]["overall_score"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

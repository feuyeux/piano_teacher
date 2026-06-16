from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def frame(message: dict) -> bytes:
    data = json.dumps(message).encode("utf-8")
    return f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data


def read_frame(stream) -> dict:
    headers = {}
    while True:
        line = stream.readline()
        if line in {b"\r\n", b"\n"}:
            break
        key, _, value = line.decode("ascii").partition(":")
        headers[key.lower()] = value.strip()
    data = stream.read(int(headers["content-length"]))
    return json.loads(data.decode("utf-8"))


def main() -> int:
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.mcp_server"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin and proc.stdout
    proc.stdin.write(frame({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    proc.stdin.flush()
    initialized = read_frame(proc.stdout)
    assert initialized["result"]["serverInfo"]["name"] == "piano-teacher"

    proc.stdin.write(frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}))
    proc.stdin.flush()
    tools = read_frame(proc.stdout)
    names = {tool["name"] for tool in tools["result"]["tools"]}
    assert {"refresh_library", "normalize_score", "start_practice", "finish_practice"} <= names
    proc.terminate()
    proc.wait(timeout=5)
    print(json.dumps({"status": "ok", "tools": sorted(names)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

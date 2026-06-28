from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from app.utils.json_io import read_json, write_json
from app.utils.paths import project_root


class MidiRecorder:
    def list_input_devices(self) -> list[str]:
        command = [sys.executable, "-m", "app.tools.midi_recorder", "list-devices"]
        env = os.environ.copy()
        root = str(project_root())
        env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                env=env,
                capture_output=True,
                check=True,
                text=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []
        try:
            data = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return []
        return data.get("devices") or []

    def _list_input_devices_in_process(self) -> list[str]:
        try:
            import mido
        except ImportError:
            return []
        return list(mido.get_input_names())

    def start(
        self,
        session_id: str,
        midi_log_path: str | Path,
        midi_device: str | None = None,
        state_path: str | Path | None = None,
    ) -> dict:
        devices = self.list_input_devices()
        selected_device = self._select_device(devices, midi_device)
        if not selected_device:
            return {
                "session_id": session_id,
                "status": "no_midi_device",
                "midi_device": None,
                "midi_log_path": None,
                "available_devices": devices,
            }

        log_path = Path(midi_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        state = Path(state_path) if state_path else log_path.with_name("midi_recorder_state.json")
        stderr_path = log_path.with_name("midi_recorder.log")
        command = [
            sys.executable,
            "-m",
            "app.tools.midi_recorder",
            "record",
            "--session-id",
            session_id,
            "--output",
            str(log_path),
            "--device",
            selected_device,
        ]
        env = os.environ.copy()
        root = str(project_root())
        env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        with stderr_path.open("a", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                command,
                cwd=root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                start_new_session=True,
            )
        write_json(
            state,
            {
                "session_id": session_id,
                "pid": process.pid,
                "midi_device": selected_device,
                "midi_log_path": str(log_path),
                "started_at_ms": int(time.time() * 1000),
            },
        )
        return {
            "session_id": session_id,
            "status": "recording",
            "midi_device": selected_device,
            "midi_log_path": str(log_path),
            "available_devices": devices,
            "pid": process.pid,
        }

    def stop(self, session_id: str, state_path: str | Path) -> dict:
        state = Path(state_path)
        if not state.exists():
            return {"session_id": session_id, "status": "not_running"}
        data = read_json(state)
        pid = data.get("pid")
        if pid:
            try:
                os.kill(int(pid), signal.SIGTERM)
                time.sleep(0.3)
            except ProcessLookupError:
                pass
            except PermissionError:
                return {"session_id": session_id, "status": "stop_failed", "error": "permission_denied"}
        return {
            "session_id": session_id,
            "status": "stopped",
            "midi_device": data.get("midi_device"),
            "midi_log_path": data.get("midi_log_path"),
        }

    def _select_device(self, devices: list[str], preferred: str | None) -> str | None:
        if not devices:
            return None
        if not preferred:
            return devices[0]
        for device in devices:
            if device == preferred:
                return device
        preferred_lower = preferred.lower()
        for device in devices:
            if preferred_lower in device.lower():
                return device
        return None


def record_forever(session_id: str, output: str, device: str) -> None:
    import mido

    started_at = time.monotonic()
    events: list[dict[str, Any]] = []
    active_notes: dict[tuple[int, int], dict[str, int]] = {}
    stopped = False

    def elapsed_ms() -> int:
        return int((time.monotonic() - started_at) * 1000)

    def save() -> None:
        write_json(
            output,
            {
                "session_id": session_id,
                "ticks_per_beat": None,
                "source": "live_midi",
                "midi_input_device": device,
                "events": events,
            },
        )

    def handle_stop(signum, frame) -> None:  # noqa: ANN001
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    save()
    with mido.open_input(device) as port:
        while not stopped:
            for message in port.iter_pending():
                channel = getattr(message, "channel", None)
                note = getattr(message, "note", None)
                velocity = getattr(message, "velocity", 0)
                if message.type == "note_on" and velocity > 0 and note is not None:
                    active_notes[(channel or 0, note)] = {"start_ms": elapsed_ms(), "velocity": int(velocity)}
                elif message.type in {"note_off", "note_on"} and note is not None:
                    key = (channel or 0, note)
                    start = active_notes.pop(key, None)
                    if start:
                        events.append(
                            {
                                "event_id": f"event-{len(events) + 1}",
                                "type": "note",
                                "pitch_midi": int(note),
                                "velocity": start["velocity"],
                                "start_ms": start["start_ms"],
                                "end_ms": elapsed_ms(),
                                "channel": channel,
                            }
                        )
                        save()
            time.sleep(0.01)
    now = elapsed_ms()
    for (channel, note), start in list(active_notes.items()):
        events.append(
            {
                "event_id": f"event-{len(events) + 1}",
                "type": "note",
                "pitch_midi": int(note),
                "velocity": start["velocity"],
                "start_ms": start["start_ms"],
                "end_ms": now,
                "channel": channel,
            }
        )
    save()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Background MIDI JSON recorder.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("list-devices")
    record = subcommands.add_parser("record")
    record.add_argument("--session-id", required=True)
    record.add_argument("--output", required=True)
    record.add_argument("--device", required=True)
    args = parser.parse_args(argv)
    if args.command == "list-devices":
        print(json.dumps({"devices": MidiRecorder()._list_input_devices_in_process()}, ensure_ascii=False))
        return 0
    if args.command == "record":
        record_forever(args.session_id, args.output, args.device)
        return 0
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

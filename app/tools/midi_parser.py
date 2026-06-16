from __future__ import annotations

from pathlib import Path

from app.utils.json_io import read_json


class MidiParser:
    """First-pass parser for a JSON MIDI event fixture.

    Real .mid parsing will be swapped in later; this keeps the interface stable
    while the project skeleton is being validated.
    """

    def parse(self, midi_log_path: str | Path) -> dict:
        data = read_json(midi_log_path)
        events = data.get("events", [])
        for index, event in enumerate(events, start=1):
            event.setdefault("event_id", f"event-{index}")
            event.setdefault("type", "note")
            event.setdefault("channel", None)
        return {
            "session_id": data.get("session_id", Path(midi_log_path).stem),
            "ticks_per_beat": data.get("ticks_per_beat"),
            "events": events,
        }


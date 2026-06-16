from __future__ import annotations


class MidiRecorder:
    def start(self, session_id: str, midi_device: str | None = None) -> dict:
        return {"session_id": session_id, "status": "recording", "midi_device": midi_device}

    def stop(self, session_id: str) -> dict:
        return {"session_id": session_id, "status": "stopped"}


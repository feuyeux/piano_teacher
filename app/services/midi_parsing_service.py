from __future__ import annotations

from app.tools.midi_parser import MidiParser


class MidiParsingService:
    def __init__(self) -> None:
        self.parser = MidiParser()

    def parse(self, midi_log_path: str) -> dict:
        return self.parser.parse(midi_log_path)


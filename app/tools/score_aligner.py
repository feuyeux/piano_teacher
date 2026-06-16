from __future__ import annotations


class ScoreAligner:
    def align(self, score: dict, performance: dict, options: dict | None = None) -> dict:
        options = options or {}
        timing_tolerance_ms = int(options.get("timing_tolerance_ms", 180))
        score_notes = self._playable_notes(score)
        events = [event for event in performance.get("events", []) if event.get("type") == "note"]
        note_matches = []
        used_events: set[str] = set()

        for index, score_note in enumerate(score_notes):
            event = events[index] if index < len(events) else None
            if event is None:
                note_matches.append(self._match(score_note, None, "missed"))
                continue

            used_events.add(event["event_id"])
            expected_pitch = score_note.get("pitch_midi")
            performed_pitch = event.get("pitch_midi")
            timing_offset = self._expected_start_ms(score, score_note) - int(event.get("start_ms", 0))

            if expected_pitch != performed_pitch:
                match_type = "pitch_error"
            elif abs(timing_offset) > timing_tolerance_ms:
                match_type = "timing_error"
            else:
                match_type = "matched"
            note_matches.append(self._match(score_note, event, match_type, timing_offset))

        extra_events = [event["event_id"] for event in events if event["event_id"] not in used_events]
        for event in events[len(score_notes):]:
            note_matches.append(
                {
                    "score_note_id": None,
                    "event_id": event["event_id"],
                    "measure_number": None,
                    "hand": "unknown",
                    "expected_pitch_midi": None,
                    "performed_pitch_midi": event.get("pitch_midi"),
                    "timing_offset_ms": None,
                    "duration_offset_ms": None,
                    "match_type": "extra",
                }
            )

        status = "completed"
        warnings = []
        if len(events) < len(score_notes):
            status = "partial"
            warnings.append("Performance has fewer notes than the score.")
        return {"alignment_status": status, "note_matches": note_matches, "extra_events": extra_events, "warnings": warnings}

    def _playable_notes(self, score: dict) -> list[dict]:
        notes = []
        for measure in score.get("measures", []):
            for note in measure.get("notes", []):
                if not note.get("is_rest"):
                    notes.append({**note, "measure_number": measure["measure_number"]})
        return sorted(notes, key=lambda item: (item["measure_number"], item["onset_division"], item["note_id"]))

    def _expected_start_ms(self, score: dict, note: dict) -> int:
        divisions = max(int(score.get("division_unit") or 1), 1)
        # First version assumes 120 bpm, quarter note = 500 ms.
        return int(((note["measure_number"] - 1) * 4 + note.get("onset_division", 0) / divisions) * 500)

    def _match(self, score_note: dict, event: dict | None, match_type: str, timing_offset: int | None = None) -> dict:
        return {
            "score_note_id": score_note.get("note_id"),
            "event_id": event.get("event_id") if event else None,
            "measure_number": score_note.get("measure_number"),
            "hand": score_note.get("hand", "unknown"),
            "expected_pitch_midi": score_note.get("pitch_midi"),
            "performed_pitch_midi": event.get("pitch_midi") if event else None,
            "timing_offset_ms": timing_offset,
            "duration_offset_ms": None,
            "match_type": match_type,
        }


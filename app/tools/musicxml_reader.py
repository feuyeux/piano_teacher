from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from app.models.normalized_score import NormalizedScore
from app.utils.ids import file_hash
from app.utils.time_utils import utc_now


NS = {"m": "http://www.musicxml.org/ns/musicxml"}
STEP_TO_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


class MusicXmlReader:
    def normalize(self, piece_id: str, musicxml_path: str | Path) -> dict:
        source = Path(musicxml_path).resolve()
        root = self._load_root(source)
        title = self._text(root, ".//m:work-title", ".//work-title") or source.stem
        composer = self._creator(root, "composer")
        divisions = int(self._text(root, ".//m:divisions", ".//divisions") or "1")
        time_signature = self._time_signature(root)
        key_signature = self._text(root, ".//m:key/m:fifths", ".//key/fifths")

        measures = []
        for measure_index, measure in enumerate(self._findall(root, ".//m:measure", ".//measure"), start=1):
            measure_number = int(measure.attrib.get("number", measure_index)) if measure.attrib.get("number", str(measure_index)).isdigit() else measure_index
            onset_by_voice: dict[str, int] = {}
            notes = []
            chord_index = 0
            for note_index, note in enumerate(self._findall(note := measure, "m:note", "note"), start=1):
                voice = self._text(note, "m:voice", "voice") or "1"
                duration = int(self._text(note, "m:duration", "duration") or "0")
                is_chord = self._find(note, "m:chord", "chord") is not None
                onset = onset_by_voice.get(voice, 0)
                if is_chord:
                    chord_index += 1
                pitch_midi, pitch_name = self._pitch(note)
                staff = self._text(note, "m:staff", "staff")
                notes.append(
                    {
                        "note_id": f"{piece_id}-m{measure_number}-n{note_index}",
                        "pitch_midi": pitch_midi,
                        "pitch_name": pitch_name,
                        "voice": int(voice) if voice.isdigit() else None,
                        "staff": staff,
                        "hand": self._hand_from_staff(staff),
                        "is_rest": self._find(note, "m:rest", "rest") is not None,
                        "onset_division": onset,
                        "duration_division": duration,
                        "tie_start": self._has_tie(note, "start"),
                        "tie_stop": self._has_tie(note, "stop"),
                        "chord_index": chord_index if is_chord else None,
                    }
                )
                if not is_chord:
                    onset_by_voice[voice] = onset + duration
            measures.append({"measure_number": measure_number, "beats": None, "beat_unit": None, "notes": notes})

        score = NormalizedScore(
            piece_id=piece_id,
            score_revision_id=file_hash(source),
            title=title,
            composer=composer,
            time_signature=time_signature,
            key_signature=key_signature,
            default_tempo_bpm=None,
            division_unit=divisions,
            measure_count=len(measures),
            measures=measures,
            created_at=utc_now(),
        )
        return score.to_dict()

    def _load_root(self, source: Path) -> ET.Element:
        if source.suffix.lower() == ".mxl":
            with zipfile.ZipFile(source) as archive:
                names = [name for name in archive.namelist() if name.endswith((".xml", ".musicxml"))]
                score_names = [name for name in names if not name.upper().startswith("META-INF/")]
                if not score_names:
                    raise ValueError("compressed MusicXML contains no score XML")
                with archive.open(score_names[0]) as file:
                    return ET.parse(file).getroot()
        return ET.parse(source).getroot()

    def _pitch(self, note: ET.Element) -> tuple[int | None, str | None]:
        pitch = self._find(note, "m:pitch", "pitch")
        if pitch is None:
            return None, None
        step = self._text(pitch, "m:step", "step")
        octave = self._text(pitch, "m:octave", "octave")
        alter = int(self._text(pitch, "m:alter", "alter") or "0")
        if step is None or octave is None:
            return None, None
        midi = (int(octave) + 1) * 12 + STEP_TO_SEMITONE[step] + alter
        accidental = "#" if alter == 1 else "b" if alter == -1 else ""
        return midi, f"{step}{accidental}{octave}"

    def _creator(self, root: ET.Element, creator_type: str) -> str | None:
        for creator in self._findall(root, ".//m:creator", ".//creator"):
            if creator.attrib.get("type") == creator_type and creator.text:
                return creator.text.strip()
        return None

    def _time_signature(self, root: ET.Element) -> str | None:
        beats = self._text(root, ".//m:time/m:beats", ".//time/beats")
        beat_type = self._text(root, ".//m:time/m:beat-type", ".//time/beat-type")
        return f"{beats}/{beat_type}" if beats and beat_type else None

    def _has_tie(self, note: ET.Element, tie_type: str) -> bool:
        for tie in self._findall(note, "m:tie", "tie"):
            if tie.attrib.get("type") == tie_type:
                return True
        return False

    def _hand_from_staff(self, staff: str | None) -> str:
        if staff == "1":
            return "right"
        if staff == "2":
            return "left"
        return "unknown"

    def _findall(self, root: ET.Element, namespaced: str, plain: str) -> list[ET.Element]:
        found = root.findall(namespaced, NS)
        return found or root.findall(plain)

    def _find(self, root: ET.Element, namespaced: str, plain: str) -> ET.Element | None:
        element = root.find(namespaced, NS)
        if element is not None:
            return element
        return root.find(plain)

    def _text(self, root: ET.Element, namespaced: str, plain: str | None = None) -> str | None:
        element = root.find(namespaced, NS)
        if element is None and plain:
            element = root.find(plain)
        return element.text.strip() if element is not None and element.text else None


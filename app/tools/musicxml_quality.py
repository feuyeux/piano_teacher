from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"m": "http://www.musicxml.org/ns/musicxml"}


@dataclass
class MusicXmlQualityReport:
    validation_status: str
    path: str
    title: str | None
    composer: str | None
    part_count: int
    measure_count: int
    note_count: int
    rest_count: int
    chord_note_count: int
    staff_values: list[int]
    voice_values: list[str]
    time_signatures: list[str]
    key_signatures: list[str]
    warnings: list[str]
    review_hints: list[str]

    def to_dict(self) -> dict:
        return {
            "validation_status": self.validation_status,
            "path": self.path,
            "title": self.title,
            "composer": self.composer,
            "part_count": self.part_count,
            "measure_count": self.measure_count,
            "note_count": self.note_count,
            "rest_count": self.rest_count,
            "chord_note_count": self.chord_note_count,
            "staff_values": self.staff_values,
            "voice_values": self.voice_values,
            "time_signatures": self.time_signatures,
            "key_signatures": self.key_signatures,
            "warnings": self.warnings,
            "review_hints": self.review_hints,
        }


class MusicXmlQualityAnalyzer:
    def analyze(self, path: str | Path) -> MusicXmlQualityReport:
        source = Path(path).resolve()
        warnings: list[str] = []
        review_hints: list[str] = []

        try:
            root = self._load_root(source)
        except Exception as exc:
            return MusicXmlQualityReport(
                validation_status="invalid",
                path=str(source),
                title=None,
                composer=None,
                part_count=0,
                measure_count=0,
                note_count=0,
                rest_count=0,
                chord_note_count=0,
                staff_values=[],
                voice_values=[],
                time_signatures=[],
                key_signatures=[],
                warnings=[f"Could not parse MusicXML: {exc}"],
                review_hints=["The converted file is not parseable; rerun OMR or inspect export settings."],
            )

        title = self._text(root, ".//m:work-title") or self._text(root, ".//work-title")
        composer = self._creator(root, "composer")
        parts = self._findall(root, ".//m:part", ".//part")
        measures = self._findall(root, ".//m:measure", ".//measure")
        notes = self._findall(root, ".//m:note", ".//note")
        rest_count = sum(1 for note in notes if self._find(note, "m:rest", "rest") is not None)
        chord_note_count = sum(1 for note in notes if self._find(note, "m:chord", "chord") is not None)
        staff_values = sorted({int(text) for text in self._texts(root, ".//m:staff", ".//staff") if text.isdigit()})
        voice_values = sorted({text for text in self._texts(root, ".//m:voice", ".//voice") if text})
        time_signatures = sorted(
            {
                f"{beats}/{beat_type}"
                for beats, beat_type in self._time_signature_pairs(root)
                if beats and beat_type
            }
        )
        key_signatures = sorted({text for text in self._texts(root, ".//m:key/m:fifths", ".//key/fifths") if text})

        if not measures:
            warnings.append("No measures were found.")
        if not notes:
            warnings.append("No notes were found.")
        if len(parts) == 0:
            warnings.append("No score parts were found.")
        if len(staff_values) < 2:
            review_hints.append("Piano grand-staff mapping may be missing or collapsed into one staff.")
        if len(voice_values) > 6:
            review_hints.append("Many voices were detected; inspect voice assignment and hidden rests.")
        if chord_note_count == 0 and len(notes) > 80:
            review_hints.append("No chord notes were detected in a non-trivial score; check whether vertical harmony was flattened.")
        if len(time_signatures) > 3:
            review_hints.append("Many time signatures were detected; inspect false meter changes.")
        if len(key_signatures) > 4:
            review_hints.append("Many key signatures were detected; inspect false key changes.")
        if notes and measures and len(notes) / len(measures) < 1.5:
            review_hints.append("Very few notes per measure; possible missed notation.")

        validation_status = "valid"
        if warnings:
            validation_status = "invalid"
        elif review_hints:
            validation_status = "warning"

        return MusicXmlQualityReport(
            validation_status=validation_status,
            path=str(source),
            title=title,
            composer=composer,
            part_count=len(parts),
            measure_count=len(measures),
            note_count=len(notes),
            rest_count=rest_count,
            chord_note_count=chord_note_count,
            staff_values=staff_values,
            voice_values=voice_values[:20],
            time_signatures=time_signatures,
            key_signatures=key_signatures,
            warnings=warnings,
            review_hints=review_hints,
        )

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

    def _creator(self, root: ET.Element, creator_type: str) -> str | None:
        for creator in self._findall(root, ".//m:creator", ".//creator"):
            if creator.attrib.get("type") == creator_type and creator.text:
                return creator.text.strip()
        return None

    def _time_signature_pairs(self, root: ET.Element) -> list[tuple[str | None, str | None]]:
        pairs = []
        for time in self._findall(root, ".//m:time", ".//time"):
            pairs.append((self._text(time, "m:beats") or self._text(time, "beats"), self._text(time, "m:beat-type") or self._text(time, "beat-type")))
        return pairs

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

    def _texts(self, root: ET.Element, namespaced: str, plain: str) -> list[str]:
        elements = root.findall(namespaced, NS) or root.findall(plain)
        return [element.text.strip() for element in elements if element.text]

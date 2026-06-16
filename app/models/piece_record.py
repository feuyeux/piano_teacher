from __future__ import annotations

from dataclasses import dataclass, field

from app.models.base import JsonModel


@dataclass
class PieceRecord(JsonModel):
    piece_id: str
    title: str
    composer: str | None
    aliases: list[str]
    source_dir: str
    primary_musicxml_path: str | None
    pdf_paths: list[str]
    musicxml_paths: list[str]
    score_source_type: str | None
    score_revision_id: str | None
    converted_from_pdf: bool
    conversion_status: str
    validation_status: str
    arrangement_note: str | None
    difficulty_level: str | None
    measure_count: int | None
    part_count: int | None
    has_piano_hands_mapping: bool
    last_practiced_at: str | None
    practice_count: int
    current_stage: str
    known_issues: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


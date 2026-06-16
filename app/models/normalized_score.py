from __future__ import annotations

from dataclasses import dataclass, field

from app.models.base import JsonModel


@dataclass
class NormalizedScore(JsonModel):
    piece_id: str
    score_revision_id: str
    title: str
    composer: str | None
    time_signature: str | None
    key_signature: str | None
    default_tempo_bpm: int | None
    division_unit: int
    measure_count: int
    measures: list[dict] = field(default_factory=list)
    created_at: str = ""


from __future__ import annotations

from pathlib import Path

from app.models.piece_record import PieceRecord
from app.repositories.piece_repository import PieceRepository
from app.tools.musicxml_quality import MusicXmlQualityAnalyzer
from app.utils.paths import relative_to_project, slugify
from app.utils.time_utils import utc_now


class ScoreLibraryService:
    def __init__(self, library_root: str | Path, repository: PieceRepository) -> None:
        self.library_root = Path(library_root)
        self.repository = repository
        self.quality = MusicXmlQualityAnalyzer()

    def refresh_index(self) -> list[dict]:
        pieces = self.scan_library()
        self.repository.save_all(pieces)
        return pieces

    def scan_library(self) -> list[dict]:
        self.library_root.mkdir(parents=True, exist_ok=True)
        grouped: dict[str, dict[str, list[Path]]] = {}
        for path in self.library_root.rglob("*"):
            if path.is_dir():
                continue
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".xml", ".musicxml", ".mxl"}:
                continue
            piece_id = slugify(path.parent.name if path.parent != self.library_root else path.stem)
            grouped.setdefault(piece_id, {"pdf": [], "musicxml": []})
            if suffix == ".pdf":
                grouped[piece_id]["pdf"].append(path)
            else:
                grouped[piece_id]["musicxml"].append(path)

        now = utc_now()
        records = []
        for piece_id, files in sorted(grouped.items()):
            musicxml_paths = sorted(files["musicxml"])
            pdf_paths = sorted(files["pdf"])
            primary = musicxml_paths[0] if musicxml_paths else None
            quality_report = self.quality.analyze(primary) if primary else None
            record = PieceRecord(
                piece_id=piece_id,
                title=quality_report.title if quality_report and quality_report.title else piece_id.replace("-", " ").title(),
                composer=quality_report.composer if quality_report else None,
                aliases=[],
                source_dir=relative_to_project(primary.parent if primary else (pdf_paths[0].parent if pdf_paths else self.library_root)),
                primary_musicxml_path=relative_to_project(primary) if primary else None,
                pdf_paths=[relative_to_project(path) for path in pdf_paths],
                musicxml_paths=[relative_to_project(path) for path in musicxml_paths],
                score_source_type="musicxml" if primary else None,
                score_revision_id=None,
                converted_from_pdf=False,
                conversion_status="not_needed" if primary else "pending",
                validation_status=quality_report.validation_status if quality_report else "warning",
                arrangement_note=None,
                difficulty_level=None,
                measure_count=quality_report.measure_count if quality_report else None,
                part_count=quality_report.part_count if quality_report else None,
                has_piano_hands_mapping=bool(quality_report and len(quality_report.staff_values) >= 2),
                last_practiced_at=None,
                practice_count=0,
                current_stage="new_piece",
                known_issues=quality_report.review_hints if quality_report else ["missing_musicxml"],
                created_at=now,
                updated_at=now,
            )
            records.append(record.to_dict())
        return records

    def get_piece(self, piece_id: str) -> dict | None:
        return self.repository.get_piece(piece_id)


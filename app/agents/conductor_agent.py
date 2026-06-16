from __future__ import annotations

import os
from pathlib import Path

from app.config import Settings
from app.agents.score_import_review_agent import ScoreImportReviewAgent
from app.workflows.finish_practice_workflow import FinishPracticeWorkflow
from app.workflows.listen_mock_practice_workflow import ListenMockPracticeWorkflow
from app.workflows.normalize_score_workflow import NormalizeScoreWorkflow
from app.workflows.refresh_library_workflow import RefreshLibraryWorkflow
from app.workflows.start_practice_workflow import StartPracticeWorkflow
from app.repositories.profile_repository import ProfileRepository
from app.repositories.piece_repository import PieceRepository
from app.repositories.session_repository import SessionRepository
from app.services.profile_service import ProfileService
from app.utils.paths import project_root, slugify


class ConductorAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()
        self.score_root = self.settings.resolve(self.settings.score_library_path)
        self.session_root = self.settings.resolve(self.settings.session_output_path)
        self.profile_root = self.settings.resolve(self.settings.profile_output_path)
        self.piece_repo = PieceRepository(self.score_root / "piece_index.json")
        self.session_repo = SessionRepository(self.session_root)

    def handle_natural_language(self, text: str) -> dict:
        lowered = text.lower()
        piece_id = self._detect_piece_id(text)

        if self._has_any(lowered, ["review", "复核", "检查", "导入"]) and self._has_any(lowered, ["pdf", "musicxml", "mxl", "琴谱", "谱"]):
            source_path = self._extract_path(text)
            if not source_path:
                raise ValueError("请在请求中提供 PDF 或 MusicXML 路径。")
            key = "pdf_path" if source_path.lower().endswith(".pdf") else "musicxml_path"
            return self.handle_command("review_score_import", **{key: source_path}, piece_id=piece_id)

        if self._has_any(lowered, ["prepare", "准备", "标准化", "normalize"]):
            if not piece_id:
                raise ValueError("请指定要准备的 piece_id 或曲名。")
            return self.handle_command("prepare_piece", piece_id=piece_id)

        if self._has_any(lowered, ["refresh", "刷新", "更新曲库"]):
            return self.handle_command("refresh_library")

        if self._has_any(lowered, ["memory", "进度", "画像", "成果", "计划"]) and self._has_any(lowered, ["show", "查看", "读取", "看"]):
            if not piece_id:
                raise ValueError("请指定要查看的 piece_id 或曲名。")
            return self.handle_command("get_teacher_memory", piece_id=piece_id)

        if self._has_any(lowered, ["结束", "finish", "stop", "完成"]):
            session = self._latest_session(piece_id, {"recording", "stopped"})
            midi_log_path = self._extract_path(text)
            if not session:
                raise ValueError("没有找到可结束的练习会话。")
            return self.handle_command("finish_practice", session_id=session["session_id"], midi_log_path=midi_log_path)

        if self._has_any(lowered, ["mock", "模拟", "听我", "listen"]):
            if not piece_id:
                raise ValueError("请指定要练习的 piece_id 或曲名。")
            return self.handle_command(
                "listen_mock_practice",
                piece_id=piece_id,
                mock_mode=self._detect_mock_mode(lowered),
                max_notes=self._detect_max_notes(lowered),
                user_command=text,
            )

        if self._has_any(lowered, ["开始", "start", "练习", "practice"]):
            if not piece_id:
                raise ValueError("请指定要练习的 piece_id 或曲名。")
            return self.handle_command("start_practice", piece_id=piece_id, user_command=text)

        return {
            "status": "needs_clarification",
            "message": "我可以处理：开始练习、结束练习、模拟听练习、准备曲目、复核 PDF/MusicXML、查看学习进度。",
            "detected_piece_id": piece_id,
        }

    def handle_command(self, command: str, **kwargs) -> dict:
        if command == "refresh_library":
            return RefreshLibraryWorkflow(self.score_root).run()
        if command == "normalize_score":
            return NormalizeScoreWorkflow(self.score_root).run(kwargs["piece_id"])
        if command == "prepare_piece":
            refreshed = RefreshLibraryWorkflow(self.score_root).run()
            piece_id = kwargs.get("piece_id")
            if not piece_id:
                return {"status": "library_refreshed", "library": refreshed}
            normalized = NormalizeScoreWorkflow(self.score_root).run(piece_id)
            return {"status": "prepared", "library": refreshed, "normalized": normalized}
        if command == "start_practice":
            return StartPracticeWorkflow(self.score_root, self.session_root).run(kwargs["piece_id"], kwargs.get("user_command"))
        if command == "finish_practice":
            return FinishPracticeWorkflow(self.score_root, self.session_root, self.profile_root).run(kwargs["session_id"], kwargs.get("midi_log_path"))
        if command == "listen_mock_practice":
            listened = ListenMockPracticeWorkflow(self.score_root, self.session_root).run(
                piece_id=kwargs["piece_id"],
                session_id=kwargs.get("session_id"),
                midi_log_path=kwargs.get("midi_log_path"),
                mock_mode=kwargs.get("mock_mode") or "rough",
                max_notes=int(kwargs.get("max_notes") or 96),
                user_command=kwargs.get("user_command"),
            )
            finished = FinishPracticeWorkflow(self.score_root, self.session_root, self.profile_root).run(
                listened["session"]["session_id"],
                listened["midi_log_path"],
            )
            return {"status": "completed", "listening": listened, **finished}
        if command == "update_teacher_memory":
            profile = ProfileService(ProfileRepository(self.profile_root)).update_memory(
                piece_id=kwargs["piece_id"],
                note=kwargs.get("note"),
                stage_label=kwargs.get("stage_label"),
                current_goal=kwargs.get("current_goal"),
                next_goal=kwargs.get("next_goal"),
                teacher_focus_tags=kwargs.get("teacher_focus_tags"),
            )
            return {"status": "memory_updated", "profile": profile}
        if command == "get_teacher_memory":
            profile = ProfileService(ProfileRepository(self.profile_root)).get_profile(kwargs["piece_id"])
            return {"status": "found" if profile else "missing", "profile": profile}
        if command == "review_score_import":
            source_path = kwargs.get("pdf_path") or kwargs.get("musicxml_path")
            if not source_path:
                raise ValueError("review_score_import requires pdf_path or musicxml_path")
            piece_id = kwargs.get("piece_id") or slugify(Path(source_path).stem)
            output_dir = kwargs.get("output_dir") or self.score_root / piece_id
            prompt_path = project_root() / "app" / "prompts" / "score_import_review_system_prompt.txt"
            review_command = kwargs.get("review_command")
            if not review_command and not os.getenv("PIANO_TEACHER_DISABLE_MODEL_REVIEW"):
                review_command = self.settings.score_import_review_command
            return ScoreImportReviewAgent(
                audiveris_command=self.settings.musicxml_converter_command,
                prompt_path=prompt_path,
                model=kwargs.get("model"),
                review_command=review_command,
            ).run(
                piece_id=piece_id,
                output_dir=output_dir,
                pdf_path=kwargs.get("pdf_path"),
                musicxml_path=kwargs.get("musicxml_path"),
            )
        raise ValueError(f"Unknown command: {command}")

    def _detect_piece_id(self, text: str) -> str | None:
        lowered = text.lower()
        for piece in self.piece_repo.list_pieces():
            candidates = [piece.get("piece_id"), piece.get("title"), *(piece.get("aliases") or [])]
            for candidate in candidates:
                if candidate and candidate.lower() in lowered:
                    return piece["piece_id"]
        return None

    def _detect_mock_mode(self, lowered: str) -> str:
        if "clean" in lowered or "干净" in lowered:
            return "clean"
        if "pitch" in lowered or "音高" in lowered or "错音" in lowered:
            return "pitch_errors"
        if "timing" in lowered or "节奏" in lowered:
            return "timing_errors"
        if "miss" in lowered or "漏音" in lowered:
            return "missed_notes"
        return "rough"

    def _detect_max_notes(self, lowered: str) -> int:
        import re

        match = re.search(r"(?:前|first\s*)?(\d{1,3})\s*(?:个音|notes?)", lowered)
        if not match:
            return 96
        return max(1, min(int(match.group(1)), 512))

    def _extract_path(self, text: str) -> str | None:
        import re

        match = re.search(r"(/[^，。；\s]+(?:\.pdf|\.mxl|\.musicxml|\.xml|\.json))", text, flags=re.I)
        return match.group(1) if match else None

    def _has_any(self, text: str, words: list[str]) -> bool:
        return any(word in text for word in words)

    def _latest_session(self, piece_id: str | None, statuses: set[str]) -> dict | None:
        return self.session_repo.latest_for_piece(piece_id=piece_id, statuses=statuses)

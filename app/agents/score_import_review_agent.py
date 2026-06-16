from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.tools.audiveris_runner import AudiverisResult, AudiverisRunner
from app.tools.musicxml_quality import MusicXmlQualityAnalyzer
from app.utils.json_io import write_json
from app.utils.paths import slugify


class ModelReviewer:
    def __init__(
        self,
        system_prompt_path: str | Path,
        model: str | None = None,
        review_command: str | None = None,
    ) -> None:
        self.system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.review_command = review_command or os.getenv("MODEL_REVIEW_COMMAND")

    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            if self.review_command:
                return self._review_with_command(payload)
            if os.getenv("OPENAI_API_KEY"):
                return self._review_with_openai(payload)
        except Exception as exc:
            return {
                "decision": self._fallback_decision(payload),
                "confidence": "low",
                "summary": "模型 review 调用失败，已保留确定性校验结果。",
                "risks": [
                    {
                        "severity": "high",
                        "area": "model_review",
                        "reason": str(exc),
                        "suggested_check": "检查模型配置后重跑，或人工复核 review_request.json。",
                    }
                ],
                "next_action": "不要直接进入练习分析，先完成谱面人工复核。",
            }
        return {
            "decision": self._fallback_decision(payload),
            "confidence": "low",
            "summary": "未配置模型调用；已生成可供模型 review 的结构化请求。",
            "risks": [
                {
                    "severity": "medium",
                    "area": "model_review",
                    "reason": "OPENAI_API_KEY 或 MODEL_REVIEW_COMMAND 未配置。",
                    "suggested_check": "配置模型后重新运行，或人工检查 review_request.json。",
                }
            ],
            "next_action": "先人工打开 MusicXML 与原 PDF 对照检查，再决定是否进入练习分析流程。",
        }

    def _review_with_openai(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "input": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
            ],
            "text": {"format": {"type": "json_object"}},
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))

        text = self._extract_response_text(data)
        return json.loads(text)

    def _review_with_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        completed = subprocess.run(
            shlex.split(self.review_command),
            input=json.dumps(
                {"system_prompt": self.system_prompt, "payload": payload},
                ensure_ascii=False,
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return {
                "decision": self._fallback_decision(payload),
                "confidence": "low",
                "summary": "外部模型 review 命令执行失败。",
                "risks": [
                    {
                        "severity": "high",
                        "area": "model_review",
                        "reason": completed.stderr.strip() or f"exit code {completed.returncode}",
                        "suggested_check": "检查 MODEL_REVIEW_COMMAND，并人工复核转换结果。",
                    }
                ],
                "next_action": "修复模型 review 命令后重跑。",
            }
        return json.loads(completed.stdout)

    def _extract_response_text(self, data: dict[str, Any]) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and "text" in content:
                    chunks.append(content["text"])
        if not chunks:
            raise ValueError("OpenAI response did not contain text output")
        return "".join(chunks)

    def _fallback_decision(self, payload: dict[str, Any]) -> str:
        conversion = payload.get("conversion", {})
        quality = payload.get("quality_report", {})
        if conversion.get("status") == "failed" or quality.get("validation_status") == "invalid":
            return "reject"
        if quality.get("validation_status") == "warning":
            return "needs_manual_review"
        return "needs_manual_review"


class ScoreImportReviewAgent:
    def __init__(
        self,
        audiveris_command: str,
        prompt_path: str | Path,
        model: str | None = None,
        review_command: str | None = None,
        timeout_seconds: int = 900,
    ) -> None:
        self.audiveris = AudiverisRunner(audiveris_command, timeout_seconds=timeout_seconds)
        self.quality_analyzer = MusicXmlQualityAnalyzer()
        self.reviewer = ModelReviewer(prompt_path, model=model, review_command=review_command)

    def run(
        self,
        piece_id: str,
        output_dir: str | Path,
        pdf_path: str | Path | None = None,
        musicxml_path: str | Path | None = None,
    ) -> dict[str, Any]:
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        conversion = self._conversion_result(pdf_path, musicxml_path, out_dir)
        if conversion.output_path:
            quality = self.quality_analyzer.analyze(conversion.output_path).to_dict()
        else:
            quality = {
                "validation_status": "invalid",
                "path": None,
                "warnings": ["No MusicXML output available for quality analysis."],
                "review_hints": ["Conversion failed before MusicXML validation."],
            }

        request_payload = {
            "piece_id": piece_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "conversion": asdict(conversion),
            "quality_report": quality,
            "review_scope": {
                "instrument": "piano",
                "goal": "decide whether converted MusicXML is safe enough for practice analysis",
                "expected_human_check": "compare PDF and MusicXML in a notation editor measure by measure where risks are flagged",
            },
        }
        write_json(out_dir / "review_request.json", request_payload)

        model_review = self.reviewer.review(request_payload)
        report = {
            "piece_id": piece_id,
            "generated_at": request_payload["generated_at"],
            "musicxml_path": conversion.output_path,
            "conversion": asdict(conversion),
            "quality_report": quality,
            "model_review": model_review,
            "agent_decision": model_review.get("decision", "needs_manual_review"),
        }
        write_json(out_dir / "score_import_review.json", report)
        return report

    def _conversion_result(
        self,
        pdf_path: str | Path | None,
        musicxml_path: str | Path | None,
        out_dir: Path,
    ) -> AudiverisResult:
        if musicxml_path:
            source = Path(musicxml_path).resolve()
            return AudiverisResult(
                status="completed",
                input_path=str(source),
                output_path=str(source),
                command=[],
                returncode=0,
                stdout="",
                stderr="",
                warnings=["Audiveris was skipped because an existing MusicXML file was provided."],
            )
        if not pdf_path:
            raise ValueError("Either pdf_path or musicxml_path is required.")
        return self.audiveris.convert(pdf_path, out_dir)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a score PDF with Audiveris and review MusicXML quality with a model.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pdf", help="Source score PDF to convert with Audiveris.")
    source.add_argument("--musicxml", help="Existing .mxl/.musicxml/.xml file to review without running Audiveris.")
    parser.add_argument("--piece-id", help="Stable piece id. Defaults to source filename slug.")
    parser.add_argument("--output-dir", help="Directory for MusicXML and review reports.")
    parser.add_argument(
        "--audiveris-command",
        default=os.getenv("AUDIVERIS_COMMAND", "audiveris -batch -export {input}"),
        help="Command template. Available placeholders: {input}, {output_dir}, {stem}.",
    )
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--review-command", default=os.getenv("MODEL_REVIEW_COMMAND"))
    parser.add_argument("--timeout-seconds", type=int, default=int(os.getenv("AUDIVERIS_TIMEOUT_SECONDS", "900")))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source_path = Path(args.pdf or args.musicxml).resolve()
    piece_id = args.piece_id or slugify(source_path.stem)
    output_dir = Path(args.output_dir or Path("scores") / piece_id).resolve()
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "score_import_review_system_prompt.txt"

    agent = ScoreImportReviewAgent(
        audiveris_command=args.audiveris_command,
        prompt_path=prompt_path,
        model=args.model,
        review_command=args.review_command,
        timeout_seconds=args.timeout_seconds,
    )
    report = agent.run(piece_id=piece_id, output_dir=output_dir, pdf_path=args.pdf, musicxml_path=args.musicxml)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["agent_decision"] == "accept" else 2


if __name__ == "__main__":
    raise SystemExit(main())

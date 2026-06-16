from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudiverisResult:
    status: str
    input_path: str
    output_path: str | None
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    warnings: list[str]


class AudiverisRunner:
    """Run Audiveris while keeping command details configurable."""

    def __init__(
        self,
        command_template: str = "audiveris -batch -export {input}",
        timeout_seconds: int = 900,
    ) -> None:
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def convert(self, pdf_path: str | Path, output_dir: str | Path) -> AudiverisResult:
        pdf = Path(pdf_path).resolve()
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        before = self._musicxml_candidates(pdf, out_dir)
        command = self._build_command(pdf, out_dir)

        try:
            completed = subprocess.run(
                command,
                cwd=str(out_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            return AudiverisResult(
                status="failed",
                input_path=str(pdf),
                output_path=None,
                command=command,
                returncode=None,
                stdout="",
                stderr=str(exc),
                warnings=["Audiveris command was not found."],
            )
        except subprocess.TimeoutExpired as exc:
            return AudiverisResult(
                status="failed",
                input_path=str(pdf),
                output_path=None,
                command=command,
                returncode=None,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                warnings=[f"Audiveris timed out after {self.timeout_seconds} seconds."],
            )

        after = self._musicxml_candidates(pdf, out_dir)
        new_outputs = [path for path in after if path not in before]
        output_path = self._pick_output(new_outputs or after, pdf)
        status = "completed" if completed.returncode == 0 and output_path else "failed"
        warnings = []
        if completed.returncode != 0:
            warnings.append(f"Audiveris exited with code {completed.returncode}.")
        if not output_path:
            warnings.append("No MusicXML or compressed .mxl output was detected.")

        return AudiverisResult(
            status=status,
            input_path=str(pdf),
            output_path=str(output_path) if output_path else None,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            warnings=warnings,
        )

    def _build_command(self, pdf: Path, out_dir: Path) -> list[str]:
        rendered = self.command_template.format(
            input=shlex.quote(str(pdf)),
            output_dir=shlex.quote(str(out_dir)),
            stem=shlex.quote(pdf.stem),
        )
        return shlex.split(rendered)

    def _musicxml_candidates(self, pdf: Path, out_dir: Path) -> set[Path]:
        paths = set(out_dir.glob("*.mxl"))
        paths.update(out_dir.glob("*.musicxml"))
        paths.update(out_dir.glob("*.xml"))
        paths.update(pdf.parent.glob(f"{pdf.stem}*.mxl"))
        paths.update(pdf.parent.glob(f"{pdf.stem}*.musicxml"))
        paths.update(pdf.parent.glob(f"{pdf.stem}*.xml"))
        return {path.resolve() for path in paths}

    def _pick_output(self, candidates: list[Path] | set[Path], pdf: Path) -> Path | None:
        ordered = sorted(candidates, key=lambda path: (path.suffix != ".mxl", str(path)))
        stem_matches = [path for path in ordered if path.stem.startswith(pdf.stem)]
        return stem_matches[0] if stem_matches else (ordered[0] if ordered else None)


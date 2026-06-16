# Piano Teacher Agent

[中文说明](README_CN.md)

Piano Teacher Agent is a local piano-practice assistant that connects score import, MusicXML normalization, MIDI-vs-score analysis, Hermes skills, and long-term practice memory.

The intended workflow is conversational: tell Hermes to prepare a piece, start practice, finish practice, review the performance, record learning progress, and suggest the next practice plan. The deterministic Python workflows handle score parsing, MIDI alignment, scoring, persistence, and profile updates. Hermes subagents are used for higher-level review and teaching feedback.

## What It Does

- Imports and reviews piano scores from PDF or existing MusicXML/MXL.
- Normalizes MusicXML into a compact `normalized_score.json` format for analysis.
- Creates practice sessions and analyzes MIDI event logs against the score.
- Generates structured practice feedback: score, problem measures, issue tags, practice plan, and next focus.
- Maintains per-piece learning profiles in `profiles/`.
- Provides script-backed Hermes skills so the main agent can coordinate workflows without depending on MCP.
- Keeps an MCP server as a compatibility layer for older Hermes dashboard/tool flows.

## Architecture

```text
Hermes / user request
  -> piano-teacher-conductor skill
  -> scripts/hermes_piano_teacher
  -> app.agents.ConductorAgent
  -> workflow layer
  -> deterministic services/tools
  -> practice feedback or score import review subagent
  -> sessions/, profiles/, scores/
```

Core modules:

- `app/agents/`: conductor, piano teacher feedback agent, score import review agent.
- `app/workflows/`: start practice, finish practice, mock listening, score normalization, library refresh.
- `app/services/`: scoring, alignment, MIDI parsing, profile updates, score library logic.
- `app/tools/`: Audiveris wrapper, MusicXML reader, MIDI parser, score aligner.
- `skills/`: local Hermes/Codex skills for conductor, practice review, and score import review.
- `scripts/`: script entrypoints used by Hermes skills and compatibility MCP.
- `scores/`: score library, imported MusicXML/MXL, normalized scores, review reports.
- `sessions/`: practice session records, analyses, feedback, mock MIDI logs.
- `profiles/`: long-term per-piece learning memory.

## Quick Start

Run commands from the project root:

```bash
cd /Users/zonghe/Downloads/piano_teacher
```

Start a Hermes CLI conversation:

```bash
scripts/start_hermes_piano_teacher_cli
```

Then talk naturally, for example:

```text
准备 minimal-piano-fixture
mock 听我练习 minimal-piano-fixture 前24个音 rough 模式
查看 minimal-piano-fixture 的学习进度和计划
请记住 minimal-piano-fixture：目标是慢速稳定，下次目标是保持当前速度完整弹奏
```

The repository `AGENTS.md` instructs Hermes to run the local conductor script for these requests and summarize the result.

You can also call the conductor script directly:

Prepare a piece:

```bash
scripts/hermes_piano_teacher "准备 minimal-piano-fixture"
```

Run a mock practice session and generate feedback:

```bash
scripts/hermes_piano_teacher "mock 听我练习 minimal-piano-fixture 前24个音 rough 模式"
```

View progress and next plan:

```bash
scripts/hermes_piano_teacher "查看 minimal-piano-fixture 的学习进度和计划"
```

Review a PDF score import:

```bash
scripts/hermes_piano_teacher "复核琴谱 PDF /Users/zonghe/Downloads/piano_teacher/Por_una_cabeza_Feisi.pdf"
```

## Direct CLI

The same workflows can be run without Hermes:

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score minimal-piano-fixture
python3 -m app.main start-practice minimal-piano-fixture
python3 -m app.main finish-practice <session_id> --midi-log-path scores/minimal-piano-fixture/performance_fixture.json
python3 -m app.main listen-mock-practice minimal-piano-fixture --mock-mode rough --max-notes 24
python3 -m app.main ask "查看 minimal-piano-fixture 的学习进度和计划"
```

## Hermes Skills

The project includes three local skills:

- `skills/piano-teacher-conductor`: natural-language coordinator for practice workflows.
- `skills/piano-practice-reviewer`: teaching feedback subagent for analyzed MIDI-vs-score results.
- `skills/score-import-reviewer`: score import review subagent for PDF/MusicXML quality checks.

`AGENTS.md` tells Hermes/Codex to prefer these script-backed skills over MCP. MCP remains available through `scripts/piano_teacher_mcp` for compatibility.

For the plain Hermes CLI workflow, start Hermes from this project root so `AGENTS.md` is loaded:

```bash
hermes chat --cli
```

`scripts/start_hermes_piano_teacher_cli` is a small convenience wrapper around that command.

## Validation

Smoke tests:

```bash
python3 tests/smoke_test.py
python3 tests/dashboard_flow_smoke_test.py
python3 tests/natural_language_conductor_smoke_test.py
python3 tests/mcp_smoke_test.py
python3 -m compileall app scripts tests
```

Skill validation, using the Hermes Python environment that includes `yaml`:

```bash
/Users/zonghe/.hermes/hermes-agent/venv/bin/python \
  /Users/zonghe/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  /Users/zonghe/Downloads/piano_teacher/skills/piano-teacher-conductor
```

Repeat the same validation for `piano-practice-reviewer` and `score-import-reviewer`.

## Requirements

- Python 3.11 or compatible Python 3.
- Hermes CLI for conversational and subagent workflows.
- Audiveris for PDF-to-MusicXML conversion:

```text
/Applications/Audiveris.app/Contents/MacOS/Audiveris
```

The configured paths live in `app/settings.json`. Use `app/settings.example.json` as a portable template.

## Current Limits

- Real hardware MIDI recording is still a stub; mock MIDI and JSON MIDI fixtures are supported.
- PDF-to-MusicXML quality depends on Audiveris and should be manually reviewed before serious practice analysis.
- LLM subagents provide review and teaching interpretation only after deterministic structured data exists.
- Existing session and profile JSON files are committed as development fixtures and examples.

See `USER_MANUAL.md` for detailed operating instructions.

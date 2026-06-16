---
name: piano-teacher-conductor
description: Coordinate the local piano teacher practice system from natural language. Use when a user wants Hermes/Codex to start piano practice, finish practice, listen with mock MIDI, prepare or refresh scores, review a PDF/MusicXML import, view long-term learning progress, or maintain the piano teacher memory without relying on MCP tools.
---

# Piano Teacher Conductor

Use the repository script entrypoint instead of MCP:

```bash
scripts/hermes_piano_teacher "<natural language request>"
```

The conductor script enables Hermes subagents and delegates to `python3 -m app.main ask`.

Common requests:

- Start practice: `scripts/hermes_piano_teacher "开始练习 minimal-piano-fixture"`
- Mock listening: `scripts/hermes_piano_teacher "mock 听我练 minimal-piano-fixture 前32个音，rough 模式"`
- Finish practice: `scripts/hermes_piano_teacher "结束 minimal-piano-fixture 练习，midi 在 /abs/path/performance_fixture.json"`
- Prepare a score: `scripts/hermes_piano_teacher "准备 por-una-cabeza-feisi"`
- View progress: `scripts/hermes_piano_teacher "查看 por-una-cabeza-feisi 的学习进度和计划"`
- Review import: `scripts/hermes_piano_teacher "复核琴谱 PDF /abs/path/score.pdf"`

Return the JSON result to the user in concise natural language. Mention generated paths for `session.json`, `analysis.json`, `feedback.json`, `score_import_review.json`, or profile files when relevant.

The conductor may call two subagents:

- Practice feedback subagent: reads structured analysis/profile and writes teaching advice.
- Score import reviewer subagent: reviews PDF-to-MusicXML conversion quality.

Do not ask Hermes to inspect raw MIDI or MusicXML manually unless a user explicitly asks for debugging. The deterministic Python workflows do parsing, alignment, scoring, and persistence.

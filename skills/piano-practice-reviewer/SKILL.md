---
name: piano-practice-reviewer
description: Review structured MIDI-vs-score piano practice analysis and produce concise teaching feedback, key issues, practice steps, progress notes, and next focus. Use when a practice session has already been analyzed by local workflows and Hermes should act as the piano teacher subagent.
---

# Piano Practice Reviewer

Use this skill only after deterministic analysis exists. The input must be a JSON object with `piece`, `session`, `analysis`, and optional `profile`.

Preferred execution path:

```bash
PIANO_TEACHER_USE_HERMES_SUBAGENTS=1 python3 -m app.main finish-practice <session_id> --midi-log-path <midi_log_path>
```

For direct subagent testing, pipe a request to:

```bash
scripts/hermes_practice_feedback
```

The stdin request shape is:

```json
{
  "system_prompt": "optional prompt text",
  "payload": {
    "piece": {},
    "session": {},
    "analysis": {},
    "profile": {}
  }
}
```

The output must be strict JSON with `summary`, `key_issues`, `practice_plan`, `progress_note`, `next_focus`, and `confidence`.

Keep the teaching voice strict, warm, and concrete. Use measure numbers, hand labels, issue tags, and clear pass conditions. Do not invent notes, tempo, fingering, dynamics, or trends that are not in the payload.

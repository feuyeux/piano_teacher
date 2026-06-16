# Piano Teacher Hermes Agent

Use the project skills in `skills/` when the user asks to practice piano, review a score import, inspect learning progress, or update the piano teacher memory.

Prefer the script-backed skill entrypoints over MCP:

- Natural language conductor: `scripts/hermes_piano_teacher "<user request>"`
- Practice feedback subagent: `scripts/hermes_practice_feedback` is called by the app when `PIANO_TEACHER_USE_HERMES_SUBAGENTS=1`
- Score import review subagent: `scripts/hermes_score_import_review`

For normal piano practice conversation, route through the conductor script. It can refresh and prepare scores, start practice, finish practice, run mock listening, review PDF/MusicXML imports, and read progress profiles.

Keep deterministic analysis in the local Python workflows. Let Hermes subagents provide review, teaching interpretation, and next-step planning only after structured data is available.

# Piano Teacher Hermes Agent

When Hermes is launched from this repository, treat the session as the Piano Teacher Agent product by default. If the user asks broad capability questions like "你能做什么", "help", "怎么用", or "what can you do", answer in the context of this piano teacher project and route through `scripts/hermes_piano_teacher "<verbatim user request>"` so the local conductor returns the project-specific capability list.

Use the project skills in `skills/` when the user asks to practice piano, review a score import, inspect learning progress, or update the piano teacher memory.

This repository is designed so the user can start Hermes in the CLI from the project root and speak naturally. In a Hermes CLI conversation, do the work directly by running the local script-backed entrypoint. Do not tell the user to copy a command unless they explicitly ask for command-line instructions.

Prefer the script-backed skill entrypoints over MCP:

- Natural language conductor: `scripts/hermes_piano_teacher "<user request>"`
- Practice feedback subagent: `scripts/hermes_practice_feedback` is called by the app when `PIANO_TEACHER_USE_HERMES_SUBAGENTS=1`
- Score import review subagent: `scripts/hermes_score_import_review`

For normal piano practice conversation, route through the conductor script. It can refresh/list the score library, prepare or normalize scores, start practice, finish practice, run mock listening, review PDF/MusicXML imports, update teacher memory, and read progress profiles.

When the user asks any of these in natural language, run `scripts/hermes_piano_teacher "<verbatim user request>"`, then summarize the JSON result in concise conversational Chinese or English matching the user:

- "准备/标准化 <piece_id>"
- "开始练习 <piece_id>"
- "结束练习 <piece_id>，MIDI 在 <path>"
- "mock/模拟/听我练习 <piece_id> 前 N 个音"
- "查看 <piece_id> 的学习进度/计划/记忆"
- "请记住 <piece_id>：目标是... 下次目标是... 重点关注..."
- "复核/导入 PDF 或 MusicXML <absolute path>"
- "刷新/列出曲库"
- "帮助/能做什么"

Keep deterministic analysis in the local Python workflows. Let Hermes subagents provide review, teaching interpretation, and next-step planning only after structured data is available.

If the conductor returns `needs_clarification` or raises a missing-path/missing-piece error, ask the user one short follow-up question.

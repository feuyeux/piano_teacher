---
name: score-import-reviewer
description: Review a piano score import before practice analysis. Use when the user wants Hermes/Codex to convert or review a PDF, MXL, MusicXML, or XML score, check PDF-to-MusicXML quality, decide whether it is safe for MIDI practice alignment, and report manual review risks.
---

# Score Import Reviewer

Use the local score import workflow, not MCP:

```bash
python3 -m app.main review-score-import --pdf-path /abs/path/score.pdf --piece-id optional-piece-id
python3 -m app.main review-score-import --musicxml-path /abs/path/score.mxl --piece-id optional-piece-id
```

The workflow writes:

- `scores/<piece_id>/review_request.json`
- `scores/<piece_id>/score_import_review.json`
- converted MusicXML/MXL when Audiveris succeeds

The model subagent is `scripts/hermes_score_import_review`; it receives deterministic conversion and MusicXML quality data and returns a JSON decision. Treat `needs_manual_review` as a normal cautious result, not a failure.

After a usable import, prepare the piece before practice:

```bash
python3 -m app.main refresh-library
python3 -m app.main normalize-score <piece_id>
```

Do not claim OMR accuracy is perfect. Always surface warnings, missing parts, low note/measure counts, parse failures, or validation risks.

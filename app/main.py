from __future__ import annotations

import argparse
import json
import sys

from app.agents.conductor_agent import ConductorAgent


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Piano teacher agent local CLI.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("refresh-library")
    normalize = subcommands.add_parser("normalize-score")
    normalize.add_argument("piece_id")
    start = subcommands.add_parser("start-practice")
    start.add_argument("piece_id")
    finish = subcommands.add_parser("finish-practice")
    finish.add_argument("session_id")
    finish.add_argument("--midi-log-path")
    listen = subcommands.add_parser("listen-mock-practice")
    listen.add_argument("piece_id")
    listen.add_argument("--mock-mode", default="rough", choices=["clean", "rough", "pitch_errors", "timing_errors", "missed_notes"])
    listen.add_argument("--max-notes", type=int, default=96)
    listen.add_argument("--user-command")
    review = subcommands.add_parser("review-score-import")
    review_source = review.add_mutually_exclusive_group(required=True)
    review_source.add_argument("--pdf-path")
    review_source.add_argument("--musicxml-path")
    review.add_argument("--piece-id")
    review.add_argument("--output-dir")
    ask = subcommands.add_parser("ask")
    ask.add_argument("text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    conductor = ConductorAgent()
    if args.command == "refresh-library":
        result = conductor.handle_command("refresh_library")
    elif args.command == "normalize-score":
        result = conductor.handle_command("normalize_score", piece_id=args.piece_id)
    elif args.command == "start-practice":
        result = conductor.handle_command("start_practice", piece_id=args.piece_id)
    elif args.command == "finish-practice":
        result = conductor.handle_command("finish_practice", session_id=args.session_id, midi_log_path=args.midi_log_path)
    elif args.command == "listen-mock-practice":
        result = conductor.handle_command(
            "listen_mock_practice",
            piece_id=args.piece_id,
            mock_mode=args.mock_mode,
            max_notes=args.max_notes,
            user_command=args.user_command,
        )
    elif args.command == "review-score-import":
        result = conductor.handle_command(
            "review_score_import",
            pdf_path=args.pdf_path,
            musicxml_path=args.musicxml_path,
            piece_id=args.piece_id,
            output_dir=args.output_dir,
        )
    elif args.command == "ask":
        result = conductor.handle_natural_language(args.text)
    else:
        raise ValueError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

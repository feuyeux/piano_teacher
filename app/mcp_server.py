from __future__ import annotations

import json
import sys
from typing import Any

from app.agents.conductor_agent import ConductorAgent


class PianoTeacherMcpServer:
    def __init__(self) -> None:
        self.conductor = ConductorAgent()
        self.transport_mode = "headers"

    def serve(self) -> None:
        while True:
            message = self._read_message()
            if message is None:
                break
            response = self._handle(message)
            if response is not None:
                self._write_message(response)

    def _handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")
        try:
            if method == "initialize":
                return self._result(
                    message_id,
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "piano-teacher", "version": "0.1.0"},
                    },
                )
            if method in {"notifications/initialized", "notifications/cancelled"}:
                return None
            if method == "tools/list":
                return self._result(message_id, {"tools": self._tools()})
            if method == "tools/call":
                params = message.get("params", {})
                return self._result(message_id, self._call_tool(params.get("name"), params.get("arguments") or {}))
            return self._error(message_id, -32601, f"Unknown method: {method}")
        except Exception as exc:
            return self._error(message_id, -32000, str(exc))

    def _tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "refresh_library",
                "description": "Scan the piano score library and update scores/piece_index.json. Use when the user says refresh/update the piano teacher memory or score library.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "normalize_score",
                "description": "Normalize one MusicXML score into scores/<piece_id>/normalized_score.json so it can be used for practice analysis.",
                "inputSchema": {
                    "type": "object",
                    "required": ["piece_id"],
                    "properties": {"piece_id": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "prepare_piece",
                "description": "Refresh the score library and optionally normalize a piece in one step. Use when the user asks to update teacher memory, prepare a piece, or make a score ready for practice.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"piece_id": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "start_practice",
                "description": "Create a practice session for a piece. Use when the user says they want to start practicing a prepared piece.",
                "inputSchema": {
                    "type": "object",
                    "required": ["piece_id"],
                    "properties": {"piece_id": {"type": "string"}, "user_command": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "finish_practice",
                "description": "Analyze a practice session using a JSON MIDI fixture and generate teacher feedback. Use after recording/listening is stopped.",
                "inputSchema": {
                    "type": "object",
                    "required": ["session_id"],
                    "properties": {"session_id": {"type": "string"}, "midi_log_path": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "listen_mock_practice",
                "description": "Mock listening to the user practice through MIDI, then analyze the performance, update the piano teacher memory/profile, and generate feedback. Use when the user says listen to my practice but no MIDI device is connected yet.",
                "inputSchema": {
                    "type": "object",
                    "required": ["piece_id"],
                    "properties": {
                        "piece_id": {"type": "string"},
                        "session_id": {"type": "string"},
                        "midi_log_path": {"type": "string"},
                        "mock_mode": {
                            "type": "string",
                            "enum": ["clean", "rough", "pitch_errors", "timing_errors", "missed_notes"],
                        },
                        "max_notes": {"type": "integer"},
                        "user_command": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "update_teacher_memory",
                "description": "Manually update the piano teacher memory/profile for a piece, including goals, stage, focus tags, and teacher notes.",
                "inputSchema": {
                    "type": "object",
                    "required": ["piece_id"],
                    "properties": {
                        "piece_id": {"type": "string"},
                        "note": {"type": "string"},
                        "stage_label": {"type": "string"},
                        "current_goal": {"type": "string"},
                        "next_goal": {"type": "string"},
                        "teacher_focus_tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "get_teacher_memory",
                "description": "Read the piano teacher memory/profile for a piece.",
                "inputSchema": {
                    "type": "object",
                    "required": ["piece_id"],
                    "properties": {"piece_id": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            {
                "name": "review_score_import",
                "description": "Convert/review a score PDF or existing MusicXML before it enters practice analysis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "musicxml_path": {"type": "string"},
                        "piece_id": {"type": "string"},
                        "output_dir": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        ]

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "refresh_library":
            result = self.conductor.handle_command("refresh_library")
        elif name == "normalize_score":
            result = self.conductor.handle_command("normalize_score", piece_id=arguments["piece_id"])
        elif name == "prepare_piece":
            result = self.conductor.handle_command("prepare_piece", piece_id=arguments.get("piece_id"))
        elif name == "start_practice":
            result = self.conductor.handle_command(
                "start_practice",
                piece_id=arguments["piece_id"],
                user_command=arguments.get("user_command"),
            )
        elif name == "finish_practice":
            result = self.conductor.handle_command(
                "finish_practice",
                session_id=arguments["session_id"],
                midi_log_path=arguments.get("midi_log_path"),
            )
        elif name == "listen_mock_practice":
            result = self.conductor.handle_command(
                "listen_mock_practice",
                piece_id=arguments["piece_id"],
                session_id=arguments.get("session_id"),
                midi_log_path=arguments.get("midi_log_path"),
                mock_mode=arguments.get("mock_mode"),
                max_notes=arguments.get("max_notes"),
                user_command=arguments.get("user_command"),
            )
        elif name == "update_teacher_memory":
            result = self.conductor.handle_command(
                "update_teacher_memory",
                piece_id=arguments["piece_id"],
                note=arguments.get("note"),
                stage_label=arguments.get("stage_label"),
                current_goal=arguments.get("current_goal"),
                next_goal=arguments.get("next_goal"),
                teacher_focus_tags=arguments.get("teacher_focus_tags"),
            )
        elif name == "get_teacher_memory":
            result = self.conductor.handle_command("get_teacher_memory", piece_id=arguments["piece_id"])
        elif name == "review_score_import":
            result = self.conductor.handle_command(
                "review_score_import",
                pdf_path=arguments.get("pdf_path"),
                musicxml_path=arguments.get("musicxml_path"),
                piece_id=arguments.get("piece_id"),
                output_dir=arguments.get("output_dir"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}

    def _read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            line = sys.stdin.buffer.readline()
            if line == b"":
                return None
            stripped = line.strip()
            if stripped.startswith(b"{"):
                self.transport_mode = "jsonl"
                return json.loads(stripped.decode("utf-8"))
            if line in {b"\r\n", b"\n"}:
                break
            key, _, value = line.decode("ascii").partition(":")
            headers[key.lower()] = value.strip()
        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))

    def _write_message(self, message: dict[str, Any]) -> None:
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        if self.transport_mode == "jsonl":
            sys.stdout.buffer.write(data + b"\n")
            sys.stdout.buffer.flush()
            return
        sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

    def _result(self, message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": message_id, "result": result}

    def _error(self, message_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def main() -> int:
    PianoTeacherMcpServer().serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

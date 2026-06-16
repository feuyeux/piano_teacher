from __future__ import annotations

from pathlib import Path

from app.utils.json_io import read_json, write_json


class SessionRepository:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, session: dict) -> None:
        write_json(self.root / session["session_id"] / "session.json", session)

    def load(self, session_id: str) -> dict:
        return read_json(self.root / session_id / "session.json")

    def list_sessions(self) -> list[dict]:
        sessions = []
        for path in self.root.glob("*/session.json"):
            try:
                sessions.append(read_json(path))
            except Exception:
                continue
        return sorted(sessions, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)

    def latest_for_piece(self, piece_id: str | None = None, statuses: set[str] | None = None) -> dict | None:
        for session in self.list_sessions():
            if piece_id and session.get("piece_id") != piece_id:
                continue
            if statuses and session.get("session_status") not in statuses:
                continue
            return session
        return None

    def save_analysis(self, session_id: str, analysis: dict) -> str:
        path = self.root / session_id / "analysis.json"
        write_json(path, analysis)
        return str(path)

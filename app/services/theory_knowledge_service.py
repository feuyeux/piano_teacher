from __future__ import annotations

from pathlib import Path
from typing import Any

from app.utils.json_io import read_json
from app.utils.paths import project_root


class TheoryKnowledgeService:
    def __init__(self, knowledge_path: str | Path | None = None) -> None:
        self.knowledge_path = Path(knowledge_path) if knowledge_path else project_root() / "knowledge" / "music_theory_basics.json"

    def list_topics(self) -> list[dict[str, Any]]:
        return list(self._load().get("topics") or [])

    def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        query_tokens = self._tokens(query)
        scored: list[tuple[int, dict[str, Any]]] = []
        for topic in self.list_topics():
            haystack = self._topic_text(topic)
            score = sum(1 for token in query_tokens if token in haystack)
            if score:
                scored.append((score, topic))
        scored.sort(key=lambda item: (-item[0], item[1].get("id", "")))
        if scored:
            return [topic for _, topic in scored[:limit]]
        return self.list_topics()[:limit]

    def for_practice_context(self, analysis: dict, limit: int = 2) -> list[dict[str, Any]]:
        parts: list[str] = []
        for measure in analysis.get("problem_measures") or []:
            parts.extend(measure.get("issue_tags") or [])
        parts.extend(analysis.get("recommended_next_steps") or [])
        parts.extend(analysis.get("warnings") or [])
        return self.search(" ".join(parts), limit=limit)

    def explain(self, query: str, limit: int = 3) -> dict[str, Any]:
        topics = self.search(query, limit=limit)
        return {
            "status": "theory_answer",
            "query": query,
            "topics": topics,
            "answer": self._compose_answer(topics),
        }

    def _load(self) -> dict[str, Any]:
        if not self.knowledge_path.exists():
            return {"topics": []}
        return read_json(self.knowledge_path)

    def _compose_answer(self, topics: list[dict[str, Any]]) -> str:
        if not topics:
            return "我还没有找到对应的乐理条目。"
        lines = []
        for topic in topics:
            lines.append(f"{topic['title']}：{topic['summary']} 练习提示：{topic['practice_tip']}")
        return "\n".join(lines)

    def _topic_text(self, topic: dict[str, Any]) -> str:
        values = [
            topic.get("id", ""),
            topic.get("title", ""),
            topic.get("summary", ""),
            topic.get("practice_tip", ""),
            " ".join(topic.get("keywords") or []),
            " ".join(topic.get("examples") or []),
        ]
        return " ".join(values).lower()

    def _tokens(self, query: str) -> list[str]:
        text = query.lower()
        tokens = [token for token in text.replace("_", " ").split() if token]
        keywords = [
            "乐理",
            "节奏",
            "拍子",
            "节拍",
            "重音",
            "时值",
            "音高",
            "错音",
            "音程",
            "音阶",
            "调号",
            "和弦",
            "和声",
            "乐句",
            "触键",
            "连奏",
            "断奏",
            "力度",
            "踏板",
            "timing",
            "rhythm",
            "pitch",
            "duration",
            "scale",
            "key",
            "chord",
            "harmony",
            "phrasing",
            "articulation",
            "dynamic",
            "pedal",
        ]
        tokens.extend(keyword for keyword in keywords if keyword in text)
        return list(dict.fromkeys(tokens))

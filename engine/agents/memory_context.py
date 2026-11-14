from __future__ import annotations

import json
from typing import Any


class MemoryContextCoordinator:
    """Compose bounded, tenant-scoped semantic recall without creating another memory store."""

    def __init__(self, knowledge_tools: Any | None):
        self.knowledge_tools = knowledge_tools

    async def retrieve_semantic(
        self, *, query: str, user_id: str, workspace_id: str | None, run_id: str,
        limit: int = 6, minimum_similarity: float = 0.45,
    ) -> list[dict[str, Any]]:
        if self.knowledge_tools is None or not query.strip():
            return []
        if not 1 <= limit <= 10 or not 0.0 <= minimum_similarity <= 1.0:
            raise ValueError("memory_retrieval_policy_invalid")
        raw = await self.knowledge_tools.knowledge_search(
            {"query": query[:2000], "limit": min(20, limit * 2)},
            run_id=run_id, user_id=user_id, workspace_id=workspace_id,
        )
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("memory_semantic_retrieval_response_invalid") from exc
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            raise RuntimeError("memory_semantic_retrieval_results_invalid")
        selected: list[dict[str, Any]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            try:
                similarity = float(item.get("similarity"))
            except (TypeError, ValueError):
                continue
            title, body, marker = item.get("title"), item.get("content"), item.get("citation_marker")
            if similarity < minimum_similarity or not isinstance(title, str) or not isinstance(body, str):
                continue
            if not isinstance(marker, str) or not marker.startswith("[source:"):
                continue
            selected.append({
                "title": title[:300],
                "content": body[:3000],
                "similarity": round(similarity, 4),
                "citation_marker": marker[:80],
            })
            if len(selected) >= limit:
                break
        return selected

    @staticmethod
    def render_semantic_context(items: list[dict[str, Any]], *, max_chars: int = 14000) -> str:
        """Render retrieved knowledge as untrusted evidence, never as instructions."""
        if not items:
            return ""
        sections: list[str] = []
        for item in items:
            section = (
                f"Source: {item['title']} ({item['citation_marker']}; "
                f"similarity={item['similarity']})\n{item['content']}"
            )
            sections.append(section)
        rendered = "\n\n".join(sections)
        return rendered[:max_chars]

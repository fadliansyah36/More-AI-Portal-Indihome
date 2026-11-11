from __future__ import annotations

import os
from typing import Any

import httpx


class TavilySearchAdapter:
    """Provider-pinned web search adapter. No arbitrary URL or user-controlled host is accepted."""

    endpoint = "https://api.tavily.com/search"

    def __init__(self, http: httpx.AsyncClient, *, api_key: str | None = None):
        self.http = http
        self.api_key = api_key if api_key is not None else os.getenv("TAVILY_API_KEY", "")

    async def google_search(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        query = arguments.get("query")
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 1000:
            raise ValueError("search_query_invalid")
        if not self.api_key:
            raise RuntimeError("search_provider_not_configured")
        response = await self.http.post(
            self.endpoint,
            json={
                "api_key": self.api_key,
                "query": query.strip(),
                "max_results": 10,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=25.0,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            raise RuntimeError("search_provider_response_invalid")
        normalized = []
        for item in results[:10]:
            if not isinstance(item, dict):
                continue
            url, title, snippet = item.get("url"), item.get("title"), item.get("content")
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                continue
            normalized.append({
                "title": str(title or "")[:500],
                "url": url[:2048],
                "snippet": str(snippet or "")[:3000],
            })
        import json
        return json.dumps({"query": query.strip(), "results": normalized}, ensure_ascii=False, separators=(",", ":"))

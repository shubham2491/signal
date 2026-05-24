"""Tavily search wrapper.

We use Tavily because it returns clean JSON with snippets in one call — no
scraping, no SERP parsing. Each query is constrained to a brand domain so we
stay in the curated brand universe and avoid marketplaces.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


class SearchClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.tavily_api_key

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, *, max_results: int = 4) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(TAVILY_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            log.warning("Tavily search failed for %r: %s", query, e)
            return []
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in data.get("results", [])
        ]

    async def search_many(self, queries: list[str], *, max_results: int = 3) -> list[dict[str, Any]]:
        """Fan out several queries in parallel; flatten results with the source query."""
        if not queries:
            return []
        results = await asyncio.gather(
            *(self.search(q, max_results=max_results) for q in queries),
            return_exceptions=True,
        )
        out: list[dict[str, Any]] = []
        for q, r in zip(queries, results):
            if isinstance(r, Exception):
                continue
            for item in r:
                item["query"] = q
                out.append(item)
        return out


_singleton: SearchClient | None = None


def get_search() -> SearchClient:
    global _singleton
    if _singleton is None:
        _singleton = SearchClient()
    return _singleton

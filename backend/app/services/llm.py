"""Thin LLM client with vision support.

OpenAI is the default provider (gpt-4o). The interface is intentionally small
so we can swap in Gemini or Anthropic later without touching agent code.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

log = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def vision_json(
        self,
        *,
        system: str,
        user_text: str,
        images: list[bytes],
        schema_hint: str = "",
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Send images + a prompt, expect a JSON object back."""
        if self._client is None:
            raise RuntimeError("LLM client not configured (missing OPENAI_API_KEY)")

        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for img in images:
            b64 = base64.b64encode(img).decode("ascii")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })

        full_system = system
        if schema_hint:
            full_system = f"{system}\n\nReturn JSON matching this shape:\n{schema_hint}"

        resp = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": content},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON, falling back to empty dict: %r", raw[:200])
            return {}

    async def text_json(
        self,
        *,
        system: str,
        user_text: str,
        schema_hint: str = "",
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Text-only JSON call."""
        if self._client is None:
            raise RuntimeError("LLM client not configured (missing OPENAI_API_KEY)")
        full_system = system
        if schema_hint:
            full_system = f"{system}\n\nReturn JSON matching this shape:\n{schema_hint}"
        resp = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_text},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("LLM returned non-JSON, falling back to empty dict: %r", raw[:200])
            return {}


_singleton: LLMClient | None = None


def get_llm() -> LLMClient:
    global _singleton
    if _singleton is None:
        _singleton = LLMClient()
    return _singleton

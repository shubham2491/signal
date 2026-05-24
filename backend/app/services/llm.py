"""Thin LLM client with vision support.

Two providers: Gemini (default, free tier) and OpenAI. Selected via
LLM_PROVIDER env var. Both expose the same `vision_json` / `text_json`
interface, returning a dict parsed from JSON.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Protocol

from app.config import get_settings

log = logging.getLogger(__name__)


class _Backend(Protocol):
    is_available: bool
    async def vision_json(self, *, system: str, user_text: str, images: list[bytes],
                          schema_hint: str = "", temperature: float = 0.2) -> dict[str, Any]: ...
    async def text_json(self, *, system: str, user_text: str,
                        schema_hint: str = "", temperature: float = 0.3) -> dict[str, Any]: ...


# ---------- Gemini ----------

class GeminiBackend:
    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.gemini_model
        self.api_key = settings.gemini_api_key
        self._configured = False
        if self.api_key:
            try:
                import google.generativeai as genai  # noqa: PLC0415
                genai.configure(api_key=self.api_key)
                self._genai = genai
                self._configured = True
            except ImportError:
                log.warning("google-generativeai not installed")

    @property
    def is_available(self) -> bool:
        return self._configured

    def _model(self):
        return self._genai.GenerativeModel(self.model_name)

    async def vision_json(
        self, *, system: str, user_text: str, images: list[bytes],
        schema_hint: str = "", temperature: float = 0.2,
    ) -> dict[str, Any]:
        full_prompt = system
        if schema_hint:
            full_prompt += f"\n\nReturn JSON matching this shape:\n{schema_hint}"
        full_prompt += f"\n\n{user_text}"
        parts: list[Any] = [full_prompt]
        for img in images:
            parts.append({"mime_type": "image/jpeg", "data": img})

        def _call() -> str:
            resp = self._model().generate_content(
                parts,
                generation_config={
                    "temperature": temperature,
                    "response_mime_type": "application/json",
                },
            )
            return resp.text or "{}"

        raw = await asyncio.to_thread(_call)
        return _parse_json(raw)

    async def text_json(
        self, *, system: str, user_text: str,
        schema_hint: str = "", temperature: float = 0.3,
    ) -> dict[str, Any]:
        full_prompt = system
        if schema_hint:
            full_prompt += f"\n\nReturn JSON matching this shape:\n{schema_hint}"
        full_prompt += f"\n\n{user_text}"

        def _call() -> str:
            resp = self._model().generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "response_mime_type": "application/json",
                },
            )
            return resp.text or "{}"

        raw = await asyncio.to_thread(_call)
        return _parse_json(raw)


# ---------- OpenAI ----------

class OpenAIBackend:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self._client = None
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI  # noqa: PLC0415
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                log.warning("openai SDK not installed")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def vision_json(
        self, *, system: str, user_text: str, images: list[bytes],
        schema_hint: str = "", temperature: float = 0.2,
    ) -> dict[str, Any]:
        assert self._client is not None
        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for img in images:
            b64 = base64.b64encode(img).decode("ascii")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
        full_system = system + (f"\n\nReturn JSON matching this shape:\n{schema_hint}" if schema_hint else "")
        resp = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": content},
            ],
        )
        return _parse_json(resp.choices[0].message.content or "{}")

    async def text_json(
        self, *, system: str, user_text: str,
        schema_hint: str = "", temperature: float = 0.3,
    ) -> dict[str, Any]:
        assert self._client is not None
        full_system = system + (f"\n\nReturn JSON matching this shape:\n{schema_hint}" if schema_hint else "")
        resp = await self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_text},
            ],
        )
        return _parse_json(resp.choices[0].message.content or "{}")


# ---------- Facade ----------

class LLMClient:
    def __init__(self) -> None:
        provider = get_settings().llm_provider.lower()
        if provider == "openai":
            self._backend: _Backend = OpenAIBackend()
        else:
            self._backend = GeminiBackend()
        self.provider = provider

    @property
    def is_available(self) -> bool:
        return self._backend.is_available

    async def vision_json(self, **kw) -> dict[str, Any]:
        return await self._backend.vision_json(**kw)

    async def text_json(self, **kw) -> dict[str, Any]:
        return await self._backend.text_json(**kw)


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else {}
    except json.JSONDecodeError:
        log.warning("LLM returned non-JSON, falling back to empty dict: %r", raw[:200])
        return {}


_singleton: LLMClient | None = None


def get_llm() -> LLMClient:
    global _singleton
    if _singleton is None:
        _singleton = LLMClient()
    return _singleton

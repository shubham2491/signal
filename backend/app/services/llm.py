"""Thin LLM client with vision support.

Two providers: Gemini (default, free tier) and OpenAI. Selected via
LLM_PROVIDER env var. Both expose the same `vision_json` / `text_json`
interface, returning a dict parsed from JSON.

All LLM calls are wrapped in a hard timeout (LLM_CALL_TIMEOUT_S) so a
slow upstream never blocks the analyze pipeline indefinitely — agents
catch the timeout and fall through to mock output.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Protocol

from app.config import get_settings

log = logging.getLogger(__name__)

# Hard per-call ceiling. Tuned for Gemini Flash p95 (~6-10s) with headroom.
LLM_CALL_TIMEOUT_S = 25.0
LLM_TEXT_TIMEOUT_S = 45.0  # text_json calls — keep tight so retry kicks in fast
LLM_RETRY_ATTEMPTS = 2     # initial + 1 retry; second attempt bumps temperature


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
        max_output_tokens: int = 4096,
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
                    "max_output_tokens": max_output_tokens,
                },
            )
            return resp.text or "{}"

        raw = await asyncio.to_thread(_call)
        return _parse_json(raw)

    async def text_json(
        self, *, system: str, user_text: str,
        schema_hint: str = "", temperature: float = 0.3,
        max_output_tokens: int = 4096,
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
                    "max_output_tokens": max_output_tokens,
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
        return await asyncio.wait_for(self._backend.vision_json(**kw), timeout=LLM_CALL_TIMEOUT_S)

    async def text_json(self, **kw) -> dict[str, Any]:
        """text_json with built-in retry. Each attempt is bounded by
        LLM_TEXT_TIMEOUT_S; on failure we bump temperature slightly and
        try again. Surfaces the final exception so the caller can route
        to a focused fallback."""
        base_temp = kw.pop("temperature", 0.3)
        last_err: Exception | None = None
        for attempt in range(LLM_RETRY_ATTEMPTS):
            temp = base_temp + (0.1 * attempt)
            try:
                return await asyncio.wait_for(
                    self._backend.text_json(**kw, temperature=temp),
                    timeout=LLM_TEXT_TIMEOUT_S,
                )
            except (asyncio.TimeoutError, Exception) as e:
                last_err = e
                log.warning("text_json attempt %d/%d failed (%s: %s)",
                            attempt + 1, LLM_RETRY_ATTEMPTS, type(e).__name__, e)
                if attempt + 1 < LLM_RETRY_ATTEMPTS:
                    await asyncio.sleep(0.4)  # tiny backoff
        # All attempts exhausted — re-raise so the caller decides what to do.
        raise last_err if last_err is not None else RuntimeError("text_json failed")


def _parse_json(raw: str) -> dict[str, Any]:
    try:
        out = json.loads(raw)
        return out if isinstance(out, dict) else {}
    except json.JSONDecodeError as e:
        # Try to recover from common truncation by trimming to the last valid
        # closing brace. Helps when max_output_tokens cut us off mid-field.
        recovered = _try_recover_truncated_json(raw)
        if recovered is not None:
            log.warning("LLM returned truncated JSON, recovered partial: %d keys", len(recovered))
            return recovered
        log.warning("LLM returned non-JSON (%s), raw[:400]=%r", e, raw[:400])
        return {}


def _try_recover_truncated_json(raw: str) -> dict[str, Any] | None:
    """Last-ditch: if JSON is cut off mid-value, find the last clean key/value
    boundary and close the object. Returns whatever we managed to parse."""
    if not raw or not raw.lstrip().startswith("{"):
        return None
    # Walk backwards from the end, looking for a position where we can close
    # the object cleanly (after a complete value, before any trailing junk).
    for end in range(len(raw) - 1, 0, -1):
        ch = raw[end]
        if ch in (",", "{"):
            continue
        if ch in ("}", "]", '"', "0123456789"[0]) or ch.isdigit() or ch.isalpha():
            try:
                # Trim any trailing comma, then close the outer object.
                candidate = raw[: end + 1].rstrip().rstrip(",") + "}"
                out = json.loads(candidate)
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                continue
    return None


_singleton: LLMClient | None = None


def get_llm() -> LLMClient:
    global _singleton
    if _singleton is None:
        _singleton = LLMClient()
    return _singleton

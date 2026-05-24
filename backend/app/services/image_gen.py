"""Image generation for design directions.

Two backends:
  - Pollinations.ai (default, free, no auth). URL-based: the prompt is
    encoded into the URL and the image is fetched lazily by the client.
    Generation typically completes in 6-15s on the Pollinations side.
  - fal.ai Flux Schnell (used when FAL_API_KEY is set). ~2-4s/image,
    sharper composition, costs ~$0.003/image.

The function returns a string URL the frontend can drop into an <Image>.
On any error we return an empty string — never raise — because image
generation is a nice-to-have, not a critical path for the brief.
"""
from __future__ import annotations

import asyncio
import logging
from urllib.parse import quote

import httpx

from app.config import get_settings
from app.schemas import Direction

log = logging.getLogger(__name__)

_IMAGE_TIMEOUT_S = 30.0
_FAL_ENDPOINT = "https://fal.run/fal-ai/flux/schnell"


def build_prompt(direction: Direction, *, palette: list[str], observation: str = "") -> str:
    """Compose a designer-quality prompt for the image model.

    Anchored on apparel product photography — flat-lay or e-commerce
    studio framing — so the output reads as a real product render rather
    than a fashion editorial."""
    palette_phrase = ", ".join(palette[:4]) if palette else "neutral palette"
    body = direction.description or direction.title
    # Strip generic INR / tier-1 boilerplate that doesn't help the image model.
    body = body.replace("Tier-1", "").replace("tier-1", "").replace("INR", "")
    parts = [
        f"editorial product shot of a {direction.title}",
        observation.lower() if observation else "",
        body,
        f"palette: {palette_phrase}",
        "natural daylight, soft shadows, e-commerce studio framing, full garment visible, no logos, no text overlays",
        "photorealistic, high detail, fashion lookbook quality",
    ]
    return ". ".join(p.strip() for p in parts if p.strip())[:900]


async def generate_image(prompt: str, *, seed: int | None = None) -> str:
    """Return a URL to a generated image, or '' on failure."""
    settings = get_settings()
    if not settings.image_gen_enabled:
        return ""

    if settings.fal_api_key:
        try:
            return await _fal_generate(prompt, settings.fal_api_key, seed=seed)
        except Exception as e:
            log.warning("fal.ai generation failed (%s: %s), falling back to Pollinations", type(e).__name__, e)

    return _pollinations_url(prompt, seed=seed)


async def generate_for_directions(
    directions: list[Direction], *, palette: list[str], observation: str = "",
) -> list[Direction]:
    """Run image generation in parallel for all directions. Mutates each
    direction with image_url + image_prompt and returns the list."""
    settings = get_settings()
    if not settings.image_gen_enabled:
        return directions

    async def _one(d: Direction, seed: int) -> Direction:
        prompt = build_prompt(d, palette=palette, observation=observation)
        url = await generate_image(prompt, seed=seed)
        d.image_url = url
        d.image_prompt = prompt
        return d

    tasks = [_one(d, seed=hash(d.label) % 100_000) for d in directions]
    return await asyncio.gather(*tasks)


# ────────────────────────────────────────────────────────────────────
# Backends
# ────────────────────────────────────────────────────────────────────

def _pollinations_url(prompt: str, *, seed: int | None = None, width: int = 768, height: int = 1024) -> str:
    """Pollinations encodes the prompt into a GET URL. The image is
    generated lazily on first fetch by the client — no API call from us
    is needed, which means no latency added to the brief generation."""
    encoded = quote(prompt, safe="")
    params = f"width={width}&height={height}&nologo=true&enhance=true"
    if seed is not None:
        params += f"&seed={seed}"
    return f"https://image.pollinations.ai/prompt/{encoded}?{params}"


async def _fal_generate(prompt: str, api_key: str, *, seed: int | None = None) -> str:
    headers = {"Authorization": f"Key {api_key}", "Content-Type": "application/json"}
    body = {
        "prompt": prompt,
        "image_size": "portrait_4_3",
        "num_inference_steps": 4,
        "num_images": 1,
        "enable_safety_checker": False,
    }
    if seed is not None:
        body["seed"] = seed

    async with httpx.AsyncClient(timeout=_IMAGE_TIMEOUT_S) as client:
        resp = await client.post(_FAL_ENDPOINT, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images") or []
        if not images:
            raise RuntimeError("fal.ai returned no images")
        return images[0].get("url", "")

"""Mode Detector.

Heuristic-first (cheap, fast, deterministic) with optional LLM tie-break.
The brief calls for auto-inference with a tiny confirmation in the UI.

Modes:
  product_study      — same product, different angles
  store_walk         — many distinct products, retail context
  moodboard          — inspiration dump, screenshots, mixed
  assortment_review  — small set of distinct products from one collection
  single_image       — single upload (fast path)
"""
from __future__ import annotations

from app.schemas import ImageRead, Mode


def detect(reads: list[ImageRead]) -> tuple[Mode, float]:
    n = len(reads)
    if n <= 1:
        return "single_image", 1.0

    categories = [r.attributes.category.lower().strip() for r in reads if r.attributes.category]
    unique_cats = {c for c in categories if c}

    # Strong product_study signal: most reads share the same category
    if categories:
        dominant = max(set(categories), key=categories.count)
        dominant_share = categories.count(dominant) / len(categories)
        if dominant_share >= 0.75 and n <= 6:
            return "product_study", round(dominant_share, 2)

    # Store walk: many images, many distinct categories
    if n >= 8 and len(unique_cats) >= max(3, n // 4):
        return "store_walk", 0.8

    # Moodboard: medium count, mixed aesthetics, no strong category dominance
    aesthetics = {r.attributes.aesthetic.lower().strip() for r in reads if r.attributes.aesthetic}
    if n >= 4 and len(unique_cats) >= 3 and len(aesthetics) >= 2:
        return "moodboard", 0.65

    # Default to assortment review for small distinct sets
    if n >= 2:
        return "assortment_review", 0.6

    return "single_image", 1.0

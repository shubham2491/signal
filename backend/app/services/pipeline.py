"""Sequential orchestration of the agent pipeline.

Single-group path: vision → mode → brand → search → commentary → recommendation.
Multi-group path: if the upload spans 2+ category_groups AND has ≥3 images,
we also run brand/search/commentary/recommendation per group and emit them
as `report.groups[]` while keeping the top-level brief as the overall view.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict

from app.agents import (
    brand_selector,
    commentary as commentary_agent,
    mode_detector,
    recommendation as recommendation_agent,
    search as search_agent,
    vision,
)
from app.services import image_gen
from app.schemas import (
    AnalysisReport,
    BrandSignal,
    Direction,
    GroupReport,
    ImageRead,
    Mode,
    VisionAttributes,
)

log = logging.getLogger(__name__)


_GROUP_LABELS = {
    "top": "Tops",
    "bottom": "Bottoms",
    "outerwear": "Outerwear",
    "dress": "Dresses & Jumpsuits",
    "ethnic": "Ethnic / Indo-fusion",
    "footwear": "Footwear",
    "accessory": "Accessories",
    "co_ord": "Co-ord Sets",
    "unknown": "Other",
}


async def analyze_brief(brief: str) -> AnalysisReport:
    """Run the pipeline from a free-text designer brief (no images).

    We synthesise a single ImageRead by treating the brief itself as the
    keyword soup the downstream agents expect, then skip vision/search
    and run brand_selector + commentary + recommendation. The mode is
    fixed to 'moodboard' since text briefs are most analogous to a
    mood-board input.
    """
    brief = brief.strip()
    if not brief:
        raise ValueError("brief is required")

    # Tokenise the brief into keywords. Keep short tokens (>=3 chars).
    raw_tokens = [t.strip().lower() for t in brief.replace(",", " ").replace(".", " ").split()]
    keywords = [t for t in raw_tokens if len(t) >= 3][:12]

    synthetic_read = ImageRead(
        index=0,
        attributes=VisionAttributes(
            category="",  # left blank; brief lives in aesthetic
            aesthetic=brief[:200],
            market_segment="mid-premium",
            notes=f"Synthesised from text brief: {brief[:200]}",
            shot_type="unknown",
            category_group="unknown",
        ),
        keywords=keywords,
    )
    reads = [synthetic_read]
    mode = "moodboard"  # type: ignore[assignment]

    top_level = await _build_section(reads, mode)

    return AnalysisReport(
        id=str(uuid.uuid4()),
        mode=mode,
        mode_confidence=1.0,
        image_count=0,
        observation=top_level["observation"],
        summary=top_level["summary"],
        brand_signals=[BrandSignal(**s) for s in top_level["brand_signals"]],
        commentary=top_level["commentary"],
        directions=[d if isinstance(d, Direction) else Direction(**d) for d in top_level["directions"]],
        keywords=top_level["keywords"],
        reads=reads,
        groups=[],
        palette=top_level.get("palette", []),
        price_strategy=top_level.get("price_strategy", ""),
        production_notes=top_level.get("production_notes", ""),
        merchandising=top_level.get("merchandising", ""),
        consumer=top_level.get("consumer", ""),
        why_now=top_level.get("why_now", ""),
        india_play=top_level.get("india_play", ""),
        price_anchor_inr=top_level.get("price_anchor_inr", ""),
        price_floor_inr=top_level.get("price_floor_inr", ""),
        price_target_inr=top_level.get("price_target_inr", ""),
        data_source=top_level.get("data_source", "live"),
    )


async def analyze(images: list[bytes]) -> AnalysisReport:
    if not images:
        raise ValueError("at least one image is required")

    reads = await vision.run(images)
    mode, confidence = mode_detector.detect(reads)

    # Top-level brief covers the whole upload (the user always gets this).
    top_level = await _build_section(reads, mode)

    # Per-group breakdown — kept lightweight so it doesn't blow latency.
    # Only kicks in when 2+ category groups are present AND total ≥ 4 images,
    # and is capped to the 2 largest groups so we never exceed Gemini free-tier
    # rate limits.
    groups: list[GroupReport] = []
    grouped = _group_by_category(reads)
    if len(grouped) >= 2 and len(images) >= 4:
        groups = await _build_group_reports(grouped, mode)

    return AnalysisReport(
        id=str(uuid.uuid4()),
        mode=mode,
        mode_confidence=confidence,
        image_count=len(images),
        observation=top_level["observation"],
        summary=top_level["summary"],
        brand_signals=[BrandSignal(**s) for s in top_level["brand_signals"]],
        commentary=top_level["commentary"],
        directions=[d if isinstance(d, Direction) else Direction(**d) for d in top_level["directions"]],
        keywords=top_level["keywords"],
        reads=reads,
        groups=groups,
        palette=top_level.get("palette", []),
        price_strategy=top_level.get("price_strategy", ""),
        production_notes=top_level.get("production_notes", ""),
        merchandising=top_level.get("merchandising", ""),
        consumer=top_level.get("consumer", ""),
        why_now=top_level.get("why_now", ""),
        india_play=top_level.get("india_play", ""),
        price_anchor_inr=top_level.get("price_anchor_inr", ""),
        price_floor_inr=top_level.get("price_floor_inr", ""),
        price_target_inr=top_level.get("price_target_inr", ""),
        data_source=top_level.get("data_source", "live"),
    )


async def _build_section(reads: list[ImageRead], mode: Mode) -> dict:
    """Run the brand → search → commentary → recommendation chain for a
    set of reads. Returns the dict-shape the AnalysisReport expects."""
    brands = brand_selector.select(reads, top_k=5)
    search_results = await search_agent.run(brands, reads)
    commentary = await commentary_agent.run(
        reads=reads, brands=brands, search_results=search_results, mode=mode,
    )
    directions = await recommendation_agent.run(
        observation=commentary["observation"],
        commentary=commentary["commentary"],
        keywords=commentary["keywords"],
    )

    # Attach a generated product image per direction. Pollinations URLs
    # are lazy (client fetches on demand) so this adds zero latency to
    # the brief. fal.ai backend would add ~2-4s/image.
    try:
        directions = await image_gen.generate_for_directions(
            directions,
            palette=commentary.get("palette", []),
            observation=commentary["observation"],
        )
    except Exception as e:
        log.warning("image generation failed (%s: %s) — proceeding without product images",
                    type(e).__name__, e)

    return {
        "observation": commentary["observation"],
        "summary": commentary["summary"],
        "brand_signals": commentary["brand_signals"],
        "commentary": commentary["commentary"],
        "directions": directions,
        "keywords": commentary["keywords"],
        "palette": commentary.get("palette", []),
        "price_strategy": commentary.get("price_strategy", ""),
        "production_notes": commentary.get("production_notes", ""),
        "merchandising": commentary.get("merchandising", ""),
        "consumer": commentary.get("consumer", ""),
        "why_now": commentary.get("why_now", ""),
        "india_play": commentary.get("india_play", ""),
        "price_anchor_inr": commentary.get("price_anchor_inr", ""),
        "price_floor_inr": commentary.get("price_floor_inr", ""),
        "price_target_inr": commentary.get("price_target_inr", ""),
        "data_source": commentary.get("data_source", "live"),
    }


def _group_by_category(reads: list[ImageRead]) -> dict[str, list[ImageRead]]:
    grouped: dict[str, list[ImageRead]] = defaultdict(list)
    for r in reads:
        grouped[r.attributes.category_group or "unknown"].append(r)
    # Drop the unknown bucket only if it's the minority — otherwise keep it
    # so the user still gets a section for it.
    if "unknown" in grouped and len(grouped) > 1 and len(grouped["unknown"]) == 1:
        # If only 1 lone unknown image, absorb it into the largest known group.
        largest = max((g for g in grouped if g != "unknown"), key=lambda g: len(grouped[g]))
        grouped[largest].append(grouped["unknown"][0])
        del grouped["unknown"]
    return dict(grouped)


MAX_SUB_GROUPS = 2  # cap to keep latency + rate-limit budget tight


async def _build_group_reports(
    grouped: dict[str, list[ImageRead]], mode: Mode,
) -> list[GroupReport]:
    """Run a LIGHTWEIGHT sub-pipeline per category group.

    Lightweight = brand_select (free, sync) + commentary only. We skip
    search (Tavily) and recommendation_agent for sub-groups: directions
    live on the top-level brief, and brand DNA is enough to ground a
    short per-category commentary. This cuts the multi-group cost from
    ~5 LLM calls × N groups down to 1 × min(N, MAX_SUB_GROUPS).
    """
    # Largest categories first, capped to MAX_SUB_GROUPS.
    items = sorted(grouped.items(), key=lambda kv: -len(kv[1]))[:MAX_SUB_GROUPS]

    tasks = [_build_group_section(reads, mode) for _, reads in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[GroupReport] = []
    for (group_id, sub_reads), result in zip(items, results):
        if isinstance(result, Exception):
            log.warning("group %s failed: %s", group_id, result)
            continue
        out.append(GroupReport(
            group_id=group_id,  # type: ignore[arg-type]
            label=_GROUP_LABELS.get(group_id, group_id.title()),
            image_indices=[r.index for r in sub_reads],
            observation=result["observation"],
            summary=result["summary"],
            brand_signals=[BrandSignal(**s) for s in result["brand_signals"]],
            commentary=result["commentary"],
            directions=[],  # directions only at the top level
            keywords=result["keywords"],
        ))
    return out


async def _build_group_section(reads: list[ImageRead], mode: Mode) -> dict:
    """Lightweight per-group flow: brand_select + commentary only.
    No search, no recommendations — keeps latency bounded."""
    brands = brand_selector.select(reads, top_k=4)
    # Empty search_results forces commentary to reason from brand DNA only.
    commentary = await commentary_agent.run(
        reads=reads, brands=brands, search_results={}, mode=mode,
    )
    return {
        "observation": commentary["observation"],
        "summary": commentary["summary"],
        "brand_signals": commentary["brand_signals"],
        "commentary": commentary["commentary"],
        "keywords": commentary["keywords"],
    }

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
from app.schemas import (
    AnalysisReport,
    BrandSignal,
    Direction,
    GroupReport,
    ImageRead,
    Mode,
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


async def analyze(images: list[bytes]) -> AnalysisReport:
    if not images:
        raise ValueError("at least one image is required")

    reads = await vision.run(images)
    mode, confidence = mode_detector.detect(reads)

    # Top-level brief covers the whole upload (the user always gets this).
    top_level = await _build_section(reads, mode)

    # Per-group breakdown only kicks in when there's meaningful diversity.
    groups: list[GroupReport] = []
    grouped = _group_by_category(reads)
    if len(grouped) >= 2 and len(images) >= 3:
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
    return {
        "observation": commentary["observation"],
        "summary": commentary["summary"],
        "brand_signals": commentary["brand_signals"],
        "commentary": commentary["commentary"],
        "directions": directions,
        "keywords": commentary["keywords"],
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


async def _build_group_reports(
    grouped: dict[str, list[ImageRead]], mode: Mode,
) -> list[GroupReport]:
    """Run a sub-pipeline per category group, concurrently."""
    items = list(grouped.items())
    tasks = [_build_section(reads, mode) for _, reads in items]
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
            directions=[d if isinstance(d, Direction) else Direction(**d) for d in result["directions"]],
            keywords=result["keywords"],
        ))
    # Sort by image count desc so the biggest category leads.
    out.sort(key=lambda g: -len(g.image_indices))
    return out

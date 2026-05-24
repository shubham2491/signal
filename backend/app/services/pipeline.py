"""Sequential orchestration of the agent pipeline.

This is intentionally not a fancy orchestrator — the brief allows a
sequential implementation for the hackathon. Each step is small and replaceable.
"""
from __future__ import annotations

import logging
import uuid

from app.agents import (
    brand_selector,
    commentary as commentary_agent,
    mode_detector,
    recommendation as recommendation_agent,
    search as search_agent,
    vision,
)
from app.schemas import AnalysisReport, Direction, BrandSignal

log = logging.getLogger(__name__)


async def analyze(images: list[bytes]) -> AnalysisReport:
    if not images:
        raise ValueError("at least one image is required")

    reads = await vision.run(images)
    mode, confidence = mode_detector.detect(reads)
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

    return AnalysisReport(
        id=str(uuid.uuid4()),
        mode=mode,
        mode_confidence=confidence,
        image_count=len(images),
        observation=commentary["observation"],
        summary=commentary["summary"],
        brand_signals=[BrandSignal(**s) for s in commentary["brand_signals"]],
        commentary=commentary["commentary"],
        directions=directions if isinstance(directions[0], Direction) else [Direction(**d) for d in directions],
        keywords=commentary["keywords"],
        reads=reads,
    )

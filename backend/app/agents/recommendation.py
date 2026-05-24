"""Recommendation Agent.

Produces three actionable design directions: Safe Commercial, Trend Forward,
Differentiated. Each is a 2-3 sentence designer brief, not a buzzword list.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas import Direction
from app.services.llm import get_llm

log = logging.getLogger(__name__)


SYSTEM = """You are SIGNAL's Recommendation Agent for Indian fashion
designers and buyers (value and mid-premium retail — Zudio, Westside,
Pantaloons, Allen Solly, AND, Snitch, Biba, Wrogn, etc.).

Given an observation and commentary, propose three design directions
for the Indian floor set. Each direction is a tight, opinionated brief
a designer could hand to a sampling team — concrete fabric / silhouette
/ palette / INR price-band beats abstract trend talk.

Reference Indian realities where relevant: summer-weight fabrics,
festive/wedding occasion windows, tier-1 vs tier-2/3 distribution,
ethnic/indo-fusion crossover potential, INR 499-1,999 (value) vs
INR 1,999-4,999 (mid-premium) price thinking. Never anchor to European
luxury houses.

Labels are fixed: 'Safe Commercial', 'Trend Forward', 'Differentiated Route'.
""".strip()

SCHEMA = """
{
  "directions": [
    {"label": "Safe Commercial",       "title": "string (3-6 words)", "description": "string (2-3 sentences)"},
    {"label": "Trend Forward",          "title": "string (3-6 words)", "description": "string (2-3 sentences)"},
    {"label": "Differentiated Route",   "title": "string (3-6 words)", "description": "string (2-3 sentences)"}
  ]
}
""".strip()


async def run(*, observation: str, commentary: str, keywords: list[str]) -> list[Direction]:
    llm = get_llm()
    if not llm.is_available:
        return _mock(observation, keywords)

    user_text = f"""
Observation: {observation}
Commentary:  {commentary}
Keywords:    {", ".join(keywords) or "—"}

Write three directions.
""".strip()

    try:
        data: dict[str, Any] = await llm.text_json(
            system=SYSTEM, user_text=user_text, schema_hint=SCHEMA, temperature=0.6,
        )
    except Exception as e:
        log.warning("Recommendation LLM call failed, using mock: %s", e)
        return _mock(observation, keywords)

    out: list[Direction] = []
    expected = ["Safe Commercial", "Trend Forward", "Differentiated Route"]
    raw = {d.get("label"): d for d in (data.get("directions") or []) if isinstance(d, dict)}
    for label in expected:
        d = raw.get(label) or {}
        out.append(Direction(
            label=label,  # type: ignore[arg-type]
            title=str(d.get("title", label))[:80],
            description=str(d.get("description", ""))[:400] or _fallback_desc(label, observation),
        ))
    return out


def _mock(observation: str, keywords: list[str]) -> list[Direction]:
    kw = ", ".join(keywords[:3]) if keywords else "neutral palette, boxy fit"
    return [
        Direction(
            label="Safe Commercial",
            title=f"Hero {observation}",
            description=f"Run a tight capsule of {kw} pieces at INR 799-1,299. Volume play for tier-1 metros — Zudio / Pantaloons positioning. Stick to proven silhouettes; this is shelf-velocity, not noise.",
        ),
        Direction(
            label="Trend Forward",
            title="Push the proportion",
            description="Take the same direction and exaggerate one variable — sleeve length, drop shoulder, or hem treatment. Limited drops at INR 1,799-2,499, Snitch / Wrogn / Westside price-band. Tier-1 first, watch sell-through before tier-2 push.",
        ),
        Direction(
            label="Differentiated Route",
            title="Indo-fusion craft story",
            description="Lean into handloom textures, hand-block prints, or sustainable cotton — Nicobar / FabIndia adjacency. Higher margin, lower velocity. Festive window timing maximises pull.",
        ),
    ]


def _fallback_desc(label: str, observation: str) -> str:
    return f"Direction informed by '{observation}'."

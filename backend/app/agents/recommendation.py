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


SYSTEM = """You are SIGNAL's Recommendation Agent for fashion designers.

Given an observation and commentary, propose three design directions. Each
direction is a tight, opinionated brief a designer could hand to a sampling
team. Concrete fabric / silhouette / palette beats abstract trend talk.

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
            description=f"Run a tight capsule of {kw} pieces at a high-street price point. Stick to proven silhouettes — this is volume, not noise.",
        ),
        Direction(
            label="Trend Forward",
            title="Push the proportion",
            description="Take the same direction and exaggerate one variable — sleeve length, drop shoulder, or hem treatment. Limited drops, premium fabric.",
        ),
        Direction(
            label="Differentiated Route",
            title="Craft + earthtone story",
            description="Lean into texture-led knits, hand-feel finishes, undyed naturals. Sells the brand story; lower velocity, higher margin.",
        ),
    ]


def _fallback_desc(label: str, observation: str) -> str:
    return f"Direction informed by '{observation}'."

"""Recommendation Agent.

Produces three actionable design directions sized for an Indian
fast-fashion designer (Zudio / Westside / Pantaloons level), each with
an INR price band, production complexity tag, and a season/timing call.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas import Direction
from app.services.llm import get_llm

log = logging.getLogger(__name__)


SYSTEM = """You are SIGNAL's Recommendation Agent for an Indian fast-fashion
designer (Zudio / Westside / Pantaloons-level retail).

Given the observation, commentary, and keywords, write THREE directions
the designer could hand directly to a sampling team. Each must be
concrete on:
  - the silhouette / fabric / palette bet
  - an INR price-band sized for the Indian floor (typically INR 499-1,799)
  - production complexity (easy / medium / hard at scale)
  - season / festive window timing

The three labels are FIXED: 'Safe Commercial', 'Trend Forward',
'Differentiated Route'. Use Indian retail vocabulary (tier-1 metros,
tier-2/3 carry-over, festive cycles, summer-weight fabrics). Never
anchor to European luxury houses.

Each direction's description is 2-3 sentences. Be designer-specific:
fabric, gsm / weave, trim callouts, color story — not abstract trend
talk.
""".strip()

SCHEMA = """
{
  "directions": [
    {
      "label": "Safe Commercial",
      "title": "string (3-6 words)",
      "description": "string (2-3 sentences with fabric / palette / trim specifics)",
      "price_band_inr": "string (e.g. 'INR 799-1,099')",
      "complexity": "easy | medium | hard",
      "timing": "string (e.g. 'SS26 — drop in Feb for tier-1, May for tier-2/3')"
    },
    {"label": "Trend Forward", "...": "same shape"},
    {"label": "Differentiated Route", "...": "same shape"}
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

Write three directions. Each MUST include price_band_inr, complexity,
and timing — they're the difference between a brief and a wish list.
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
        complexity = str(d.get("complexity", "")).strip().lower()
        if complexity not in ("easy", "medium", "hard"):
            complexity = ""
        out.append(Direction(
            label=label,  # type: ignore[arg-type]
            title=str(d.get("title", label))[:80],
            description=str(d.get("description", ""))[:600] or _fallback_desc(label, observation),
            price_band_inr=str(d.get("price_band_inr", ""))[:60],
            complexity=complexity,  # type: ignore[arg-type]
            timing=str(d.get("timing", ""))[:120],
        ))
    return out


def _mock(observation: str, keywords: list[str]) -> list[Direction]:
    kw = ", ".join(keywords[:3]) if keywords else "neutral palette, boxy fit"
    return [
        Direction(
            label="Safe Commercial",
            title=f"Hero {observation}",
            description=(
                f"Capsule of {kw} pieces in 200 gsm cotton jersey, neutral palette "
                f"(ecru, rust, off-white). Tier-1 metro volume play, deep stacks on the lead "
                f"colors. Run the standard hem and chest-placement print."
            ),
            price_band_inr="INR 799-1,099",
            complexity="easy",  # type: ignore[arg-type]
            timing="Spring drop, Feb for tier-1; carry-over to tier-2/3 by May",
        ),
        Direction(
            label="Trend Forward",
            title="Push the proportion",
            description=(
                "Exaggerate one variable from the safe capsule — drop shoulder by "
                "1cm, lengthen sleeve to fingertip, or move to a heavier 240 gsm "
                "brushed jersey. Limited drop in tier-1 metros; watch sell-through "
                "before committing to tier-2 broadcast."
            ),
            price_band_inr="INR 1,299-1,799",
            complexity="medium",  # type: ignore[arg-type]
            timing="Early festive window — late August to early September",
        ),
        Direction(
            label="Differentiated Route",
            title="Indo-fusion craft story",
            description=(
                "Bring in handloom textures, hand-block prints, or sustainable cotton — "
                "Nicobar / FabIndia adjacency. Higher margin, lower velocity, but builds "
                "brand cred. Festive window timing maximises pull."
            ),
            price_band_inr="INR 1,499-1,999",
            complexity="hard",  # type: ignore[arg-type]
            timing="Festive (Oct-Nov) and wedding (Nov-Feb) windows",
        ),
    ]


def _fallback_desc(label: str, observation: str) -> str:
    return f"Direction informed by '{observation}'."

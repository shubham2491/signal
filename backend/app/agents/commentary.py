"""Commentary Agent.

Takes pooled vision facets + per-brand search snippets and produces:
  - an editorial observation (one phrase, eg "Oversized Minimal Casualwear")
  - a short summary line
  - brand signals (Strong / Adjacent / Moderate / Weak) with rationale
  - a short market commentary paragraph (1-3 sentences, no essays)
  - top keywords
"""
from __future__ import annotations

import logging
from typing import Any

from app.data.brands import Brand
from app.schemas import BrandSignal, ImageRead, Mode
from app.services.llm import get_llm

log = logging.getLogger(__name__)


SYSTEM = """You are SIGNAL's Commentary Agent, writing for designers and
buyers in INDIAN fashion retail (value and mid-premium tiers).

Brand signals you receive may include both Indian brands (Zudio,
Westside, Snitch, AND, Biba, Allen Solly, etc.) AND globally accessible
brands present/benchmarked in India (Zara, COS, Uniqlo, Mango,
Massimo Dutti, etc.). Reference any of them where useful.

COMMENTARY IS ALWAYS INDIAN-CONTEXT. Frame everything from the lens of
Indian retail — never frame from a US/EU/UK consumer lens. Compare to
how the floor would land at Indian tier-1 metros vs tier-2/3 cities.

NEVER reference maison-tier luxury (Prada, Gucci, Chanel, LV, Hermes,
Loewe, Bottega, Balenciaga, Jacquemus, Acne, Miu Miu). Not useful.

MANDATORY in every commentary:
  1. An explicit INR price-band call (e.g. "INR 999-1,799 sweet spot",
     "premium-mass at INR 2,499-3,999", "value tier at INR 499-899").
     The band should reflect where this product would actually retail in
     India, not the global price.
  2. A tier-1 vs tier-2/3 distribution take — does this work pan-India
     or stay metro-only?
  3. A seasonal/festive timing note where the inputs allow it
     (summer-weight, festive window, wedding occasion, monsoon, etc.).

Be editorial, not analytical. No SaaS jargon, no bullet-point essays.
2-4 short sentences total. Always identity-blind.
""".strip()

SCHEMA = """
{
  "observation": "string (3-7 words, editorial)",
  "summary": "string (one sentence, <= 22 words)",
  "brand_signals": [
    {
      "brand": "string (must be one of the input brand names)",
      "similarity": "Strong | Adjacent | Moderate | Weak",
      "rationale": "string (<= 18 words)",
      "citations": ["url"]
    }
  ],
  "commentary": "string (1-3 sentences, plain prose)",
  "keywords": ["string"]
}
""".strip()


async def run(
    *,
    reads: list[ImageRead],
    brands: list[Brand],
    search_results: dict[str, list[dict]],
    mode: Mode,
) -> dict[str, Any]:
    llm = get_llm()
    pooled = _pool(reads)
    brand_block = _brand_block(brands, search_results)

    if not llm.is_available:
        return _mock_commentary(brands, pooled)

    user_text = f"""
Mode: {mode}
Image count: {len(reads)}

Vision facets (pooled across images):
  aesthetics: {", ".join(pooled["aesthetics"]) or "—"}
  categories: {", ".join(pooled["categories"]) or "—"}
  colors:     {", ".join(pooled["colors"]) or "—"}
  silhouettes:{", ".join(pooled["silhouettes"]) or "—"}
  market:     {", ".join(pooled["segments"]) or "—"}
  keywords:   {", ".join(pooled["keywords"]) or "—"}

Candidate Indian-retail brands with recent snippets (cite URLs you use):

{brand_block}

Write the brief.
- Commentary frames EVERYTHING from Indian retail context. MUST include
  an explicit INR price band, a tier-1 vs tier-2/3 distribution take,
  and a seasonal/festive timing note where facets allow.
- Brand signals must cover ALL candidate brands. For each: Strong =
  input could plausibly be from that brand's current floor at its
  Indian price-point. Adjacent = different positioning, same direction.
  Moderate = some shared facets. Weak = mostly divergent.
- Brand signal rationales can reference either Indian floor positioning
  or how a global brand (e.g. Zara/Uniqlo) would benchmark in India.
""".strip()

    try:
        data = await llm.text_json(system=SYSTEM, user_text=user_text, schema_hint=SCHEMA)
    except Exception as e:
        log.warning("Commentary LLM call failed, using mock: %s", e)
        return _mock_commentary(brands, pooled)

    data = _sanitize(data, brands)
    return data


def _pool(reads: list[ImageRead]) -> dict[str, list[str]]:
    aesthetics, categories, colors, silhouettes, segments, keywords = [], [], [], [], [], []
    for r in reads:
        a = r.attributes
        if a.aesthetic:
            aesthetics.append(a.aesthetic)
        if a.category:
            categories.append(a.category)
        colors.extend(a.colors)
        if a.silhouette:
            silhouettes.append(a.silhouette)
        if a.market_segment:
            segments.append(a.market_segment)
        keywords.extend(r.keywords)
    return {
        "aesthetics": _uniq(aesthetics),
        "categories": _uniq(categories),
        "colors": _uniq(colors),
        "silhouettes": _uniq(silhouettes),
        "segments": _uniq(segments),
        "keywords": _uniq(keywords),
    }


def _uniq(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        k = x.lower().strip()
        if k and k not in seen:
            seen.add(k)
            out.append(x)
    return out


def _brand_block(brands: list[Brand], results: dict[str, list[dict]]) -> str:
    blocks: list[str] = []
    for b in brands:
        hits = results.get(b.name, []) or []
        if hits:
            lines = [f"  - {h['title']} ({h['url']}): {h['snippet'][:160]}" for h in hits[:3]]
            blocks.append(f"{b.name} ({b.segment}) — {b.domain}\n" + "\n".join(lines))
        else:
            blocks.append(f"{b.name} ({b.segment}) — {b.domain}\n  (no fresh snippets — reason from brand DNA)")
    return "\n\n".join(blocks)


def _sanitize(data: dict[str, Any], brands: list[Brand]) -> dict[str, Any]:
    allowed_brands = {b.name for b in brands}
    sigs_raw = data.get("brand_signals") or []
    sigs: list[BrandSignal] = []
    seen: set[str] = set()
    for s in sigs_raw:
        name = str(s.get("brand", "")).strip()
        if name not in allowed_brands or name in seen:
            continue
        seen.add(name)
        sim = str(s.get("similarity", "Moderate")).strip().title()
        if sim not in ("Strong", "Adjacent", "Moderate", "Weak"):
            sim = "Moderate"
        sigs.append(BrandSignal(
            brand=name,
            similarity=sim,  # type: ignore[arg-type]
            rationale=str(s.get("rationale", ""))[:200],
            citations=[c for c in (s.get("citations") or []) if isinstance(c, str)][:3],
        ))
    # Fill missing brands with weak placeholder so the UI shows the full shortlist
    for b in brands:
        if b.name not in seen:
            sigs.append(BrandSignal(
                brand=b.name, similarity="Weak",
                rationale=f"Limited overlap with {b.name}'s current floor set.",
                citations=[],
            ))
    return {
        "observation": str(data.get("observation", "")).strip() or "Editorial Read",
        "summary": str(data.get("summary", "")).strip(),
        "brand_signals": [s.model_dump() for s in sigs],
        "commentary": str(data.get("commentary", "")).strip(),
        "keywords": [str(k) for k in (data.get("keywords") or [])][:10],
    }


def _mock_commentary(brands: list[Brand], pooled: dict[str, list[str]]) -> dict[str, Any]:
    obs = " ".join(pooled["aesthetics"][:2] + pooled["categories"][:1]).title() or "Casual Mid-Premium Read"
    sigs = []
    aesthetic_phrase = pooled["aesthetics"][0] if pooled["aesthetics"] else "casual"
    for i, b in enumerate(brands):
        sim = ["Strong", "Adjacent", "Moderate", "Moderate", "Weak"][min(i, 4)]
        sigs.append(BrandSignal(
            brand=b.name, similarity=sim,  # type: ignore[arg-type]
            rationale=f"{b.name} runs similar {aesthetic_phrase} silhouettes on its current India floor.",
            citations=[],
        ).model_dump())
    return {
        "observation": obs,
        "summary": "Oversized cotton silhouettes in a muted palette — mid-premium casualwear read.",
        "brand_signals": sigs,
        "commentary": (
            "Reads as mid-premium casualwear — sits comfortably between Zudio's "
            "fast-trend floor and Snitch/Wrogn's premium-youth positioning. "
            "Tier-1 metro core, with strong potential carry-over to tier-2 cities "
            "in the next refresh cycle. INR 999-1,799 sweet spot."
        ),
        "keywords": pooled["keywords"][:8] or ["oversized", "neutral", "casual", "drop-shoulder"],
    }

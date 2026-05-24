"""Commentary Agent.

Builds the actionable brief for an Indian fast-fashion designer.

Persona: a designer at Zudio / Westside / Pantaloons-level who wants to
translate ASPIRATIONAL global looks (Zara / H&M / Uniqlo / COS / Mango)
into AFFORDABLE Indian floor sets (INR 499-1,799).

Output adds four actionable structured fields beyond the editorial brief:
  - palette          : 4-6 named trade colors
  - price_strategy   : INR price ladder (aspirational anchor → Indian competitive → recommended)
  - production_notes : fabric / complexity / trim spec
  - merchandising    : adjacent SKUs + shelf strategy
"""
from __future__ import annotations

import logging
from typing import Any

from app.data.brands import Brand
from app.schemas import BrandSignal, ImageRead, Mode
from app.services.llm import get_llm

log = logging.getLogger(__name__)


SYSTEM = """You are SIGNAL's Commentary Agent for an Indian fast-fashion
designer working at Zudio / Westside / Pantaloons-level retail.

Your reader wants to translate ASPIRATIONAL global looks (Zara, H&M,
Uniqlo, COS, Mango, Massimo Dutti, Arket, & Other Stories, etc.) into
AFFORDABLE Indian floor sets. The Indian competitive shelf is Zudio,
Westside, Pantaloons, Max, Reliance Trends, Bewakoof, The Souled Store.

Every brief must speak from INDIAN retail context: tier-1 metros vs
tier-2/3, festive / wedding / summer-weight cycles, INR price-bands
(typically 499-1,799 for the value-to-mid floor), pan-India distribution.

NEVER reference maison luxury (Prada, Gucci, Chanel, Loewe, etc).
NEVER reference Indian mid-tier branded labels not in the candidate set
(Snitch, Wrogn, Allen Solly, AND, Biba, etc.) — they aren't useful
comparators for this audience.

Produce DETAILED, ACTIONABLE output across these fields:

1. observation: 3-7 word editorial headline.
2. summary: one tight sentence (≤24 words) that names the look.
3. brand_signals: one entry per candidate brand. Strong = could plausibly
   be from that brand's current floor; Adjacent = same direction,
   different positioning; Moderate = some shared facets; Weak =
   divergent. Rationale ≤22 words, anchored to either the global
   reference DNA or the Indian competitive reality.
4. commentary: 3-5 sentences. Must call out (a) what's working
   commercially, (b) the tier-1 vs tier-2/3 distribution take, (c)
   season / festive timing.
5. palette: 4-6 specific named trade colors ("ecru", "rust", "kerala
   green", "burnt sienna" — never "light" / "dark" / "blue").
6. price_strategy: a short paragraph (2-3 sentences) framing the INR
   price ladder. MUST include three numbers: the aspirational anchor
   price (e.g. "Zara INR 2,990"), the Indian competitive shelf price
   (e.g. "Zudio INR 599-799"), and your RECOMMENDED MRP for the
   designer's floor (e.g. "INR 999-1,299"). End with a one-line gap
   reasoning — what's the margin / volume bet.
7. production_notes: 1-2 sentences naming the fabric spec
   (e.g. "200 gsm cotton jersey, brushed interior"), production
   complexity (easy / medium / hard at scale), and the 1-2 critical
   trim callouts that make the look.
8. merchandising: 1-2 sentences on adjacent SKUs to drop alongside (so
   the floor reads as a story, not a one-off) and a shelf-stack note.
9. keywords: 6-10 short tokens a designer could feed into trend search.
""".strip()

SCHEMA = """
{
  "observation": "string (3-7 words)",
  "summary": "string (one sentence, <= 24 words)",
  "brand_signals": [
    {
      "brand": "string (must be one of the input brand names)",
      "similarity": "Strong | Adjacent | Moderate | Weak",
      "rationale": "string (<= 22 words)",
      "citations": ["url"]
    }
  ],
  "commentary": "string (3-5 sentences, plain prose)",
  "palette": ["string (named trade color, 4-6 total)"],
  "price_strategy": "string (2-3 sentences with three INR numbers)",
  "production_notes": "string (1-2 sentences: fabric + complexity + trims)",
  "merchandising": "string (1-2 sentences: adjacent SKUs + shelf note)",
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
  aesthetics:  {", ".join(pooled["aesthetics"]) or "—"}
  categories:  {", ".join(pooled["categories"]) or "—"}
  colors:      {", ".join(pooled["colors"]) or "—"}
  silhouettes: {", ".join(pooled["silhouettes"]) or "—"}
  market:      {", ".join(pooled["segments"]) or "—"}
  keywords:    {", ".join(pooled["keywords"]) or "—"}

Candidate brand set (mix of global aspirational + Indian competitive shelf):

{brand_block}

Write the full actionable brief. Every section must be specific and
designer-usable. Cite at least one web URL in brand_signals citations
where it grounds your call.
""".strip()

    try:
        data = await llm.text_json(system=SYSTEM, user_text=user_text, schema_hint=SCHEMA)
    except Exception as e:
        log.warning("Commentary LLM call failed, using mock: %s", e)
        return _mock_commentary(brands, pooled)

    return _sanitize(data, brands, pooled)


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
        tier_label = {
            "global_aspirational": "ASPIRATIONAL ANCHOR",
            "india_competitive":   "INDIAN COMPETITIVE SHELF",
            "india_premium":       "INDIAN PREMIUM / CRAFT",
        }.get(b.segment, b.segment.upper())
        if hits:
            lines = [f"  - {h['title']} ({h['url']}): {h['snippet'][:160]}" for h in hits[:3]]
            blocks.append(f"{b.name} [{tier_label}] — {b.domain}\n" + "\n".join(lines))
        else:
            blocks.append(f"{b.name} [{tier_label}] — {b.domain}\n  (no fresh snippets — reason from brand DNA)")
    return "\n\n".join(blocks)


def _sanitize(data: dict[str, Any], brands: list[Brand], pooled: dict[str, list[str]]) -> dict[str, Any]:
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
            rationale=str(s.get("rationale", ""))[:240],
            citations=[c for c in (s.get("citations") or []) if isinstance(c, str)][:3],
        ))
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
        "palette": [str(c) for c in (data.get("palette") or [])][:8] or pooled["colors"][:6],
        "price_strategy": str(data.get("price_strategy", "")).strip(),
        "production_notes": str(data.get("production_notes", "")).strip(),
        "merchandising": str(data.get("merchandising", "")).strip(),
        "keywords": [str(k) for k in (data.get("keywords") or [])][:10],
    }


def _mock_commentary(brands: list[Brand], pooled: dict[str, list[str]]) -> dict[str, Any]:
    obs = " ".join(pooled["aesthetics"][:2] + pooled["categories"][:1]).title() or "Quiet Casual Mid-Premium"
    sigs = []
    aesthetic_phrase = pooled["aesthetics"][0] if pooled["aesthetics"] else "casual contemporary"
    for i, b in enumerate(brands):
        sim = ["Strong", "Adjacent", "Moderate", "Moderate", "Weak"][min(i, 4)]
        if b.segment == "global_aspirational":
            rat = f"{b.name}'s current floor leans {aesthetic_phrase} — strong DNA to translate."
        elif b.segment == "india_competitive":
            rat = f"Where this would land on {b.name}'s floor at INR 599-999 today."
        else:
            rat = f"{b.name} runs the craft adjacency if the read tilts indo-fusion."
        sigs.append(BrandSignal(
            brand=b.name, similarity=sim,  # type: ignore[arg-type]
            rationale=rat, citations=[],
        ).model_dump())
    return {
        "observation": obs,
        "summary": "Aspirational global silhouettes ready to translate into an INR 999-1,299 Indian floor.",
        "brand_signals": sigs,
        "commentary": (
            "Reads like a Zara / Mango current floor moment — proportions and palette are aspirational "
            "but the underlying construction is well within Zudio / Westside's manufacturing reach. "
            "Tier-1 metros lead on drop; tier-2/3 follows in 4-6 weeks once the silhouette is validated. "
            "Best window is the late-summer to early-festive bridge."
        ),
        "palette": pooled["colors"][:6] or ["ecru", "rust", "olive", "off-white", "burnt sienna"],
        "price_strategy": (
            "Aspirational anchor: Zara INR 2,990. Indian competitive shelf: "
            "Zudio / Westside INR 599-899. Recommended MRP for this floor: "
            "INR 999-1,299. The 30-40% gap to Zara is the headroom; matching "
            "Zudio at INR 599 sacrifices margin without buying meaningful share."
        ),
        "production_notes": (
            "200 gsm cotton jersey, brushed interior; medium complexity to "
            "manufacture at scale. Critical trims: ribbed neck tape, centered "
            "chest placement print, double-needle hem."
        ),
        "merchandising": (
            "Drop alongside a wide-leg cargo and an open-weave knit so the "
            "floor reads as a complete capsule, not a one-off. Stack 3 colors "
            "deep on the lead SKU; the support SKUs in 2."
        ),
        "keywords": pooled["keywords"][:8] or ["oversized", "neutral", "minimal", "casual", "contemporary"],
    }

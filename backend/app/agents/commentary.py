"""Commentary Agent.

Translates an international aspirational read into an India-launch brief.

Reader: an Indian fast-fashion designer working at the value-to-mid floor
(Zudio / Westside / Pantaloons level). The reader already lives on that
shelf — SIGNAL's job is to:

  1. Name the ASPIRATIONAL INTERNATIONAL anchor (Zara, COS, Uniqlo,
     Mango, Massimo Dutti, Arket, & Other Stories, Theory, Reiss,
     Madewell, Sezane, Aritzia, Reformation, etc.) — that's the look
     to translate.
  2. Read the WHY: cultural fit, consumer profile, why-now.
  3. Read the HOW: distribution tier, drop timing, capsule format.
  4. Set the price ladder in INR — global anchor → India value floor →
     recommended MRP — WITHOUT naming any Indian retailer.

Strict narrative rule: brand_signals reference ONLY international
brands. The fields `commentary`, `consumer`, `why_now`, `india_play`,
`price_strategy`, `production_notes`, `merchandising` must NEVER name
an Indian retailer (no Zudio, Westside, Pantaloons, Max, Reliance
Trends, Bewakoof, The Souled Store, Snitch, Wrogn, Allen Solly, etc).
Refer to that tier as "the Indian value floor", "the aspirational-mass
shelf", "the metro fast-fashion floor" instead.
"""
from __future__ import annotations

import logging
from typing import Any

from app.data.brands import Brand
from app.schemas import BrandSignal, ImageRead, Mode
from app.services.llm import get_llm

log = logging.getLogger(__name__)


SYSTEM = """You are SIGNAL's Commentary Agent. You read an apparel image
or mood board through the lens of an Indian fast-fashion designer who
already operates on the value-to-mid floor (INR 499-1,799 MRP).

Your job is to translate an INTERNATIONAL ASPIRATIONAL READ into an
India-launch brief. Reference international brands by name (Zara, H&M,
Uniqlo, COS, Mango, Massimo Dutti, Arket, & Other Stories, Theory,
Reiss, Madewell, Sezane, Aritzia, Reformation, etc.) wherever it
sharpens the brief.

STRICT NARRATIVE RULE — never name an Indian retailer in any of these
fields: commentary, consumer, why_now, india_play, price_strategy,
production_notes, merchandising. No Zudio, Westside, Pantaloons, Max,
Reliance Trends, Bewakoof, The Souled Store, Snitch, Wrogn, Allen
Solly, AND, Biba, FabIndia, Nicobar, etc. Refer to that tier as "the
Indian value floor", "the metro aspirational-mass shelf", "the urban
fast-fashion floor". The designer already knows where they sit.

Never reference maison luxury (Prada, Gucci, Chanel, Loewe, Bottega,
Balenciaga, Jacquemus, Acne, Miu Miu, Saint Laurent, Dior, Hermes).

Be SPECIFIC. Use Indian retail vocabulary: tier-1 metros, tier-2/3
cities, festive cycles, summer-weight fabrics, wedding/resort windows,
post-monsoon refresh, end-of-season-sale rhythms.

Sections you must populate:

1. observation — 3-7 word editorial headline.
2. summary — one tight sentence (≤24 words) naming the look.

3. brand_signals — one entry per candidate brand. All candidates are
   international. Strong = could plausibly be from that brand's current
   floor; Adjacent = same direction, different positioning;
   Moderate = some shared facets; Weak = divergent. Rationale ≤22 words.

4. commentary — 3-5 sentences. The WHY. What's the global signal,
   how strong / how peaking, what's the editorial read. Reference the
   international anchors by name.

5. consumer — 2-3 sentences. WHO buys this in India + WHEN it gets
   worn. Be specific: age band, city tier, household income proxy
   (e.g. "household income 8-15L"), media diet (Pinterest / Instagram
   / Netflix / global e-comm), occasion (WFH-to-cafe, wedding-resort,
   festive day-2, work-to-evening, college-going). NO retailer names.

6. why_now — 1-2 sentences. Why does this signal land in India in this
   specific window? Festive calendar, fabric weight, monsoon, post-EOSS
   refresh, school re-open, etc. NO retailer names.

7. india_play — 2-3 sentences. The HOW. Distribution (tier-1 metros
   only / pan-India / digital-first), drop timing (week of year or
   season), format (capsule / single-SKU hero / 3-color stack / limited
   drop), and what the success signal looks like. NO retailer names —
   say "metro stores", "aspirational-mass shelf", "value floor".

8. price_strategy — 2-3 sentences with the INR ladder. Start with the
   aspirational anchor (named brand + price, e.g. "Zara INR 2,990").
   Describe the Indian value floor in generic terms (e.g. "the urban
   value floor lands a similar silhouette at INR 599-899" — no brand
   name). End with the recommended MRP and the gap reasoning (why the
   discount is the right play).

9. price_anchor_inr — short label string for the aspirational anchor,
   format "BRAND INR XXX" (e.g. "Zara INR 2,990").
10. price_floor_inr — short label string for the Indian value floor
   band, format "INR XXX-YYY" (no brand name).
11. price_target_inr — short label for the recommended MRP,
   format "INR XXX-YYY".

12. palette — 4-6 specific named trade colors (ecru, rust, kerala
   green, burnt sienna — never "light" / "dark" / "blue").

13. production_notes — 1-2 sentences: fabric spec (gsm + weave),
   production complexity, 1-2 critical trim callouts. NO retailer names.

14. merchandising — 1-2 sentences: adjacent SKUs to drop alongside +
   shelf-stack note. NO retailer names.

15. keywords — 6-10 short tokens.
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
  "commentary": "string (3-5 sentences, WHY)",
  "consumer": "string (2-3 sentences, WHO + WHEN, no retailer names)",
  "why_now": "string (1-2 sentences, WHY NOW)",
  "india_play": "string (2-3 sentences, HOW to launch, no retailer names)",
  "price_strategy": "string (2-3 sentences with INR ladder, no Indian retailer names)",
  "price_anchor_inr": "string (e.g. 'Zara INR 2,990')",
  "price_floor_inr": "string (e.g. 'INR 599-899')",
  "price_target_inr": "string (e.g. 'INR 999-1,299')",
  "palette": ["string (named trade color, 4-6 total)"],
  "production_notes": "string (1-2 sentences, no retailer names)",
  "merchandising": "string (1-2 sentences, no retailer names)",
  "keywords": ["string"]
}
""".strip()


# Words we strictly scrub from narrative output if the model leaks them.
_FORBIDDEN_NARRATIVE_BRANDS = [
    "Zudio", "Westside", "Pantaloons", "Max Fashion", "Reliance Trends",
    "V-Mart", "Bewakoof", "Souled Store", "Snitch", "Wrogn", "Allen Solly",
    "Van Heusen", "Louis Philippe", "Jack & Jones", "Biba", "Aurelia",
    "FabIndia", "Nicobar", "Good Earth", "Anita Dongre", "Doodlage",
    "Ajio", "Myntra", "Flipkart Fashion",
]


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

Candidate INTERNATIONAL aspirational brands (cite URLs where you use them):

{brand_block}

Write the full brief. Every narrative section must be specific and
designer-usable. Remember: brand_signals = international only;
narrative sections NEVER name an Indian retailer.
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
        if hits:
            lines = [f"  - {h['title']} ({h['url']}): {h['snippet'][:160]}" for h in hits[:3]]
            blocks.append(f"{b.name} — {b.domain}\n" + "\n".join(lines))
        else:
            blocks.append(f"{b.name} — {b.domain}\n  (no fresh snippets — reason from brand DNA)")
    return "\n\n".join(blocks)


def _scrub_narrative(text: str) -> str:
    """Belt-and-suspenders: strip Indian retailer names if the model leaks them."""
    if not text:
        return text
    out = text
    for term in _FORBIDDEN_NARRATIVE_BRANDS:
        # Replace the brand name with a generic descriptor, then collapse any
        # awkward leftover phrasing like "the   floor".
        out = out.replace(term, "the Indian value floor")
        out = out.replace(term.lower(), "the Indian value floor")
    return out


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
        "commentary":       _scrub_narrative(str(data.get("commentary", "")).strip()),
        "consumer":         _scrub_narrative(str(data.get("consumer", "")).strip()),
        "why_now":          _scrub_narrative(str(data.get("why_now", "")).strip()),
        "india_play":       _scrub_narrative(str(data.get("india_play", "")).strip()),
        "price_strategy":   _scrub_narrative(str(data.get("price_strategy", "")).strip()),
        "price_anchor_inr": str(data.get("price_anchor_inr", "")).strip()[:60],
        "price_floor_inr":  str(data.get("price_floor_inr", "")).strip()[:60],
        "price_target_inr": str(data.get("price_target_inr", "")).strip()[:60],
        "palette":          [str(c) for c in (data.get("palette") or [])][:8] or pooled["colors"][:6],
        "production_notes": _scrub_narrative(str(data.get("production_notes", "")).strip()),
        "merchandising":    _scrub_narrative(str(data.get("merchandising", "")).strip()),
        "keywords":         [str(k) for k in (data.get("keywords") or [])][:10],
    }


def _mock_commentary(brands: list[Brand], pooled: dict[str, list[str]]) -> dict[str, Any]:
    obs = " ".join(pooled["aesthetics"][:2] + pooled["categories"][:1]).title() or "Quiet Casual Mid-Premium"
    aesthetic_phrase = pooled["aesthetics"][0] if pooled["aesthetics"] else "casual contemporary"
    sigs = []
    for i, b in enumerate(brands):
        sim = ["Strong", "Adjacent", "Moderate", "Moderate", "Weak"][min(i, 4)]
        sigs.append(BrandSignal(
            brand=b.name, similarity=sim,  # type: ignore[arg-type]
            rationale=f"{b.name}'s current floor leans {aesthetic_phrase} — strong DNA to translate.",
            citations=[],
        ).model_dump())
    return {
        "observation": obs,
        "summary": "Quiet-luxury minimalism translating from European fast-fashion into the Indian aspirational-mass tier.",
        "brand_signals": sigs,
        "commentary": (
            "This is the Zara / COS quiet-luxury moment hitting peak globally — restrained palette, "
            "elevated proportions, a Mango-style ease of styling. The editorial signal is strong: "
            "Pinterest saves are up, the look reads in both office and weekend modes, and it survives "
            "the Indian climate without compromise. Right now this aesthetic carries the credibility "
            "of European retail without the maison-tier price burden."
        ),
        "consumer": (
            "Urban tier-1 woman, 24-34, white-collar or freelance creative, household income INR "
            "8-18L. Heavy Pinterest / Instagram diet; currently saves Zara purchases for end-of-season. "
            "Worn for office, brunch, work-from-cafe, low-key weddings — the wardrobe spine, not the showpiece."
        ),
        "why_now": (
            "Post-monsoon refresh + the pre-festive build-up creates an 8-week window where mid-premium "
            "shoppers reset their basics layer. The quiet-luxury narrative also aligns with the "
            "after-effect of celebrity capsule drops dominating Indian Instagram this quarter."
        ),
        "india_play": (
            "Drop tier-1 metro stores first (Mumbai, Delhi-NCR, Bangalore, Hyderabad) in week 1, with "
            "a 3-color stack on the lead SKU and 2-color on support. Hold tier-2/3 carry-over for week 5 "
            "once sell-through validates the silhouette. Format as a 6-SKU capsule so it reads as a "
            "story on the floor rather than a one-off."
        ),
        "price_strategy": (
            "Aspirational anchor: Zara INR 2,990. The urban value floor lands the same silhouette "
            "around INR 599-899 today. Recommended MRP INR 999-1,299 — that 60% discount to Zara is "
            "the headroom to capture the shopper who currently waits for Zara EOSS, while the 30-50% "
            "premium over the value floor protects margin and signals the elevated read."
        ),
        "price_anchor_inr": "Zara INR 2,990",
        "price_floor_inr": "INR 599-899",
        "price_target_inr": "INR 999-1,299",
        "palette": pooled["colors"][:6] or ["ecru", "rust", "olive", "off-white", "burnt sienna"],
        "production_notes": (
            "200 gsm cotton jersey, brushed interior for hand-feel; medium complexity at scale. "
            "Critical trims: ribbed neck tape, centered chest placement print, double-needle hem."
        ),
        "merchandising": (
            "Drop alongside a wide-leg cargo and an open-weave knit so the capsule reads as a "
            "complete story. Stack 3 colors on the hero SKU; 2 on supports."
        ),
        "keywords": pooled["keywords"][:8] or ["oversized", "neutral", "minimal", "casual", "contemporary"],
    }

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

import asyncio
import logging
from dataclasses import dataclass
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
    """Run the commentary chain. Splits the previous monolithic call into
    THREE parallel focused agents so each LLM request is small, fast and
    reliable. Each agent has its own retry inside the LLM client.

    A. editorial_agent  — observation, summary, brand_signals, commentary, keywords, palette
    B. translation_agent — consumer, why_now, india_play
    C. ops_agent        — price_strategy + price_*, production_notes, merchandising

    If a single agent fails, ONLY that subsection falls back. The others
    still show live LLM output. data_source becomes 'live' (all three
    succeeded), 'partial' (some succeeded, some fell back), or
    'fallback' (Gemini not configured at all)."""
    llm = get_llm()
    pooled = pool_reads(reads)
    brand_block = _brand_block(brands, search_results)

    if not llm.is_available:
        out = _mock_commentary(brands, pooled)
        out["data_source"] = "fallback"
        return out

    # Fire all three agents in parallel; each retries internally.
    ed_task = _editorial_agent(llm, pooled, brand_block, brands, mode, reads)
    tr_task = _translation_agent(llm, pooled, mode)
    ops_task = _ops_agent(llm, pooled, brands, mode)
    ed_res, tr_res, ops_res = await asyncio.gather(
        ed_task, tr_task, ops_task, return_exceptions=True,
    )

    mock = _mock_commentary(brands, pooled)
    out: dict[str, Any] = {}
    statuses: list[str] = []

    # Editorial: observation, summary, brand_signals, commentary, keywords, palette
    if isinstance(ed_res, dict):
        out.update({
            "observation": ed_res.get("observation") or mock["observation"],
            "summary":     ed_res.get("summary") or mock["summary"],
            "commentary":  ed_res.get("commentary") or mock["commentary"],
            "keywords":    ed_res.get("keywords") or mock["keywords"],
            "palette":     ed_res.get("palette") or mock["palette"],
            "brand_signals": ed_res.get("brand_signals") or mock["brand_signals"],
        })
        statuses.append("editorial:live")
    else:
        log.warning("editorial_agent failed (%s): %s", type(ed_res).__name__, ed_res)
        for k in ("observation", "summary", "commentary", "keywords", "palette", "brand_signals"):
            out[k] = mock[k]
        statuses.append("editorial:fallback")

    # Translation: consumer, why_now, india_play
    if isinstance(tr_res, dict):
        out["consumer"]   = tr_res.get("consumer") or mock["consumer"]
        out["why_now"]    = tr_res.get("why_now") or mock["why_now"]
        out["india_play"] = tr_res.get("india_play") or mock["india_play"]
        statuses.append("translation:live")
    else:
        log.warning("translation_agent failed (%s): %s", type(tr_res).__name__, tr_res)
        out["consumer"]   = mock["consumer"]
        out["why_now"]    = mock["why_now"]
        out["india_play"] = mock["india_play"]
        statuses.append("translation:fallback")

    # Ops: price ladder, production, merchandising
    if isinstance(ops_res, dict):
        out["price_strategy"]    = ops_res.get("price_strategy") or mock["price_strategy"]
        out["price_anchor_inr"]  = ops_res.get("price_anchor_inr") or mock["price_anchor_inr"]
        out["price_floor_inr"]   = ops_res.get("price_floor_inr") or mock["price_floor_inr"]
        out["price_target_inr"]  = ops_res.get("price_target_inr") or mock["price_target_inr"]
        out["production_notes"]  = ops_res.get("production_notes") or mock["production_notes"]
        out["merchandising"]     = ops_res.get("merchandising") or mock["merchandising"]
        statuses.append("ops:live")
    else:
        log.warning("ops_agent failed (%s): %s", type(ops_res).__name__, ops_res)
        for k in ("price_strategy", "price_anchor_inr", "price_floor_inr",
                  "price_target_inr", "production_notes", "merchandising"):
            out[k] = mock[k]
        statuses.append("ops:fallback")

    # Scrub Indian retailer name leaks from every narrative field, regardless of source.
    for k in ("commentary", "consumer", "why_now", "india_play",
              "price_strategy", "production_notes", "merchandising"):
        out[k] = _scrub_narrative(out.get(k, ""))

    live_count = sum(1 for s in statuses if s.endswith("live"))
    if live_count == len(statuses):
        out["data_source"] = "live"
    elif live_count == 0:
        out["data_source"] = "fallback"
    else:
        out["data_source"] = "partial"
    log.info("commentary statuses: %s → data_source=%s", statuses, out["data_source"])
    return out


# ─── Three focused sub-agents ──────────────────────────────────────────

_EDITORIAL_SYSTEM = """You are SIGNAL's Editorial Agent. The reader is
an Indian fast-fashion designer at the value-to-mid floor. Translate
the international aspirational read into a tight editorial headline +
short market-context paragraph + brand-similarity scorecard.

STRICT: brand_signals reference ONLY the supplied international brands.
The 'commentary' field must NEVER name an Indian retailer (no Zudio,
Westside, Pantaloons, Snitch, Wrogn, Allen Solly, AND, Biba, FabIndia,
Nicobar, etc.) — refer to that tier as "the Indian value floor" or
"the metro aspirational-mass shelf".

palette: 4-6 specific named trade colors (ecru, rust, kerala green,
burnt sienna — never "light"/"dark"/"blue").
""".strip()

_EDITORIAL_SCHEMA = """
{
  "observation": "string (3-7 words, editorial headline)",
  "summary": "string (one sentence <= 24 words)",
  "brand_signals": [
    {"brand": "<name from candidates>", "similarity": "Strong|Adjacent|Moderate|Weak",
     "rationale": "string (<= 22 words)", "citations": ["url"]}
  ],
  "commentary": "string (3-5 sentences, market WHY, no Indian retailer names)",
  "palette": ["string"],
  "keywords": ["string"]
}
""".strip()

_TRANSLATION_SYSTEM = """You are SIGNAL's Translation Agent. The reader
is an Indian fast-fashion designer translating an international
aspirational look into an India launch. Produce three short
India-context sections:

  consumer  — 2-3 sentences naming WHO buys this (age band, city tier,
              household income proxy, media diet) and WHEN they wear it
              (occasion). NO retailer names.
  why_now   — 1-2 sentences on why this signal lands in India in this
              specific window. Tie to monsoon / festive / wedding /
              post-EOSS / back-to-office cycles. NO retailer names.
  india_play — 2-3 sentences on HOW to launch. Distribution (tier-1
              metros vs pan-India vs digital-first), drop timing (week
              of year or season), format (capsule / hero SKU / 3-color
              stack / limited drop). Use generic descriptors like
              "metro stores", "value floor", "aspirational-mass shelf"
              — NEVER name an Indian retailer.

Be specific. Use Indian retail vocabulary.
""".strip()

_TRANSLATION_SCHEMA = """
{
  "consumer": "string",
  "why_now": "string",
  "india_play": "string"
}
""".strip()

_OPS_SYSTEM = """You are SIGNAL's Operations Agent. The reader is an
Indian fast-fashion designer. Produce the INR price ladder + production
spec + merchandising note.

STRICT: never name an Indian retailer in narrative — say "the value
floor" or "the aspirational-mass shelf". The aspirational anchor IS
named (one of the supplied international brands).

price_anchor_inr — short label, format "BRAND INR X,XXX" (e.g. "Zara INR 2,990").
price_floor_inr  — short label, format "INR XXX-YYY" (no brand name).
price_target_inr — short label, format "INR XXX-YYY".
price_strategy   — 2-3 sentences explaining the ladder + margin / share logic.

production_notes — 1-2 sentences: fabric (gsm + weave), complexity
                   (easy/medium/hard at scale), 1-2 critical trim callouts.
merchandising    — 1-2 sentences: adjacent SKUs + shelf-stack note.
""".strip()

_OPS_SCHEMA = """
{
  "price_strategy": "string",
  "price_anchor_inr": "string",
  "price_floor_inr": "string",
  "price_target_inr": "string",
  "production_notes": "string",
  "merchandising": "string"
}
""".strip()


def _facets_block(pooled: dict[str, list[str]]) -> str:
    return (
        f"  aesthetics:  {', '.join(pooled['aesthetics']) or '—'}\n"
        f"  categories:  {', '.join(pooled['categories']) or '—'}\n"
        f"  colors:      {', '.join(pooled['colors']) or '—'}\n"
        f"  silhouettes: {', '.join(pooled['silhouettes']) or '—'}\n"
        f"  market:      {', '.join(pooled['segments']) or '—'}\n"
        f"  keywords:    {', '.join(pooled['keywords']) or '—'}"
    )


async def _editorial_agent(llm, pooled, brand_block, brands, mode, reads) -> dict[str, Any]:
    user = f"""
Mode: {mode}
Image count: {len(reads)}

Vision facets:
{_facets_block(pooled)}

Candidate international brands (cite URLs you use):

{brand_block}
""".strip()
    raw = await llm.text_json(
        system=_EDITORIAL_SYSTEM, user_text=user,
        schema_hint=_EDITORIAL_SCHEMA, temperature=0.25,
    )
    # Normalize brand_signals.
    allowed = {b.name for b in brands}
    sigs_raw = raw.get("brand_signals") or []
    sigs: list[BrandSignal] = []
    seen: set[str] = set()
    for s in sigs_raw:
        name = str(s.get("brand", "")).strip()
        if name not in allowed or name in seen:
            continue
        seen.add(name)
        sim = str(s.get("similarity", "Moderate")).strip().title()
        if sim not in ("Strong", "Adjacent", "Moderate", "Weak"):
            sim = "Moderate"
        sigs.append(BrandSignal(
            brand=name, similarity=sim,  # type: ignore[arg-type]
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
        "observation":  str(raw.get("observation", "")).strip(),
        "summary":      str(raw.get("summary", "")).strip(),
        "commentary":   str(raw.get("commentary", "")).strip(),
        "palette":      [str(c) for c in (raw.get("palette") or [])][:8],
        "keywords":     [str(k) for k in (raw.get("keywords") or [])][:10],
        "brand_signals": [s.model_dump() for s in sigs],
    }


async def _translation_agent(llm, pooled, mode) -> dict[str, Any]:
    user = f"""
Mode: {mode}

Vision facets:
{_facets_block(pooled)}

Write the three India-translation sections.
""".strip()
    raw = await llm.text_json(
        system=_TRANSLATION_SYSTEM, user_text=user,
        schema_hint=_TRANSLATION_SCHEMA, temperature=0.35,
    )
    return {
        "consumer":   str(raw.get("consumer", "")).strip(),
        "why_now":    str(raw.get("why_now", "")).strip(),
        "india_play": str(raw.get("india_play", "")).strip(),
    }


async def _ops_agent(llm, pooled, brands, mode) -> dict[str, Any]:
    anchor = next((b for b in brands if b.segment == "global_aspirational"), brands[0] if brands else None)
    anchor_name = anchor.name if anchor else "Zara"
    user = f"""
Mode: {mode}

Vision facets:
{_facets_block(pooled)}

Aspirational anchor brand (use this exact name in price_anchor_inr): {anchor_name}

Write the price ladder + production + merchandising sections.
""".strip()
    raw = await llm.text_json(
        system=_OPS_SYSTEM, user_text=user,
        schema_hint=_OPS_SCHEMA, temperature=0.3,
    )
    return {
        "price_strategy":   str(raw.get("price_strategy", "")).strip(),
        "price_anchor_inr": str(raw.get("price_anchor_inr", "")).strip()[:60],
        "price_floor_inr":  str(raw.get("price_floor_inr", "")).strip()[:60],
        "price_target_inr": str(raw.get("price_target_inr", "")).strip()[:60],
        "production_notes": str(raw.get("production_notes", "")).strip(),
        "merchandising":    str(raw.get("merchandising", "")).strip(),
    }


def pool_reads(reads: list[ImageRead]) -> dict[str, list[str]]:
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
    """Build a brief that *uses* the actual pooled vision facets so every
    upload produces unique-feeling output, even when the LLM is down.

    Reads the dominant aesthetic, category, color, silhouette tokens from the
    pool and uses them to pick:
      - a flavor profile (occasion / fabric / construction)
      - a season window
      - price-ladder math based on the detected market segment
    """
    # Pull the most salient signals.
    aesthetics = pooled["aesthetics"] or ["contemporary"]
    categories = pooled["categories"] or ["apparel"]
    colors = pooled["colors"] or ["neutral"]
    silhouettes = pooled["silhouettes"] or ["regular"]
    segments = pooled["segments"] or ["mid-premium"]
    keywords = pooled["keywords"] or aesthetics + categories

    lead_aesthetic = aesthetics[0]
    lead_category = categories[0]
    lead_color = colors[0]
    lead_silhouette = silhouettes[0]
    lead_segment = segments[0].lower() if segments else "mid-premium"

    # Build an observation — short, editorial, derived from facets.
    obs_bits = [
        lead_aesthetic.title(),
        lead_silhouette.title() if lead_silhouette != "regular" else "",
        lead_category.title(),
    ]
    observation = " ".join([b for b in obs_bits if b]).strip()[:64] or "Editorial Read"

    # Flavor profile inferred from aesthetic + category text.
    blob = " ".join(aesthetics + categories + keywords).lower()
    profile = _infer_flavor(blob)

    # Brand signals: rank by quick keyword match into the brand's DNA so the
    # similarity isn't always Strong/Adjacent/Moderate in the same order.
    sigs = []
    for i, b in enumerate(brands):
        score = sum(1 for token in (aesthetics + keywords) if any(token.lower() in a for a in b.aesthetics))
        if score >= 3:
            sim = "Strong"
        elif score == 2:
            sim = "Adjacent"
        elif score == 1:
            sim = "Moderate"
        else:
            sim = ["Adjacent", "Moderate", "Moderate", "Weak", "Weak"][min(i, 4)]
        rationale = (
            f"{b.name}'s current floor runs adjacent to this {lead_aesthetic} {lead_category} "
            f"read — {('strong' if sim == 'Strong' else 'partial')} DNA to translate."
        )
        sigs.append(BrandSignal(
            brand=b.name, similarity=sim,  # type: ignore[arg-type]
            rationale=rationale[:220], citations=[],
        ).model_dump())

    # Price ladder math: derive from market segment + flavor profile.
    anchor_name, anchor_price, floor_band, target_band = _price_ladder(brands, lead_segment, profile)

    return {
        "observation": observation,
        "summary": (
            f"{lead_aesthetic.capitalize()} {lead_category} read in a "
            f"{lead_color} palette — translating from a global {profile.tier} aesthetic "
            f"into the Indian {lead_segment} floor."
        )[:220],
        "brand_signals": sigs,
        "commentary": (
            f"The look reads as {lead_aesthetic} — proportions tilt toward {lead_silhouette}, "
            f"palette anchored in {lead_color}. The {profile.tier} narrative is "
            f"{profile.momentum} globally right now, and {profile.cultural_fit} translates "
            f"cleanly into the Indian {lead_segment} consumer's reference set. "
            f"This is the moment to translate it before the silhouette commoditises."
        ),
        "consumer": (
            f"{profile.consumer_geo}, {profile.consumer_age}, "
            f"{profile.consumer_income}. Media diet: {profile.consumer_media}. "
            f"Worn for {profile.occasion} — {profile.wardrobe_role}."
        ),
        "why_now": (
            f"{profile.season_window} is the natural drop window for this read. "
            f"{profile.cultural_moment}"
        ),
        "india_play": (
            f"Drop tier-1 metros first (Mumbai, Delhi-NCR, Bangalore, Hyderabad) in week 1 with "
            f"a {profile.color_stack} color stack on the hero SKU. Hold tier-2/3 carry-over for "
            f"week {profile.tier2_week} once sell-through validates. Format as a "
            f"{profile.capsule_size}-SKU capsule so the floor reads as a story, not a one-off."
        ),
        "price_strategy": (
            f"Aspirational anchor: {anchor_name} {anchor_price}. The urban value floor lands "
            f"the same silhouette at {floor_band} today. Recommended MRP {target_band} — "
            f"{profile.price_logic}"
        ),
        "price_anchor_inr": f"{anchor_name} {anchor_price}",
        "price_floor_inr": floor_band,
        "price_target_inr": target_band,
        "palette": colors[:6],
        "production_notes": (
            f"{profile.fabric_spec}; {profile.complexity} complexity at scale. "
            f"Critical trims: {profile.trims}."
        ),
        "merchandising": (
            f"Drop alongside {profile.adjacent_skus} so the capsule reads complete. "
            f"Stack {profile.color_stack} colors deep on the hero, 2 on supports."
        ),
        "keywords": keywords[:8],
    }


@dataclass
class _Flavor:
    tier: str
    momentum: str
    cultural_fit: str
    season_window: str
    cultural_moment: str
    consumer_geo: str
    consumer_age: str
    consumer_income: str
    consumer_media: str
    occasion: str
    wardrobe_role: str
    color_stack: int
    tier2_week: int
    capsule_size: int
    fabric_spec: str
    complexity: str
    trims: str
    adjacent_skus: str
    price_logic: str


def _infer_flavor(blob: str) -> _Flavor:
    """Pick one of a handful of pre-rolled flavor profiles based on the
    pooled vision text. Each flavor wires up consumer / season / fabric /
    price logic that fits the look."""
    has = lambda *tokens: any(t in blob for t in tokens)

    if has("ethnic", "kurta", "saree", "lehenga", "festive", "indo", "handloom"):
        return _Flavor(
            tier="craft / indo-fusion", momentum="peaking with the festive build-up",
            cultural_fit="the regional craft revival",
            season_window="The festive-to-wedding bridge (October through February)",
            cultural_moment="Wedding-season demand pulls handloom + occasion-wear right now.",
            consumer_geo="Urban tier-1 + emerging tier-2 woman", consumer_age="28-42",
            consumer_income="household income INR 12-25L",
            consumer_media="Instagram / Pinterest / wedding-Instagram inspiration",
            occasion="mehendi, sangeet, day-time wedding events, festive office wear",
            wardrobe_role="the lehenga-alternative that still photographs",
            color_stack=2, tier2_week=3, capsule_size=8,
            fabric_spec="120 gsm chanderi-blend / mul cotton, with selective hand-block detailing",
            complexity="medium-to-high",
            trims="hand-block placement, tassel ties, contrast piping",
            adjacent_skus="a coordinating dupatta and a layering jacket",
            price_logic="the craft narrative justifies the premium; volume is secondary to margin and brand cred.",
        )

    if has("denim", "wide-leg", "indigo", "rinse", "jean"):
        return _Flavor(
            tier="elevated denim", momentum="resurgent with the wide-leg silhouette swing",
            cultural_fit="the post-skinny denim reset",
            season_window="The pre-monsoon to mid-monsoon window (June-September)",
            cultural_moment="Wide-leg denim is taking shelf share from skinny across global retail.",
            consumer_geo="Urban tier-1 woman", consumer_age="22-32",
            consumer_income="household income INR 6-15L",
            consumer_media="Instagram + YouTube hauls + TikTok adjacent",
            occasion="college, work-from-cafe, weekend brunch",
            wardrobe_role="the silhouette refresh that signals 'on-trend' without trying",
            color_stack=3, tier2_week=5, capsule_size=6,
            fabric_spec="12-14 oz cotton denim, mid-rinse with selective whiskering",
            complexity="medium",
            trims="metal shank button, antique copper rivets, classic 5-pocket detailing",
            adjacent_skus="a cropped tee and an unstructured cotton jacket",
            price_logic="denim sustains a higher MRP than its cost suggests; the silhouette is the markup.",
        )

    if has("tailor", "blazer", "trouser", "suit", "office", "smart-casual"):
        return _Flavor(
            tier="elevated tailoring", momentum="steady-state with quiet-luxury tailwind",
            cultural_fit="the return-to-office and the polished-creative consumer",
            season_window="Post-monsoon refresh (September-November) and the New Year reset",
            cultural_moment="Return-to-office and creator-economy 'polished' aesthetics align.",
            consumer_geo="Urban tier-1 metro professional", consumer_age="26-38",
            consumer_income="household income INR 10-25L",
            consumer_media="LinkedIn Instagram + curated Pinterest boards",
            occasion="office-to-evening, client meetings, day-of-the-wedding office",
            wardrobe_role="the wardrobe spine that elevates everything around it",
            color_stack=2, tier2_week=6, capsule_size=5,
            fabric_spec="220-260 gsm wool-poly suiting with TR blend for the Indian climate",
            complexity="hard",
            trims="horn-finish buttons, half-canvas construction, contrast lining",
            adjacent_skus="a matching trouser and a fine-gauge knit",
            price_logic="tailoring rewards margin protection; the silhouette signals the price-point.",
        )

    if has("y2k", "going-out", "satin", "slip", "party", "club", "cropped"):
        return _Flavor(
            tier="Y2K going-out", momentum="peaking with the millennial-Y2K nostalgia cycle",
            cultural_fit="the going-out wardrobe gap post-pandemic",
            season_window="The wedding-season bridge + New Year + Valentine's window",
            cultural_moment="Going-out aesthetics dominate Reels and the wedding-season Instagram feed.",
            consumer_geo="Urban tier-1 metro woman", consumer_age="20-28",
            consumer_income="household income INR 6-14L (with discretionary on going-out)",
            consumer_media="Reels + Instagram + influencer hauls",
            occasion="cocktail nights, sangeet after-parties, New Year, date nights",
            wardrobe_role="the one piece that earns its cost-per-wear across 6 events",
            color_stack=2, tier2_week=4, capsule_size=4,
            fabric_spec="silk-touch satin, 80-100 gsm with a soft drape and a slip lining",
            complexity="medium",
            trims="bias binding, adjustable straps, hidden side zip",
            adjacent_skus="a matching cropped jacket and a sheer overlay top",
            price_logic="going-out earns a price premium because the cost-per-wear is event-driven, not daily.",
        )

    # Default: contemporary casualwear
    return _Flavor(
        tier="quiet-luxury contemporary", momentum="building steadily in global retail",
        cultural_fit="the elevated-mass shift away from logo-driven dressing",
        season_window="The end-of-monsoon refresh into festive prep (September-November)",
        cultural_moment="Pinterest saves on minimal contemporary silhouettes are up across India.",
        consumer_geo="Urban tier-1 woman", consumer_age="24-34",
        consumer_income="household income INR 8-18L",
        consumer_media="Pinterest + Instagram + global e-comm browsing",
        occasion="office, brunch, work-from-cafe, low-key wedding events",
        wardrobe_role="the wardrobe spine, not the showpiece",
        color_stack=3, tier2_week=5, capsule_size=6,
        fabric_spec="200 gsm cotton jersey, brushed interior for hand-feel",
        complexity="medium",
        trims="ribbed neck tape, double-needle hem, centered placement print",
        adjacent_skus="a wide-leg cargo and an open-weave knit",
        price_logic="the 30-50% premium over the value floor protects margin and signals the elevated read.",
    )


def _price_ladder(brands: list[Brand], segment: str, profile: _Flavor) -> tuple[str, str, str, str]:
    """Pick an aspirational anchor brand + INR ladder.

    Anchor pulled from the first global_aspirational brand in the candidate
    set so the named brand stays consistent with what the user sees in the
    Brand Signals section."""
    anchor = next((b for b in brands if b.segment == "global_aspirational"), brands[0] if brands else None)
    anchor_name = anchor.name if anchor else "Zara"

    # Segment-driven ladder math.
    seg = segment.lower()
    if "mass" in seg or "value" in seg:
        return anchor_name, "INR 1,790", "INR 299-499", "INR 599-799"
    if "premium" in seg and "mid" not in seg:
        return anchor_name, "INR 4,990", "INR 1,299-1,799", "INR 1,999-2,499"
    if "luxury" in seg:
        return anchor_name, "INR 8,990", "INR 2,499-3,499", "INR 3,499-4,499"
    # Default: mid-premium
    return anchor_name, "INR 2,990", "INR 599-899", "INR 999-1,299"

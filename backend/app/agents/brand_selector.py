"""Brand Selector.

Picks 5 INTERNATIONAL ASPIRATIONAL brands per analysis. The reference
set is the global accessible aspirational tier (Zara, H&M, Uniqlo, COS,
Mango, Massimo Dutti, Arket, Theory, Reiss, Madewell, Sezane, Aritzia,
etc.) — never Indian retail.

When the read leans ethnic / craft / indo-fusion, we swap one slot to
an india_premium brand (FabIndia, Nicobar) because that's where the
craft adjacency actually exists internationally.

The Indian competitive shelf (Zudio / Westside / Pantaloons) is
DELIBERATELY excluded from the signal list — the designer already lives
on that shelf; the value of SIGNAL is naming the aspirational anchor
they should be translating FROM.
"""
from __future__ import annotations

from collections import Counter

from app.data.brands import BRANDS, Brand
from app.schemas import ImageRead


# Maps free-text market/aesthetic tokens → segment buckets.
_ETHNIC_HINTS = {"ethnic", "indo-western", "indo-fusion", "festive",
                 "kurta", "saree", "lehenga", "handloom", "craft"}

# Tier default ranking used as a tiebreaker when aesthetic scoring is flat.
# Higher = more commercially relevant as a default reference brand.
_DEFAULT_RANK = {
    # global_aspirational
    "Zara": 100, "H&M": 95, "Uniqlo": 90, "Mango": 85, "COS": 80,
    "Massimo Dutti": 75, "Arket": 70, "& Other Stories": 65, "Theory": 60,
    "Reiss": 55, "AllSaints": 50, "Madewell": 45, "Reformation": 40,
    "Sezane": 35, "Aritzia": 30, "Everlane": 25, "Weekday": 20, "Mango Man": 15,
    # india_competitive
    "Zudio": 100, "Westside": 95, "Pantaloons": 90, "Max Fashion": 85,
    "Reliance Trends": 80, "The Souled Store": 70, "Bewakoof": 65, "V-Mart": 60,
    # india_premium
    "Nicobar": 100, "FabIndia": 95, "Good Earth": 90, "Anita Dongre": 85,
    "Doodlage": 80,
}


def _aggregate(reads: list[ImageRead]) -> dict[str, list[str]]:
    aesthetics: list[str] = []
    categories: list[str] = []
    segments: list[str] = []
    keywords: list[str] = []
    colors: list[str] = []
    for r in reads:
        a = r.attributes
        if a.aesthetic:
            aesthetics.extend(_tokens(a.aesthetic))
        if a.category:
            categories.extend(_tokens(a.category))
        if a.market_segment:
            segments.extend(_tokens(a.market_segment))
        keywords.extend([k.lower() for k in r.keywords])
        colors.extend([c.lower() for c in a.colors])
    return {
        "aesthetics": aesthetics,
        "categories": categories,
        "segments": segments,
        "keywords": keywords,
        "colors": colors,
    }


def _tokens(s: str) -> list[str]:
    return [t.strip().lower() for t in s.replace("/", " ").replace(",", " ").replace("-", " ").split() if t.strip()]


def _is_ethnic(facets: dict[str, list[str]]) -> bool:
    """Read leans ethnic / craft / indo-fusion?"""
    blob = " ".join(facets["aesthetics"] + facets["categories"] + facets["keywords"]).lower()
    return any(h in blob for h in _ETHNIC_HINTS)


def _score_brand(b: Brand, facets: dict[str, list[str]]) -> int:
    score = 0
    for token in facets["aesthetics"] + facets["keywords"]:
        if any(token in a for a in b.aesthetics):
            score += 2
    for token in facets["categories"]:
        if any(token in c for c in b.categories):
            score += 1
    return score


def select(reads: list[ImageRead], *, top_k: int = 5) -> list[Brand]:
    facets = _aggregate(reads)
    ethnic = _is_ethnic(facets)

    by_segment: dict[str, list[tuple[Brand, int]]] = {
        "global_aspirational": [],
        "india_premium": [],
    }
    for b in BRANDS:
        if b.segment not in by_segment:
            continue
        by_segment[b.segment].append((b, _score_brand(b, facets)))

    for k in by_segment:
        by_segment[k].sort(key=lambda x: (-x[1], -_DEFAULT_RANK.get(x[0].name, 0), x[0].name))

    # Composition: 5 INTERNATIONAL aspirational brands.
    # If the read leans ethnic, swap 1 slot for a craft-adjacency brand.
    picks: list[Brand] = []
    asp_slots = top_k - 1 if ethnic else top_k

    picks.extend([b for b, _ in by_segment["global_aspirational"][:asp_slots]])
    if ethnic:
        picks.extend([b for b, _ in by_segment["india_premium"][:1]])

    if len(picks) < top_k:
        seen = {b.name for b in picks}
        for b, _ in by_segment["global_aspirational"]:
            if b.name not in seen:
                picks.append(b)
                if len(picks) >= top_k:
                    break

    return picks[:top_k]

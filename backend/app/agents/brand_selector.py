"""Brand Selector.

Picks a shortlist of brands from the Indian-anchored universe based on
pooled vision facets. Default targets bias toward India mid-premium and
value, since that's the market SIGNAL is built for.
"""
from __future__ import annotations

from collections import Counter

from app.data.brands import BRANDS, Brand
from app.schemas import ImageRead


# Maps free-text market/aesthetic tokens → segment buckets in brands.py.
SEGMENT_HINTS = {
    # Indian value
    "value": "india_value",
    "budget": "india_value",
    "mass": "india_value",
    "tier-2": "india_value",
    "tier 2": "india_value",
    "tier-3": "india_value",
    "fast fashion": "india_value",
    "fast-fashion": "india_value",
    # Indian mid-premium
    "mid-premium": "india_mid_premium",
    "mid premium": "india_mid_premium",
    "premium": "india_mid_premium",
    "premium contemporary": "india_mid_premium",
    "contemporary": "india_mid_premium",
    "high street": "india_mid_premium",
    "workwear": "india_mid_premium",
    "formal": "india_mid_premium",
    "youth": "india_mid_premium",
    "going out": "india_mid_premium",
    "denim": "india_mid_premium",
    "ethnic": "india_mid_premium",
    "indowestern": "india_mid_premium",
    "indo-western": "india_mid_premium",
    "festive": "india_mid_premium",
    # India premium / craft
    "craft": "india_premium",
    "handloom": "india_premium",
    "natural fabric": "india_premium",
    "minimal": "india_premium",
    "elevated": "india_premium",
    # Global accessible (Zara, COS, Uniqlo, Mango, etc.) — comparator tier
    "global": "global_accessible",
    "european": "global_accessible",
    "japanese": "global_accessible",
    "scandi": "global_accessible",
    "british": "global_accessible",
    "americana": "global_accessible",
}


def _aggregate(reads: list[ImageRead]) -> dict[str, list[str]]:
    aesthetics: list[str] = []
    categories: list[str] = []
    segments: list[str] = []
    keywords: list[str] = []
    for r in reads:
        a = r.attributes
        if a.aesthetic:
            aesthetics.extend(_tokens(a.aesthetic))
        if a.category:
            categories.extend(_tokens(a.category))
        if a.market_segment:
            segments.extend(_tokens(a.market_segment))
        keywords.extend([k.lower() for k in r.keywords])
    return {
        "aesthetics": aesthetics,
        "categories": categories,
        "segments": segments,
        "keywords": keywords,
    }


def _tokens(s: str) -> list[str]:
    return [t.strip().lower() for t in s.replace("/", " ").replace(",", " ").split() if t.strip()]


def _segment_targets(segments: list[str], aesthetics: list[str]) -> set[str]:
    out: set[str] = set()
    haystack = " ".join(segments + aesthetics).lower()
    for hint, seg in SEGMENT_HINTS.items():
        if hint in haystack:
            out.add(seg)
    # Default: blend value + mid-premium (covers ~90% of Indian retail signals).
    if not out:
        out.update({"india_value", "india_mid_premium"})
    # Always include global accessible (Zara/COS/Uniqlo/Mango etc.) as
    # comparators — they're recognisable benchmarks the designer will know.
    # Scored lower than India tiers below so the mix leans India-anchored.
    out.add("global_accessible")
    return out


def select(reads: list[ImageRead], *, top_k: int = 6) -> list[Brand]:
    facets = _aggregate(reads)
    targets = _segment_targets(facets["segments"], facets["aesthetics"])

    counter: Counter[str] = Counter()
    for b in BRANDS:
        score = 0
        if b.segment in targets:
            # India tiers weighted higher than global comparators.
            score += 6 if b.segment.startswith("india_") else 2
        for token in facets["aesthetics"] + facets["keywords"]:
            if any(token in a for a in b.aesthetics):
                score += 2
        for token in facets["categories"]:
            if any(token in c for c in b.categories):
                score += 1
        if score:
            counter[b.name] = score

    if not counter:
        # Cold-start fallback: 4 India anchors + 2 global comparators.
        default = ["Zudio", "Westside", "Snitch", "AND", "Zara", "Uniqlo"]
        return [b for b in BRANDS if b.name in default][:top_k]

    # Reserve 1-2 slots for global comparators so the brief always has a
    # recognisable global anchor next to the India brands.
    name_to_brand = {b.name: b for b in BRANDS}
    ranked = [(name, score) for name, score in counter.most_common()]
    indian = [n for n, _ in ranked if name_to_brand[n].segment.startswith("india_")]
    globals_ = [n for n, _ in ranked if name_to_brand[n].segment == "global_accessible"]
    out_names: list[str] = []
    # Take up to top_k-1 India brands first.
    out_names.extend(indian[:max(1, top_k - 1)])
    # Then 1 (or 2 if room) global comparator.
    out_names.extend(globals_[:max(1, top_k - len(out_names))])
    # If still short, top up with whatever's left in ranking order.
    if len(out_names) < top_k:
        for n, _ in ranked:
            if n not in out_names:
                out_names.append(n)
            if len(out_names) >= top_k:
                break
    return [name_to_brand[n] for n in out_names[:top_k] if n in name_to_brand]

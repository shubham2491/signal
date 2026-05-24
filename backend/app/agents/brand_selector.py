"""Brand Selector.

Maps the vision read's aesthetic + market_segment + category to a short list
of brands from the curated universe. We score brands by token overlap with
aesthetic/category facets and return the top K.

Returning a *short list* (4-6 brands) keeps downstream search costs bounded
and matches the brief's principle: don't scan all brands blindly.
"""
from __future__ import annotations

from collections import Counter

from app.data.brands import BRANDS, Brand
from app.schemas import ImageRead


SEGMENT_HINTS = {
    "premium": "premium_contemporary",
    "premium contemporary": "premium_contemporary",
    "minimal": "premium_contemporary",
    "luxury": "luxury_reference",
    "fast fashion": "global_fast_fashion",
    "high street": "global_fast_fashion",
    "trend": "global_fast_fashion",
    "youth": "youth_digital",
    "gen z": "youth_digital",
    "street": "sports_street",
    "athletic": "sports_street",
    "sport": "sports_street",
    "denim": "denim_casual",
    "americana": "denim_casual",
    "indian": "india",
    "ethnic": "india",
    "indowestern": "india",
}


def _aggregate(reads: list[ImageRead]) -> dict[str, list[str]]:
    """Flatten N image reads into pooled facets."""
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
    """Derive likely brand segments from extracted text."""
    out: set[str] = set()
    haystack = " ".join(segments + aesthetics).lower()
    for hint, seg in SEGMENT_HINTS.items():
        if hint in haystack:
            out.add(seg)
    if not out:
        out.update({"global_fast_fashion", "premium_contemporary"})
    return out


def select(reads: list[ImageRead], *, top_k: int = 5) -> list[Brand]:
    facets = _aggregate(reads)
    targets = _segment_targets(facets["segments"], facets["aesthetics"])

    counter: Counter[str] = Counter()
    for b in BRANDS:
        score = 0
        if b.segment in targets:
            score += 4
        for token in facets["aesthetics"] + facets["keywords"]:
            if any(token in a for a in b.aesthetics):
                score += 2
        for token in facets["categories"]:
            if any(token in c for c in b.categories):
                score += 1
        if score:
            counter[b.name] = score

    if not counter:
        # Sensible default for cold start: a spread across high-street + premium
        default = ["Zara", "H&M", "Uniqlo", "COS", "Massimo Dutti"]
        return [b for b in BRANDS if b.name in default][:top_k]

    top_names = [name for name, _ in counter.most_common(top_k)]
    name_to_brand = {b.name: b for b in BRANDS}
    return [name_to_brand[n] for n in top_names if n in name_to_brand]

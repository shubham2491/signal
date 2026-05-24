"""Search Agent.

Builds retailer-scoped queries from vision keywords and pulls fresh snippets
via Tavily. The brief's example:

    site:zara.com oversized neutral utility tee
    site:cos.com minimal oversized knitwear

We construct one query per (brand, top-3 keywords) combo, fan them out in
parallel, and group results by brand for the Commentary Agent.
"""
from __future__ import annotations

from app.data.brands import Brand
from app.schemas import ImageRead
from app.services.search import get_search


def _top_keywords(reads: list[ImageRead], k: int = 4) -> list[str]:
    """Pick the most common keywords across all reads."""
    from collections import Counter
    c: Counter[str] = Counter()
    for r in reads:
        for kw in r.keywords:
            kw_l = kw.lower().strip()
            if kw_l:
                c[kw_l] += 1
    return [w for w, _ in c.most_common(k)]


def build_queries(brands: list[Brand], reads: list[ImageRead]) -> dict[str, str]:
    """Return brand_name -> query."""
    kws = _top_keywords(reads)
    # Pull the dominant category if any reads carry one
    cats = [r.attributes.category for r in reads if r.attributes.category]
    cat = cats[0] if cats else ""
    queries: dict[str, str] = {}
    for b in brands:
        parts = [f"site:{b.domain}"] + kws[:3]
        if cat:
            parts.append(cat)
        queries[b.name] = " ".join(parts)
    return queries


async def run(brands: list[Brand], reads: list[ImageRead]) -> dict[str, list[dict]]:
    search = get_search()
    queries = build_queries(brands, reads)
    if not search.is_available or not queries:
        return {name: [] for name in queries}

    # Fan out in parallel
    names = list(queries.keys())
    qlist = [queries[n] for n in names]
    flat = await search.search_many(qlist, max_results=3)

    grouped: dict[str, list[dict]] = {n: [] for n in names}
    # Walk flat results and re-bucket by source query → brand
    q_to_brand = {queries[n]: n for n in names}
    for item in flat:
        brand = q_to_brand.get(item.get("query", ""))
        if brand:
            grouped[brand].append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            })
    return grouped

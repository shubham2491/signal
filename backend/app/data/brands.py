"""Curated brand universe for SIGNAL.

Anchored to the user persona: an Indian fast-fashion designer at
Zudio / Westside / Pantaloons level, who needs to translate ASPIRATIONAL
global cues into AFFORDABLE Indian floor sets.

Two main tiers:
  - global_aspirational : Zara, H&M, Uniqlo, COS, Mango, Massimo Dutti,
                          Arket, & Other Stories, Theory, Reiss, etc.
                          "This is the look I want to translate."
  - india_competitive   : Zudio, Westside, Pantaloons, Max, Reliance
                          Trends, V-Mart, Bewakoof, The Souled Store.
                          "This is what I'll fight against on the floor."
  - india_premium       : Nicobar, FabIndia, Good Earth, Anita Dongre,
                          Doodlage — used only when the read leans
                          ethnic / craft / indo-fusion.

Deliberately excluded:
  - Maisons (Prada, Gucci, Chanel, LV, Loewe, Bottega, Balenciaga,
    Jacquemus, Acne, Miu Miu, Saint Laurent, Dior, Hermes) — not
    useful reference for fast-fashion floor sets.
  - Indian mid-tier branded labels (Snitch, Wrogn, Jack & Jones, AND,
    Biba, Aurelia, Allen Solly, Van Heusen, Louis Philippe, etc.) —
    they sit between the aspirational anchor and the Indian competitive
    shelf, and aren't useful comparators in either direction.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Brand:
    name: str
    domain: str
    segment: str
    aesthetics: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    market: tuple[str, ...] = field(default_factory=tuple)


BRANDS: list[Brand] = [
    # ─── Global aspirational anchors (the look to translate) ─────────────────
    Brand("Zara",             "zara.com",             "global_aspirational",
          ("trend-forward", "minimal", "tailored", "edgy", "european",
           "fast-trend", "going-out"),
          ("women", "men", "denim", "outerwear", "knits", "dresses",
           "tailored", "co-ord"), ("global", "in")),
    Brand("H&M",              "hm.com",               "global_aspirational",
          ("commercial", "basics", "trend-light", "broad-appeal"),
          ("women", "men", "kids", "basics"), ("global", "in")),
    Brand("Uniqlo",           "uniqlo.com",           "global_aspirational",
          ("minimal", "basics", "functional", "japanese", "tech-fabric",
           "elevated-basics"),
          ("basics", "knits", "outerwear", "tech-fabric"), ("global", "in")),
    Brand("Mango",            "shop.mango.com",       "global_aspirational",
          ("contemporary", "feminine", "european", "tailored",
           "elevated-mass"),
          ("women", "tailored", "denim"), ("global", "in")),
    Brand("COS",              "cos.com",              "global_aspirational",
          ("minimal", "architectural", "editorial", "elevated"),
          ("knits", "tailored", "outerwear"), ("global",)),
    Brand("& Other Stories",  "stories.com",          "global_aspirational",
          ("scandi", "feminine", "editorial", "elevated"),
          ("women", "dresses", "knits"), ("global",)),
    Brand("Arket",            "arket.com",            "global_aspirational",
          ("minimal", "functional", "scandi", "quiet"),
          ("basics", "outerwear", "knits"), ("global",)),
    Brand("Weekday",          "weekday.com",          "global_aspirational",
          ("scandi", "minimal", "denim", "youth-elevated"),
          ("denim", "tees", "knits"), ("global",)),
    Brand("Massimo Dutti",    "massimodutti.com",     "global_aspirational",
          ("tailored", "premium-mass", "minimal", "elevated", "european"),
          ("tailored", "knits", "outerwear"), ("global", "in")),
    Brand("Theory",           "theory.com",           "global_aspirational",
          ("tailored", "minimal", "office", "elevated"),
          ("tailored", "outerwear"), ("global",)),
    Brand("Reiss",            "reiss.com",            "global_aspirational",
          ("tailored", "premium-mass", "british", "going-out"),
          ("tailored", "dresses"), ("global",)),
    Brand("AllSaints",        "allsaints.com",        "global_aspirational",
          ("edgy", "leather", "british", "rock-tinged"),
          ("outerwear", "leather", "denim"), ("global",)),
    Brand("Everlane",         "everlane.com",         "global_aspirational",
          ("minimal", "ethical", "elevated-basics", "transparent"),
          ("basics", "denim", "knits"), ("global",)),
    Brand("Madewell",         "madewell.com",         "global_aspirational",
          ("americana", "elevated-denim", "casual", "preppy-adjacent"),
          ("denim", "basics"), ("global",)),
    Brand("Reformation",      "thereformation.com",   "global_aspirational",
          ("feminine", "sustainable", "occasion", "trend-forward"),
          ("women", "dresses", "occasion"), ("global",)),
    Brand("Sezane",           "sezane.com",           "global_aspirational",
          ("parisian", "feminine", "soft", "elevated"),
          ("women", "knits", "blouses"), ("global",)),
    Brand("Aritzia",          "aritzia.com",          "global_aspirational",
          ("contemporary", "minimal", "north-american", "polished"),
          ("women", "tailored", "knits"), ("global",)),
    Brand("Mango Man",        "shop.mango.com/man",   "global_aspirational",
          ("tailored", "european", "smart-casual"),
          ("men", "tailored"), ("global", "in")),

    # ─── Indian competitive shelf (the actual fight at price) ────────────────
    Brand("Zudio",            "zudio.com",            "india_competitive",
          ("trend-on-budget", "youth", "broad-appeal", "fast-trend",
           "value", "shelf-velocity"),
          ("women", "men", "youth", "denim", "tees", "co-ord"), ("in",)),
    Brand("Westside",         "westside.com",         "india_competitive",
          ("contemporary", "private-label", "minimal", "feminine",
           "elevated-mass"),
          ("women", "men", "denim", "ethnic", "co-ord"), ("in",)),
    Brand("Pantaloons",       "pantaloons.com",       "india_competitive",
          ("commercial", "private-label", "family", "broad"),
          ("women", "men", "ethnic", "denim", "kids"), ("in",)),
    Brand("Max Fashion",      "maxfashion.in",        "india_competitive",
          ("commercial", "family", "basics", "value"),
          ("women", "men", "kids", "basics"), ("in",)),
    Brand("Reliance Trends",  "trends.ajio.com",      "india_competitive",
          ("commercial", "value", "family", "broad"),
          ("women", "men", "ethnic"), ("in",)),
    Brand("V-Mart",           "vmart.co.in",          "india_competitive",
          ("value", "tier-2-3", "family"),
          ("women", "men", "kids"), ("in",)),
    Brand("Bewakoof",         "bewakoof.com",         "india_competitive",
          ("youth", "graphic", "casual", "value", "digital-first"),
          ("youth", "graphics", "tees"), ("in",)),
    Brand("The Souled Store", "thesouledstore.com",   "india_competitive",
          ("youth", "graphic", "fandom", "digital-first"),
          ("youth", "graphics", "tees"), ("in",)),

    # ─── India premium / craft (only when read leans ethnic) ─────────────────
    Brand("Nicobar",          "nicobar.com",          "india_premium",
          ("minimal", "indo-western", "natural-fabric", "elevated", "craft"),
          ("women", "men", "indo-western"), ("in",)),
    Brand("FabIndia",         "fabindia.com",         "india_premium",
          ("ethnic", "craft", "natural-fabric", "handloom"),
          ("ethnic", "men", "women"), ("in",)),
    Brand("Good Earth",       "goodearth.in",         "india_premium",
          ("craft", "minimal", "natural", "elevated-india"),
          ("women", "men", "indo-western"), ("in",)),
    Brand("Anita Dongre",     "anitadongre.com",      "india_premium",
          ("ethnic", "occasion", "embroidery", "craft"),
          ("ethnic", "occasion"), ("in",)),
    Brand("Doodlage",         "doodlage.in",          "india_premium",
          ("sustainable", "craft", "upcycled"),
          ("women", "men"), ("in",)),
]


def brand_by_name(name: str) -> Brand | None:
    for b in BRANDS:
        if b.name.lower() == name.lower():
            return b
    return None

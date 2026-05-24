"""Curated brand universe for SIGNAL — Indian retail anchored.

Three tiers, all India-focused:
  - india_value           : mass-market price-driven (Zudio, Pantaloons, Max, ...)
  - india_mid_premium     : sub-luxury, full-price (Allen Solly, AND, Snitch, ...)
  - india_premium         : elevated India contemporary (Nicobar, FabIndia, Anita Dongre)
  - global_in             : global brands with strong India presence (Zara, H&M, Uniqlo, ...)

We do NOT include luxury (Prada, Loewe, etc.) — they are not useful reference
points for the value and mid-premium designers SIGNAL is built for.
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
    # ─── Indian value (price-led, high-volume floor sets) ────────────────────
    Brand("Zudio",            "zudio.com",            "india_value",
          ("trend-on-budget", "youth", "basics", "fast-trend"),
          ("women", "men", "youth", "denim", "tees"), ("in",)),
    Brand("Max Fashion",      "maxfashion.in",        "india_value",
          ("commercial", "family", "basics"),
          ("women", "men", "kids", "basics"), ("in",)),
    Brand("Pantaloons",       "pantaloons.com",       "india_value",
          ("commercial", "private-label", "family"),
          ("women", "men", "ethnic", "denim"), ("in",)),
    Brand("Reliance Trends",  "trends.ajio.com",      "india_value",
          ("commercial", "value", "family"),
          ("women", "men", "ethnic"), ("in",)),
    Brand("V-Mart",           "vmart.co.in",          "india_value",
          ("value", "tier-2-3", "family"),
          ("women", "men", "kids"), ("in",)),
    Brand("Style Union",      "styleunion.in",        "india_value",
          ("youth", "denim", "value"), ("youth", "denim"), ("in",)),
    Brand("Bewakoof",         "bewakoof.com",         "india_value",
          ("youth", "graphic", "casual", "value"),
          ("youth", "graphics", "tees"), ("in",)),
    Brand("The Souled Store", "thesouledstore.com",   "india_value",
          ("youth", "graphic", "fandom"),
          ("youth", "graphics", "tees"), ("in",)),

    # ─── Indian mid-premium (full price, contemporary cuts) ──────────────────
    Brand("Westside",         "westside.com",         "india_mid_premium",
          ("contemporary", "private-label", "minimal", "feminine"),
          ("women", "men", "denim", "ethnic"), ("in",)),
    Brand("Allen Solly",      "allensolly.com",       "india_mid_premium",
          ("workwear", "tailored", "preppy", "casual-friday"),
          ("men", "women", "tailored", "polos"), ("in",)),
    Brand("Van Heusen",       "vanheusenindia.com",   "india_mid_premium",
          ("workwear", "tailored", "formal"),
          ("men", "women", "tailored"), ("in",)),
    Brand("Louis Philippe",   "louisphilippe.com",    "india_mid_premium",
          ("formal", "tailored", "elevated-business"),
          ("men", "tailored"), ("in",)),
    Brand("Park Avenue",      "parkavenue.in",        "india_mid_premium",
          ("formal", "workwear", "tailored"), ("men", "tailored"), ("in",)),
    Brand("Peter England",    "peterengland.abfrl.in","india_mid_premium",
          ("workwear", "casual-smart"), ("men", "tailored"), ("in",)),
    Brand("Wrogn",            "wrogn.com",            "india_mid_premium",
          ("youth", "men", "streetwear-lite", "trend"),
          ("men", "youth", "denim"), ("in",)),
    Brand("Snitch",           "snitch.co.in",         "india_mid_premium",
          ("youth", "men", "trend-fast", "going-out"),
          ("men", "youth", "shirts"), ("in",)),
    Brand("Damensch",         "damensch.com",         "india_mid_premium",
          ("men", "innerwear", "casual"), ("men", "basics"), ("in",)),
    Brand("Bombay Shirt Co",  "bombayshirts.com",     "india_mid_premium",
          ("men", "tailored", "shirts", "made-to-measure"),
          ("men", "shirts"), ("in",)),
    Brand("AND",              "andindia.com",         "india_mid_premium",
          ("indowestern", "feminine", "contemporary"),
          ("women",), ("in",)),
    Brand("Global Desi",      "globaldesi.com",       "india_mid_premium",
          ("ethnic", "contemporary", "boho-fusion"),
          ("women", "ethnic"), ("in",)),
    Brand("W for Woman",      "wforwoman.com",        "india_mid_premium",
          ("ethnic", "feminine", "everyday-fusion"),
          ("women", "ethnic"), ("in",)),
    Brand("Biba",             "biba.in",              "india_mid_premium",
          ("ethnic", "feminine", "festive"),
          ("women", "ethnic"), ("in",)),
    Brand("Aurelia",          "aurelialifestyle.com", "india_mid_premium",
          ("ethnic", "everyday-fusion", "value"),
          ("women", "ethnic"), ("in",)),
    Brand("Soch",             "soch.com",             "india_mid_premium",
          ("ethnic", "festive", "feminine"),
          ("women", "ethnic", "sarees"), ("in",)),
    Brand("Rangmanch",        "pantaloons.com",       "india_mid_premium",
          ("ethnic", "everyday-fusion"), ("women", "ethnic"), ("in",)),
    Brand("Vero Moda",        "veromoda.in",          "india_mid_premium",
          ("feminine", "tailored", "european-via-india"),
          ("women", "tailored"), ("in",)),
    Brand("ONLY",             "only.in",              "india_mid_premium",
          ("youth", "denim", "feminine"),
          ("women", "denim"), ("in",)),
    Brand("Jack & Jones",     "jackjones.in",         "india_mid_premium",
          ("men", "casual", "denim", "european-via-india"),
          ("men", "denim"), ("in",)),
    Brand("US Polo Assn",     "uspoloassnindia.com",  "india_mid_premium",
          ("preppy", "casual", "polos"),
          ("men", "polos"), ("in",)),
    Brand("Pepe Jeans India", "pepejeans.com",        "india_mid_premium",
          ("denim", "youth", "european-via-india"),
          ("denim", "youth"), ("in",)),
    Brand("Tommy Hilfiger India","tommyhilfiger.in",  "india_mid_premium",
          ("preppy", "americana", "premium-mass"),
          ("men", "women", "tailored"), ("in",)),

    # ─── Indian premium / contemporary craft ─────────────────────────────────
    Brand("Nicobar",          "nicobar.com",          "india_premium",
          ("minimal", "indowestern", "natural-fabric", "elevated"),
          ("women", "men", "indowestern"), ("in",)),
    Brand("FabIndia",          "fabindia.com",        "india_premium",
          ("ethnic", "craft", "natural-fabric", "handloom"),
          ("ethnic", "men", "women"), ("in",)),
    Brand("Anita Dongre",     "anitadongre.com",      "india_premium",
          ("ethnic", "occasion", "embroidery", "craft"),
          ("ethnic", "occasion"), ("in",)),
    Brand("Good Earth",       "goodearth.in",         "india_premium",
          ("craft", "minimal", "natural", "elevated-india"),
          ("women", "men", "indowestern"), ("in",)),
    Brand("Rareism",          "rareism.com",          "india_premium",
          ("contemporary", "feminine", "elevated"),
          ("women",), ("in",)),
    Brand("Rare Rabbit",      "rarerabbit.com",       "india_premium",
          ("premium", "men", "tailored", "elevated"),
          ("men", "tailored"), ("in",)),
    Brand("Rareism Studio",   "rareism.com",          "india_premium",
          ("contemporary", "studio", "tailored"), ("women",), ("in",)),

    # ─── Global accessible brands (present in India OR widely benchmarked) ──
    # No maisons (Prada, Gucci, Chanel, LV, Hermes, Loewe, Bottega, Balenciaga,
    # Jacquemus, Acne, Miu Miu, Saint Laurent, Dior).
    Brand("Zara",             "zara.com",             "global_accessible",
          ("trend-forward", "minimal", "tailored", "edgy", "european"),
          ("women", "men", "denim", "outerwear", "knits", "dresses", "tailored"),
          ("global", "in")),
    Brand("H&M",              "hm.com",               "global_accessible",
          ("commercial", "basics", "trend-light"),
          ("women", "men", "basics"), ("global", "in")),
    Brand("Uniqlo",           "uniqlo.com",           "global_accessible",
          ("minimal", "basics", "functional", "japanese"),
          ("basics", "knits", "outerwear", "tech-fabric"), ("global", "in")),
    Brand("Mango",            "shop.mango.com",       "global_accessible",
          ("contemporary", "feminine", "european", "tailored"),
          ("women", "tailored"), ("global", "in")),
    Brand("COS",              "cos.com",              "global_accessible",
          ("minimal", "architectural", "editorial"),
          ("knits", "tailored", "outerwear"), ("global",)),
    Brand("Arket",            "arket.com",            "global_accessible",
          ("minimal", "functional", "scandi"),
          ("basics", "outerwear", "knits"), ("global",)),
    Brand("Weekday",          "weekday.com",          "global_accessible",
          ("scandi", "minimal", "denim"), ("denim", "tees"), ("global",)),
    Brand("Massimo Dutti",    "massimodutti.com",     "global_accessible",
          ("tailored", "premium", "minimal", "elevated"),
          ("tailored", "knits", "outerwear"), ("global", "in")),
    Brand("Theory",           "theory.com",           "global_accessible",
          ("tailored", "minimal", "office"), ("tailored",), ("global",)),
    Brand("Reiss",            "reiss.com",            "global_accessible",
          ("tailored", "premium", "british"), ("tailored",), ("global",)),
    Brand("AllSaints",        "allsaints.com",        "global_accessible",
          ("edgy", "leather", "british"),
          ("outerwear", "leather"), ("global",)),
    Brand("Everlane",         "everlane.com",         "global_accessible",
          ("minimal", "ethical", "elevated-basics"),
          ("basics", "denim"), ("global",)),
    Brand("Club Monaco",      "clubmonaco.com",       "global_accessible",
          ("preppy", "elevated", "minimal"), ("tailored",), ("global",)),
    Brand("Levi's",           "levi.com",             "global_accessible",
          ("denim", "americana", "classic"),
          ("denim",), ("global", "in")),
    Brand("GAP",              "gap.com",              "global_accessible",
          ("americana", "basics", "preppy"),
          ("basics", "denim"), ("global", "in")),
    Brand("Marks & Spencer",  "marksandspencer.in",   "global_accessible",
          ("tailored", "british", "premium-mass"),
          ("women", "men", "basics"), ("global", "in")),
]


def brand_by_name(name: str) -> Brand | None:
    for b in BRANDS:
        if b.name.lower() == name.lower():
            return b
    return None

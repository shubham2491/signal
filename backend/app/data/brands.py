"""Curated brand universe for SIGNAL.

We intentionally exclude marketplaces (Zudio, Ajio, Myntra, etc.) and stay
brand-focused. Each brand carries facets the Brand Selector uses to short-list
candidates after vision extracts attributes.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Brand:
    name: str
    domain: str
    segment: str          # global_fast_fashion | youth_digital | premium_contemporary
                          # | sports_street | denim_casual | luxury_reference | india
    aesthetics: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    market: tuple[str, ...] = field(default_factory=tuple)   # eg ("global", "in")


BRANDS: list[Brand] = [
    # Global fast fashion
    Brand("Zara",          "zara.com",          "global_fast_fashion",
          ("trend-forward", "minimal", "tailored", "edgy"),
          ("women", "men", "denim", "outerwear", "knits", "dresses"),
          ("global", "in")),
    Brand("H&M",           "hm.com",            "global_fast_fashion",
          ("commercial", "basics", "trend-light"), ("women", "men", "basics"),
          ("global", "in")),
    Brand("Uniqlo",        "uniqlo.com",        "global_fast_fashion",
          ("minimal", "basics", "functional", "japanese"),
          ("basics", "knits", "outerwear", "tech-fabric"), ("global",)),
    Brand("Mango",         "shop.mango.com",    "global_fast_fashion",
          ("contemporary", "feminine", "european"), ("women", "tailored"),
          ("global", "in")),
    Brand("Bershka",       "bershka.com",       "global_fast_fashion",
          ("youth", "streetwear", "trend"), ("youth", "denim", "graphics"),
          ("global",)),
    Brand("Pull&Bear",     "pullandbear.com",   "global_fast_fashion",
          ("youth", "casual", "streetwear"), ("youth", "denim"), ("global",)),
    Brand("Stradivarius",  "stradivarius.com",  "global_fast_fashion",
          ("youth", "feminine", "trend"), ("women", "youth"), ("global",)),
    Brand("Massimo Dutti", "massimodutti.com",  "premium_contemporary",
          ("tailored", "premium", "minimal", "elevated"),
          ("tailored", "knits", "outerwear"), ("global", "in")),
    Brand("COS",           "cos.com",           "premium_contemporary",
          ("minimal", "architectural", "editorial"),
          ("knits", "tailored", "outerwear"), ("global",)),
    Brand("Weekday",       "weekday.com",       "youth_digital",
          ("scandi", "minimal", "denim"), ("denim", "tees"), ("global",)),
    Brand("Arket",         "arket.com",         "premium_contemporary",
          ("minimal", "functional", "scandi"), ("basics", "outerwear"), ("global",)),
    Brand("Monki",         "monki.com",         "youth_digital",
          ("colorful", "youth", "playful"), ("women", "youth"), ("global",)),
    Brand("Primark",       "primark.com",       "global_fast_fashion",
          ("budget", "trend", "basics"), ("basics", "denim"), ("global",)),
    Brand("Urban Revivo",  "urbanrevivo.com",   "global_fast_fashion",
          ("trend", "contemporary", "feminine"), ("women", "tailored"), ("global",)),

    # Youth / digital brands
    Brand("Urbanic",       "urbanic.com",       "youth_digital",
          ("youth", "trend", "feminine"), ("women", "youth"), ("in",)),
    Brand("ASOS Design",   "asos.com",          "youth_digital",
          ("youth", "trend", "inclusive"), ("youth", "women", "men"), ("global",)),
    Brand("Boohoo",        "boohoo.com",        "youth_digital",
          ("youth", "fast-trend"), ("youth", "women"), ("global",)),
    Brand("PrettyLittleThing", "prettylittlething.com", "youth_digital",
          ("youth", "feminine", "going-out"), ("women", "youth"), ("global",)),
    Brand("Princess Polly","princesspolly.com", "youth_digital",
          ("youth", "minimal", "feminine"), ("women", "youth"), ("global",)),
    Brand("Fashion Nova",  "fashionnova.com",   "youth_digital",
          ("body-con", "going-out", "trend"), ("women",), ("global",)),

    # Premium contemporary
    Brand("Everlane",      "everlane.com",      "premium_contemporary",
          ("minimal", "ethical", "elevated-basics"),
          ("basics", "denim"), ("global",)),
    Brand("Reiss",         "reiss.com",         "premium_contemporary",
          ("tailored", "premium", "british"), ("tailored",), ("global",)),
    Brand("Theory",        "theory.com",        "premium_contemporary",
          ("tailored", "minimal", "office"), ("tailored",), ("global",)),
    Brand("Club Monaco",   "clubmonaco.com",    "premium_contemporary",
          ("preppy", "elevated", "minimal"), ("tailored",), ("global",)),
    Brand("AllSaints",     "allsaints.com",     "premium_contemporary",
          ("edgy", "leather", "british"), ("outerwear", "leather"), ("global",)),

    # Sports / street
    Brand("Nike",          "nike.com",          "sports_street",
          ("sport", "performance", "streetwear"),
          ("sportswear", "footwear"), ("global",)),
    Brand("Adidas",        "adidas.com",        "sports_street",
          ("sport", "performance", "streetwear"),
          ("sportswear", "footwear"), ("global",)),
    Brand("Puma",          "puma.com",          "sports_street",
          ("sport", "performance"), ("sportswear", "footwear"), ("global",)),
    Brand("Vans",          "vans.com",          "sports_street",
          ("skate", "street", "youth"), ("footwear", "youth"), ("global",)),
    Brand("Converse",      "converse.com",      "sports_street",
          ("street", "classic", "youth"), ("footwear",), ("global",)),

    # Denim / casual
    Brand("Levi's",        "levi.com",          "denim_casual",
          ("denim", "americana", "classic"), ("denim",), ("global", "in")),
    Brand("GAP",           "gap.com",           "denim_casual",
          ("americana", "basics", "preppy"), ("basics", "denim"), ("global",)),
    Brand("Wrangler",      "wrangler.com",      "denim_casual",
          ("denim", "western", "americana"), ("denim",), ("global",)),
    Brand("Lee",           "lee.com",           "denim_casual",
          ("denim", "americana"), ("denim",), ("global",)),
    Brand("American Eagle","ae.com",            "denim_casual",
          ("denim", "youth", "americana"), ("denim", "youth"), ("global",)),

    # Luxury reference
    Brand("Prada",         "prada.com",         "luxury_reference",
          ("luxury", "italian", "minimal", "intellectual"),
          ("women", "men"), ("global",)),
    Brand("Balenciaga",    "balenciaga.com",    "luxury_reference",
          ("luxury", "avant-garde", "streetwear"),
          ("outerwear", "footwear"), ("global",)),
    Brand("Jacquemus",     "jacquemus.com",     "luxury_reference",
          ("luxury", "mediterranean", "playful"), ("women",), ("global",)),
    Brand("Acne Studios",  "acnestudios.com",   "luxury_reference",
          ("luxury", "scandi", "denim"), ("denim", "knits"), ("global",)),
    Brand("Loewe",         "loewe.com",         "luxury_reference",
          ("luxury", "craft", "leather"), ("leather", "women", "men"), ("global",)),
    Brand("Bottega Veneta","bottegaveneta.com", "luxury_reference",
          ("luxury", "italian", "leather"), ("leather",), ("global",)),
    Brand("Miu Miu",       "miumiu.com",        "luxury_reference",
          ("luxury", "feminine", "italian"), ("women",), ("global",)),

    # India layer
    Brand("AND",           "andindia.com",      "india",
          ("indowestern", "feminine", "contemporary"), ("women",), ("in",)),
    Brand("Global Desi",   "globaldesi.com",    "india",
          ("ethnic", "contemporary", "feminine"), ("women",), ("in",)),
    Brand("ONLY",          "only.in",           "global_fast_fashion",
          ("youth", "denim", "feminine"), ("women", "denim"), ("global", "in")),
    Brand("Vero Moda",     "veromoda.in",       "global_fast_fashion",
          ("feminine", "tailored", "contemporary"), ("women",), ("global", "in")),
    Brand("Jack & Jones",  "jackjones.in",      "global_fast_fashion",
          ("men", "casual", "denim"), ("men", "denim"), ("global", "in")),
    Brand("Selected",      "selected.com",      "premium_contemporary",
          ("tailored", "scandi", "elevated"), ("men", "tailored"), ("global", "in")),
    Brand("Rare Rabbit",   "rarerabbit.com",    "india",
          ("premium", "men", "tailored"), ("men",), ("in",)),
    Brand("Snitch",        "snitch.co.in",      "india",
          ("youth", "men", "trend"), ("men", "youth"), ("in",)),
    Brand("The Souled Store", "thesouledstore.com", "india",
          ("youth", "graphic", "casual"), ("youth", "graphics"), ("in",)),
    Brand("Bewakoof",      "bewakoof.com",      "india",
          ("youth", "graphic", "value"), ("youth", "graphics"), ("in",)),
    Brand("Bonkers Corner","bonkerscorner.com", "india",
          ("youth", "streetwear", "graphic"), ("youth",), ("in",)),
    Brand("US Polo",       "uspoloassn.com",    "india",
          ("preppy", "casual"), ("men", "polos"), ("global", "in")),
    Brand("Allen Solly",   "allensolly.com",    "india",
          ("workwear", "tailored", "men"), ("men", "tailored"), ("in",)),
    Brand("Van Heusen",    "vanheusenindia.com","india",
          ("workwear", "tailored"), ("men", "tailored"), ("in",)),
    Brand("W for Woman",   "wforwoman.com",     "india",
          ("ethnic", "feminine"), ("women", "ethnic"), ("in",)),
    Brand("FabIndia",      "fabindia.com",      "india",
          ("ethnic", "craft", "natural"), ("ethnic",), ("in",)),
    Brand("Nicobar",       "nicobar.com",       "india",
          ("minimal", "indowestern", "natural"), ("women", "men"), ("in",)),
]


def brand_by_name(name: str) -> Brand | None:
    for b in BRANDS:
        if b.name.lower() == name.lower():
            return b
    return None

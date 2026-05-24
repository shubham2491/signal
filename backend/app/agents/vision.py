"""Vision Agent.

Reads N images and extracts apparel-only attributes. Identity-blind by
construction: the prompt instructs the model to ignore faces, body, identity.

For >1 images we send them in one call (per-image entries indexed) so the
model can produce internally consistent reads.
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas import ImageRead, VisionAttributes
from app.services.llm import get_llm

log = logging.getLogger(__name__)

SYSTEM = """You are SIGNAL's Vision Agent for Indian fashion designers
working in value and mid-premium retail (Zudio, Westside, Pantaloons,
Allen Solly, Snitch, AND, Biba, etc.). Be concrete and design-literate.

Identity-blind: never describe faces, body type, race, gender expression,
or any personal identifier. Only the garments and their construction.

For each image extract DESIGN-USEFUL specifics PLUS two GROUPING signals
the pipeline uses to cluster multi-image uploads:

  - shot_type:      what KIND of shot this is, one of
                    "flatlay" (product on flat surface, no model),
                    "store_walk" (rack / shelf / store interior),
                    "lookbook" (styled on model in editorial setting),
                    "runway" (catwalk),
                    "model_shot" (garment on model, plain),
                    "unknown".
  - category_group: which broad category this belongs to, one of
                    "top" (tee/shirt/blouse/kurta-top),
                    "bottom" (jeans/trousers/skirt/palazzo),
                    "outerwear" (jacket/blazer/coat/shacket),
                    "dress" (dress/jumpsuit/one-piece),
                    "ethnic" (full kurta-set/lehenga/saree/indo-fusion set),
                    "footwear",
                    "accessory" (bag/jewellery/scarf),
                    "co_ord" (matching top+bottom set),
                    "unknown".

And the design-specific extraction:
  - category:     the actual garment (e.g. "drop-shoulder graphic tee",
                  "co-ord set kurta-pant", "high-waist wide-leg denim").
                  Never just "top" or "shirt".
  - silhouette:   fit + cut + length proportions ("oversized boxy,
                  cropped above waist", "tailored slim, mid-thigh").
  - colors:       3-5 specific names. Use trade vocabulary
                  ("ecru", "rust", "kerala-green") not "light/dark".
  - fabric_guess: weight + weave + finish if visible
                  ("220gsm heavyweight cotton jersey, brushed interior").
  - styling:      what's worn/styled with it ("tucked-in", "layered
                  under utility vest", "open-front over slip dress").
  - trims:        zippers, buttons, eyelets, embroidery, prints,
                  patch pockets, top-stitch detail — be specific.
  - aesthetic:    one short phrase grounded in Indian retail vocabulary
                  ("Y2K going-out", "quiet-luxury workwear", "indo-fusion
                  festive", "athleisure utility", "old-money preppy").
  - market_segment: which Indian tier this would slot into — one of:
                  "value" / "mid-premium" / "premium-contemporary".
  - notes:        anything design-relevant the structured fields missed
                  (e.g. "graphic placement at hem only", "raw-edge hem",
                  "ribbed cuff with contrast tipping"). Keep < 25 words.

Keywords: 5-8 short tokens an Indian buyer would feed into a retailer
search ("oversized", "drop-shoulder", "tipped collar", "wide-leg",
"co-ord", "indo-fusion"). Lowercase, no punctuation.

If an image is low quality or unrelated to apparel, still produce a best
attempt — never hard-refuse.
""".strip()

SCHEMA = """
{
  "reads": [
    {
      "index": 0,
      "attributes": {
        "category": "string",
        "silhouette": "string",
        "colors": ["string"],
        "fabric_guess": "string",
        "styling": ["string"],
        "trims": ["string"],
        "aesthetic": "string",
        "market_segment": "string",
        "notes": "string",
        "shot_type": "flatlay | store_walk | lookbook | runway | model_shot | unknown",
        "category_group": "top | bottom | outerwear | dress | ethnic | footwear | accessory | co_ord | unknown"
      },
      "keywords": ["string"]
    }
  ]
}
""".strip()


async def run(images: list[bytes]) -> list[ImageRead]:
    if not images:
        return []
    llm = get_llm()
    if not llm.is_available:
        return _mock_reads(len(images))

    user_text = (
        f"You will see {len(images)} fashion image(s) in order, indexed from 0.\n"
        "For each image, return one entry in the 'reads' array. Keywords should\n"
        "be 4-8 short tokens a designer could feed into a retailer search\n"
        "(e.g. 'oversized', 'utility', 'neutral palette', 'cropped')."
    )
    try:
        data = await llm.vision_json(
            system=SYSTEM, user_text=user_text, images=images, schema_hint=SCHEMA,
        )
    except Exception as e:
        log.warning("Vision call failed, using mock: %s", e)
        return _mock_reads(len(images))

    raw_reads = data.get("reads") or []
    out: list[ImageRead] = []
    for i in range(len(images)):
        raw = raw_reads[i] if i < len(raw_reads) else {}
        attrs_raw = raw.get("attributes") or {}
        out.append(
            ImageRead(
                index=i,
                attributes=VisionAttributes(**_coerce_attrs(attrs_raw)),
                keywords=[str(k) for k in (raw.get("keywords") or [])][:8],
            )
        )
    return out


_VALID_SHOT = {"flatlay", "store_walk", "lookbook", "runway", "model_shot", "unknown"}
_VALID_GROUP = {"top", "bottom", "outerwear", "dress", "ethnic", "footwear", "accessory", "co_ord", "unknown"}


def _coerce_attrs(d: dict[str, Any]) -> dict[str, Any]:
    shot = str(d.get("shot_type", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if shot not in _VALID_SHOT:
        shot = "unknown"
    group = str(d.get("category_group", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if group not in _VALID_GROUP:
        group = _guess_group_from_category(str(d.get("category", "")))
    return {
        "category": str(d.get("category", "")),
        "silhouette": str(d.get("silhouette", "")),
        "colors": [str(c) for c in (d.get("colors") or [])][:6],
        "fabric_guess": str(d.get("fabric_guess", "")),
        "styling": [str(s) for s in (d.get("styling") or [])][:6],
        "trims": [str(t) for t in (d.get("trims") or [])][:6],
        "aesthetic": str(d.get("aesthetic", "")),
        "market_segment": str(d.get("market_segment", "")),
        "notes": str(d.get("notes", "")),
        "shot_type": shot,
        "category_group": group,
    }


def _guess_group_from_category(cat: str) -> str:
    """Keyword fallback so we always have a group even if the model omits it."""
    c = cat.lower()
    if any(k in c for k in ("kurta-set", "lehenga", "saree", "anarkali", "sherwani", "indo-fusion set")):
        return "ethnic"
    if any(k in c for k in ("co-ord", "matching set", "twin set")):
        return "co_ord"
    if any(k in c for k in ("dress", "jumpsuit", "playsuit", "gown", "frock")):
        return "dress"
    if any(k in c for k in ("jacket", "blazer", "coat", "shacket", "trench", "parka", "overshirt")):
        return "outerwear"
    if any(k in c for k in ("jean", "trouser", "pant", "skirt", "shorts", "palazzo", "joggers", "chinos")):
        return "bottom"
    if any(k in c for k in ("tee", "shirt", "blouse", "top", "kurta-top", "polo", "tank", "hoodie", "sweater", "sweatshirt")):
        return "top"
    if any(k in c for k in ("shoe", "sneaker", "boot", "sandal", "loafer", "heel", "footwear")):
        return "footwear"
    if any(k in c for k in ("bag", "handbag", "tote", "purse", "wallet", "belt", "scarf", "earring", "necklace", "watch")):
        return "accessory"
    return "unknown"


def _mock_reads(n: int) -> list[ImageRead]:
    # Cycle through categories so multi-image demos exercise grouping.
    presets = [
        dict(category="drop-shoulder graphic tee", group="top",
             aesthetic="casual youth, mid-premium",
             keywords=["oversized", "drop-shoulder", "graphic"]),
        dict(category="wide-leg high-waist denim", group="bottom",
             aesthetic="contemporary denim",
             keywords=["wide-leg", "high-waist", "indigo"]),
        dict(category="cropped utility jacket", group="outerwear",
             aesthetic="utility-lite",
             keywords=["utility", "cropped", "patch-pocket"]),
        dict(category="straight-cut kurta set", group="ethnic",
             aesthetic="indo-fusion festive",
             keywords=["indo-fusion", "festive", "straight-cut"]),
    ]
    out: list[ImageRead] = []
    for i in range(n):
        p = presets[i % len(presets)] if n > 1 else presets[0]
        out.append(ImageRead(
            index=i,
            attributes=VisionAttributes(
                category=p["category"],
                silhouette="oversized boxy, hits mid-hip",
                colors=["ecru", "rust"],
                fabric_guess="220gsm cotton jersey",
                styling=["tucked-in"],
                trims=["ribbed neckline"],
                aesthetic=p["aesthetic"],
                market_segment="mid-premium",
                notes="mock vision read",
                shot_type="flatlay",
                category_group=p["group"],
            ),
            keywords=p["keywords"],
        ))
    return out

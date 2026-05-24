"""Vision Agent.

Reads N images and extracts apparel-only attributes. Identity-blind by
construction: the prompt instructs the model to ignore faces, body, identity.

For >1 images we send them in one call (per-image entries indexed) so the
model can produce internally consistent reads.

Fallback path: if the LLM vision call fails (timeout, quota, network),
we DON'T return a hardcoded mock — that's how 'every upload gives the
same brief' bugs happen. Instead we extract the dominant palette from
the image bytes using PIL and derive a category from the image hash,
so two different images yield two different mocked reads.
"""
from __future__ import annotations

import hashlib
import logging
from io import BytesIO
from typing import Any

from PIL import Image

from app.schemas import ImageRead, VisionAttributes
from app.services.llm import get_llm

log = logging.getLogger(__name__)

SYSTEM = """You are SIGNAL's Vision Agent for Indian fashion designers
working in value and mid-premium retail (Zudio, Westside, Pantaloons,
Allen Solly, Snitch, AND, Biba, etc.). Be concrete and design-literate.

Identity-blind: never describe faces, body type, race, gender expression,
or any personal identifier. Only the garments and their construction.

For each image extract DESIGN-USEFUL specifics PLUS three GROUPING signals
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
  - gender_target: who is the GARMENT designed for, one of
                    "womenswear", "menswear", "unisex", "kidswear",
                    "unknown".
                    Read this from GARMENT cues, never the person wearing it:
                    button-side (men's button on right, women's on left),
                    silhouette conventions (e.g. dropped-shoulder
                    short-sleeve denim shirt = menswear; fit-and-flare
                    midi = womenswear), trim placement, pocket shape,
                    fly direction, common menswear vs womenswear
                    construction. If a garment is genuinely unisex
                    (e.g. boxy graphic tee, hoodie, joggers without
                    clear gendering), say "unisex". Only return
                    "unknown" if you truly cannot infer.

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
        "category_group": "top | bottom | outerwear | dress | ethnic | footwear | accessory | co_ord | unknown",
        "gender_target": "womenswear | menswear | unisex | kidswear | unknown"
      },
      "keywords": ["string"]
    }
  ]
}
""".strip()


async def run(images: list[bytes]) -> list[ImageRead]:
    """Read N images via Gemini Vision.

    Vision is the foundation of every downstream section, so we DO NOT
    fall back to a mock here — if the call fails after retry, we raise.
    The pipeline / API layer surfaces the failure as a 503 with the
    underlying error so the user sees a real failure instead of
    silently-templated text.
    """
    if not images:
        return []
    llm = get_llm()
    if not llm.is_available:
        raise RuntimeError(
            "Vision unavailable — no LLM provider configured. "
            "Set GEMINI_API_KEY (or OPENAI_API_KEY)."
        )

    user_text = (
        f"You will see {len(images)} fashion image(s) in order, indexed from 0.\n"
        "For each image, return one entry in the 'reads' array. Keywords should\n"
        "be 4-8 short tokens a designer could feed into a retailer search\n"
        "(e.g. 'oversized', 'utility', 'neutral palette', 'cropped')."
    )
    data = await llm.vision_json(
        system=SYSTEM, user_text=user_text, images=images, schema_hint=SCHEMA,
    )

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
_VALID_GENDER = {"womenswear", "menswear", "unisex", "kidswear", "unknown"}


def _coerce_attrs(d: dict[str, Any]) -> dict[str, Any]:
    shot = str(d.get("shot_type", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if shot not in _VALID_SHOT:
        shot = "unknown"
    group = str(d.get("category_group", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if group not in _VALID_GROUP:
        group = _guess_group_from_category(str(d.get("category", "")))
    raw_gender = str(d.get("gender_target", "")).strip().lower().replace("-", "").replace(" ", "")
    # Accept common variants: 'mens', 'men', 'male', 'mens-wear', 'men's wear' etc.
    if raw_gender in {"mens", "men", "male", "menswear", "boys"}:
        gender = "menswear"
    elif raw_gender in {"womens", "women", "female", "womenswear", "girls", "ladies"}:
        gender = "womenswear"
    elif raw_gender in {"unisex", "gender-neutral", "neutral", "androgynous"}:
        gender = "unisex"
    elif raw_gender in {"kids", "kidswear", "children", "child"}:
        gender = "kidswear"
    elif raw_gender in _VALID_GENDER:
        gender = raw_gender
    else:
        gender = "unknown"
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
        "gender_target": gender,
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


_MOCK_PRESETS = [
    dict(category="oversized graphic tee",         group="top",
         silhouette="boxy oversized, hits mid-hip",
         aesthetic="casual contemporary",
         keywords=["oversized", "graphic", "casual"]),
    dict(category="wide-leg high-waist denim",      group="bottom",
         silhouette="wide-leg, high-rise, full-length",
         aesthetic="elevated denim casual",
         keywords=["wide-leg", "high-waist", "denim"]),
    dict(category="cropped utility jacket",         group="outerwear",
         silhouette="cropped, structured, boxy",
         aesthetic="utility outerwear",
         keywords=["utility", "cropped", "patch-pocket"]),
    dict(category="straight-cut kurta set",         group="ethnic",
         silhouette="straight, mid-calf with cigarette pant",
         aesthetic="indo-fusion festive",
         keywords=["indo-fusion", "festive", "straight-cut"]),
    dict(category="midi shirt dress",               group="dress",
         silhouette="fluid drape, midi length, belted waist",
         aesthetic="occasion contemporary",
         keywords=["midi", "shirt-dress", "belted"]),
    dict(category="ribbed knit cardigan",           group="top",
         silhouette="cropped, ribbed, slim",
         aesthetic="elevated knitwear",
         keywords=["knitwear", "ribbed", "cropped"]),
    dict(category="tailored blazer",                group="outerwear",
         silhouette="structured single-breasted, mid-thigh",
         aesthetic="tailored office european",
         keywords=["blazer", "tailored", "office"]),
    dict(category="co-ord linen set",               group="co_ord",
         silhouette="relaxed top + wide-leg bottom",
         aesthetic="resort co-ord",
         keywords=["co-ord", "linen", "resort"]),
]


def _mock_reads_from_images(images: list[bytes]) -> list[ImageRead]:
    """Build vision reads that actually depend on the image bytes.

    For each image:
      - Extract the real dominant palette via PIL quantize (no LLM, ~30ms).
      - Pick a category preset deterministically from the image hash so
        the same image always yields the same mock, but two different
        images yield two different mocks.
      - Tag with a 'vision_unavailable' note so downstream + UI can see
        this was a graceful fallback, not a live read.
    """
    out: list[ImageRead] = []
    for i, img_bytes in enumerate(images):
        h = hashlib.sha1(img_bytes).digest()
        preset_idx = h[0] % len(_MOCK_PRESETS)
        p = _MOCK_PRESETS[preset_idx]
        colors = _extract_palette(img_bytes)
        out.append(ImageRead(
            index=i,
            attributes=VisionAttributes(
                category=p["category"],
                silhouette=p["silhouette"],
                colors=colors,
                fabric_guess="",
                styling=[],
                trims=[],
                aesthetic=p["aesthetic"],
                market_segment="mid-premium",
                notes=f"vision_unavailable — palette extracted locally, category inferred from image hash ({h[:4].hex()})",
                shot_type="unknown",
                category_group=p["group"],
            ),
            keywords=p["keywords"],
        ))
    return out


# ─── Local palette extraction (no LLM) ──────────────────────────────

# Map quantized RGB values to trade color names. Coarse but produces a
# distinct, plausible palette per image without any external call.
_NAMED_COLOR_SWATCHES: list[tuple[str, tuple[int, int, int]]] = [
    ("black",       (15, 15, 14)),
    ("charcoal",    (58, 58, 56)),
    ("graphite",    (77, 77, 73)),
    ("grey",        (138, 135, 128)),
    ("dove",        (183, 179, 168)),
    ("stone",       (184, 174, 158)),
    ("white",       (250, 248, 244)),
    ("off-white",   (245, 241, 230)),
    ("ivory",       (246, 239, 219)),
    ("ecru",        (232, 223, 203)),
    ("cream",       (241, 232, 209)),
    ("sand",        (217, 196, 160)),
    ("camel",       (185, 146, 90)),
    ("tobacco",     (122, 74, 45)),
    ("rust",        (167, 76, 42)),
    ("terracotta",  (185, 107, 71)),
    ("burnt sienna",(157, 74, 42)),
    ("brick",       (156, 74, 59)),
    ("burgundy",    (122, 42, 42)),
    ("wine",        (92, 31, 31)),
    ("red",         (178, 58, 46)),
    ("coral",       (227, 120, 104)),
    ("blush",       (232, 194, 188)),
    ("peach",       (240, 191, 160)),
    ("salmon",      (224, 134, 106)),
    ("mustard",     (201, 155, 48)),
    ("gold",        (197, 160, 75)),
    ("ochre",       (194, 138, 48)),
    ("olive",       (107, 106, 46)),
    ("moss",        (122, 138, 74)),
    ("sage",        (156, 170, 138)),
    ("mint",        (181, 212, 195)),
    ("forest",      (45, 79, 58)),
    ("kerala green",(31, 95, 74)),
    ("teal",        (47, 110, 110)),
    ("sky",         (138, 176, 204)),
    ("denim",       (74, 109, 140)),
    ("cobalt",      (45, 79, 184)),
    ("indigo",      (45, 62, 112)),
    ("navy",        (31, 44, 74)),
    ("midnight",    (15, 27, 46)),
    ("lavender",    (183, 170, 200)),
    ("plum",        (107, 58, 85)),
    ("aubergine",   (63, 36, 56)),
]


def _rgb_to_name(rgb: tuple[int, int, int]) -> str:
    """Nearest-neighbor lookup in our trade-color table (squared distance)."""
    r, g, b = rgb
    best_name = "neutral"
    best_d = float("inf")
    for name, (cr, cg, cb) in _NAMED_COLOR_SWATCHES:
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_d:
            best_d = d
            best_name = name
    return best_name


def _extract_palette(image_bytes: bytes, k: int = 4) -> list[str]:
    """Quantize the image to k colors and return their trade names.

    De-duplicates so a black tee with white background doesn't return
    ['black', 'black', 'white', 'black']. Filters out colors that
    appear in <3% of the pixels — those are usually edge artifacts.
    """
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((128, 128))
        quant = img.quantize(colors=k * 2, method=Image.Quantize.MEDIANCUT)
        palette_bytes = quant.getpalette() or []
        # Histogram of which quantized index each pixel maps to.
        hist = quant.histogram()
        total = sum(hist) or 1
        # Pair (count, rgb) sorted by count desc.
        scored: list[tuple[int, tuple[int, int, int]]] = []
        for idx in range(k * 2):
            count = hist[idx] if idx < len(hist) else 0
            if count / total < 0.03:
                continue
            r = palette_bytes[idx * 3] if idx * 3 < len(palette_bytes) else 0
            g = palette_bytes[idx * 3 + 1] if idx * 3 + 1 < len(palette_bytes) else 0
            b = palette_bytes[idx * 3 + 2] if idx * 3 + 2 < len(palette_bytes) else 0
            scored.append((count, (r, g, b)))
        scored.sort(reverse=True)
        # Map to names, dedupe while preserving order.
        seen: set[str] = set()
        out: list[str] = []
        for _, rgb in scored:
            name = _rgb_to_name(rgb)
            if name in seen:
                continue
            seen.add(name)
            out.append(name)
            if len(out) >= k:
                break
        return out or ["neutral"]
    except Exception as e:
        log.warning("palette extraction failed (%s: %s)", type(e).__name__, e)
        return ["neutral"]

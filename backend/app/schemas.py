from typing import Literal
from pydantic import BaseModel, Field


Mode = Literal[
    "product_study",
    "store_walk",
    "moodboard",
    "assortment_review",
    "single_image",
]


ShotType = Literal[
    "flatlay",          # product on flat surface, no model
    "store_walk",       # rack / shelf / interior shot
    "lookbook",         # styled on model in editorial setting
    "runway",           # runway / catwalk
    "model_shot",       # garment on model, not editorial
    "unknown",
]


CategoryGroup = Literal[
    "top",              # tee, shirt, blouse, kurta-top
    "bottom",           # jeans, trousers, skirt, palazzo
    "outerwear",        # jacket, blazer, coat, shacket
    "dress",            # dresses, jumpsuits, one-piece
    "ethnic",           # full kurta-sets, lehenga, saree, indo-fusion sets
    "footwear",
    "accessory",        # bags, jewellery, scarves
    "co_ord",           # matching set
    "unknown",
]


GenderTarget = Literal[
    "womenswear",
    "menswear",
    "unisex",
    "kidswear",
    "unknown",
]


class VisionAttributes(BaseModel):
    """Per-image attribute extraction from the Vision Agent."""

    category: str = Field(default="", description="Tee, jacket, dress, etc.")
    silhouette: str = ""
    colors: list[str] = []
    fabric_guess: str = ""
    styling: list[str] = []
    trims: list[str] = []
    aesthetic: str = ""
    market_segment: str = ""
    notes: str = ""
    # Phase 2: grouping signals
    shot_type: ShotType = "unknown"
    category_group: CategoryGroup = "unknown"
    # Phase 6: who is the garment FOR (read from styling cues, not the model)
    gender_target: GenderTarget = "unknown"


class ImageRead(BaseModel):
    """Vision read of one image."""

    index: int
    attributes: VisionAttributes
    keywords: list[str] = []


class BrandSignal(BaseModel):
    brand: str
    similarity: Literal["Strong", "Adjacent", "Moderate", "Weak"]
    rationale: str
    citations: list[str] = []


class Direction(BaseModel):
    label: Literal["Safe Commercial", "Trend Forward", "Differentiated Route"]
    title: str
    description: str
    price_band_inr: str = ""
    complexity: Literal["easy", "medium", "hard", ""] = ""
    timing: str = ""
    image_url: str = ""
    image_prompt: str = ""  # what we asked the image model for (debug + iterate)


class GroupReport(BaseModel):
    """A per-category sub-report emitted when the upload contains multiple
    category groups (e.g. tops + bottoms + outerwear). Mirrors the top-level
    report fields at a finer grain."""

    group_id: CategoryGroup
    label: str                       # human label, e.g. "Tops", "Outerwear"
    image_indices: list[int]         # indices into the original upload
    observation: str
    summary: str
    brand_signals: list[BrandSignal]
    commentary: str
    directions: list[Direction]
    keywords: list[str] = []


class AnalysisReport(BaseModel):
    """Top-level result returned by POST /analyze."""

    id: str
    mode: Mode
    mode_confidence: float = 0.0
    image_count: int
    observation: str
    summary: str
    brand_signals: list[BrandSignal]
    commentary: str
    directions: list[Direction]
    keywords: list[str] = []
    reads: list[ImageRead] = []
    # Phase 2: populated when the upload spans 2+ category groups.
    groups: list[GroupReport] = []
    # Phase 4: structured actionable layer for the designer.
    palette: list[str] = []           # 4-6 named trade colors
    price_strategy: str = ""          # INR ladder + gap reasoning (no Indian retailer names)
    production_notes: str = ""        # fabric + complexity + trim spec
    merchandising: str = ""           # adjacent SKUs + shelf strategy
    # Phase 5: India-translation depth (no Indian retailer names in narrative)
    consumer: str = ""                # who buys + when worn (1-2 sentences)
    why_now: str = ""                 # why this signal lands in India now (1-2 sentences)
    india_play: str = ""              # HOW to launch: distribution + timing + format (2-3 sentences)
    price_anchor_inr: str = ""        # short: aspirational anchor (e.g. "Zara INR 2,990")
    price_floor_inr: str = ""         # short: Indian value-floor band (e.g. "INR 499-899")
    price_target_inr: str = ""        # short: recommended MRP (e.g. "INR 999-1,299")
    # Visibility: did the LLM return a real read, or did we fall back?
    data_source: Literal["live", "partial", "fallback"] = "live"


class TextBriefRequest(BaseModel):
    brief: str = Field(..., min_length=4, max_length=2000)


class RefineDirectionRequest(BaseModel):
    """Designer hands us a direction + a natural-language refinement; we
    return an updated direction (new title/description/price/image)."""
    direction: Direction
    refinement: str = Field(..., min_length=2, max_length=400)
    # Context from the parent report so the refinement stays grounded.
    observation: str = ""
    commentary: str = ""
    palette: list[str] = []


class RefineDirectionResponse(BaseModel):
    direction: Direction


class ExportRequest(BaseModel):
    report: AnalysisReport


class ExportResponse(BaseModel):
    report_id: str
    download_url: str


class EmailRequest(BaseModel):
    report: AnalysisReport
    email: str


class EmailResponse(BaseModel):
    ok: bool
    message: str
    download_url: str

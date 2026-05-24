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

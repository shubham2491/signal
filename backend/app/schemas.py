from typing import Literal
from pydantic import BaseModel, Field


Mode = Literal[
    "product_study",
    "store_walk",
    "moodboard",
    "assortment_review",
    "single_image",
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

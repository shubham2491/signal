"""SIGNAL — Fashion Signal Agent.

POST /analyze        multipart: images[] (1..N), returns AnalysisReport
POST /export-report  json: {report}, returns {report_id, download_url}
GET  /reports/{id}   serves the generated PDF (short-lived)
POST /email-report   stubbed: returns download link in the response body
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.schemas import (
    AnalysisReport,
    EmailRequest,
    EmailResponse,
    ExportRequest,
    ExportResponse,
    RefineDirectionRequest,
    RefineDirectionResponse,
    TextBriefRequest,
)
from app.services import pdf as pdf_service
from app.services import image_cache, pipeline, reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("signal")

MAX_IMAGES = 24
MAX_BYTES_PER_IMAGE = 10 * 1024 * 1024
MAX_DIM = 1600  # downscale anything larger; saves vision tokens


@asynccontextmanager
async def lifespan(_app: FastAPI):
    reports.sweep_expired()
    yield


app = FastAPI(
    title="SIGNAL",
    description="Fashion Signal Agent — image-in, intelligence-out.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "ok": True,
        "service": "signal",
        "llm_configured": settings.has_llm,
        "search_configured": settings.has_search,
        "version": app.version,
    }


@app.post("/analyze", response_model=AnalysisReport)
async def analyze(images: list[UploadFile] = File(...)) -> AnalysisReport:
    if not images:
        raise HTTPException(400, "no images provided")
    if len(images) > MAX_IMAGES:
        raise HTTPException(413, f"too many images (max {MAX_IMAGES})")

    blobs: list[bytes] = []
    for f in images:
        raw = await f.read()
        if not raw:
            raise HTTPException(400, f"empty file: {f.filename}")
        if len(raw) > MAX_BYTES_PER_IMAGE:
            raise HTTPException(413, f"file too large: {f.filename}")
        try:
            blobs.append(_normalize(raw))
        except UnidentifiedImageError:
            raise HTTPException(400, f"unreadable image: {f.filename}")

    try:
        report = await pipeline.analyze(blobs)
    except Exception as e:
        log.exception("pipeline failure")
        raise HTTPException(500, f"analysis failed: {e}") from e
    # Cache normalized blobs so /export-report can embed them in the PDF.
    image_cache.put(report.id, blobs)
    return report


@app.post("/analyze-text", response_model=AnalysisReport)
async def analyze_text(req: TextBriefRequest) -> AnalysisReport:
    """Run the brief pipeline from a free-text input (no images)."""
    try:
        return await pipeline.analyze_brief(req.brief)
    except Exception as e:
        log.exception("text brief pipeline failure")
        raise HTTPException(500, f"analysis failed: {e}") from e


@app.post("/iterate-direction", response_model=RefineDirectionResponse)
async def iterate_direction(req: RefineDirectionRequest) -> RefineDirectionResponse:
    """Apply a natural-language refinement to a single direction.

    Designer hands us the existing direction + their refinement
    ('but in linen, drop the print'); we return an updated direction
    with a freshly generated product image.
    """
    from app.agents import recommendation as recommendation_agent
    from app.services import image_gen

    try:
        updated = await recommendation_agent.refine(
            direction=req.direction,
            refinement=req.refinement,
            observation=req.observation,
            commentary=req.commentary,
            palette=req.palette,
        )
        # Regenerate the image so it matches the refined description.
        try:
            prompt = image_gen.build_prompt(updated, palette=req.palette, observation=req.observation)
            url = await image_gen.generate_image(prompt, seed=hash(req.refinement) % 100_000)
            updated.image_url = url
            updated.image_prompt = prompt
        except Exception as e:
            log.warning("refine: image regeneration failed (%s)", e)
        return RefineDirectionResponse(direction=updated)
    except Exception as e:
        log.exception("refine endpoint failure")
        raise HTTPException(500, f"refine failed: {e}") from e


@app.post("/export-report", response_model=ExportResponse)
async def export_report(req: ExportRequest) -> ExportResponse:
    images = image_cache.get(req.report.id) or []
    pdf_bytes = pdf_service.render(req.report, images=images)
    reports.save(req.report.id, pdf_bytes)
    base = get_settings().resolved_base_url.rstrip("/")
    return ExportResponse(
        report_id=req.report.id,
        download_url=f"{base}/reports/{req.report.id}",
    )


@app.get("/reports/{report_id}")
async def get_report(report_id: str) -> FileResponse:
    path = reports.path_for(report_id)
    if path is None:
        raise HTTPException(404, "report not found or expired")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"signal-{report_id[:8]}.pdf",
    )


@app.post("/email-report", response_model=EmailResponse)
async def email_report(req: EmailRequest) -> EmailResponse:
    """Stubbed: instead of sending mail we return the download link.
    The mobile client can share it via the OS share sheet.
    """
    images = image_cache.get(req.report.id) or []
    pdf_bytes = pdf_service.render(req.report, images=images)
    reports.save(req.report.id, pdf_bytes)
    base = get_settings().resolved_base_url.rstrip("/")
    link = f"{base}/reports/{req.report.id}"
    log.info("Stub-email to %s — link %s", req.email, link)
    return EmailResponse(
        ok=True,
        message=f"PDF ready. Share this link with {req.email}.",
        download_url=link,
    )


def _normalize(raw: bytes) -> bytes:
    """Re-encode to JPEG, downscale to MAX_DIM, strip EXIF/identity metadata."""
    with Image.open(BytesIO(raw)) as img:
        img = img.convert("RGB")
        img.thumbnail((MAX_DIM, MAX_DIM))
        out = BytesIO()
        img.save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()

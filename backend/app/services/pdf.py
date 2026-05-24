"""PDF export — editorial, single-column, restrained palette."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from PIL import Image as PILImage

from app.schemas import AnalysisReport

MAX_EMBEDDED_IMAGES = 10
THUMB_SIZE = 1.7 * 72  # 1.7 inches in points


CHARCOAL = colors.HexColor("#1F1F1D")
STONE = colors.HexColor("#6B6760")
EMERALD = colors.HexColor("#1F5F4A")
BURGUNDY = colors.HexColor("#7A2A2A")
WARM_WHITE = colors.HexColor("#FBF8F2")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=26, leading=30, textColor=CHARCOAL, spaceAfter=4,
            alignment=TA_LEFT,
        ),
        "kicker": ParagraphStyle(
            "kicker", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, leading=12, textColor=STONE, spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=10, leading=14, textColor=EMERALD, spaceBefore=18,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, leading=16, textColor=CHARCOAL, spaceAfter=8,
        ),
        "observation": ParagraphStyle(
            "observation", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=20, leading=24, textColor=CHARCOAL, spaceAfter=6,
        ),
        "brand_name": ParagraphStyle(
            "brand_name", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, leading=14, textColor=CHARCOAL,
        ),
        "brand_meta": ParagraphStyle(
            "brand_meta", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, leading=14, textColor=STONE,
        ),
        "dir_label": ParagraphStyle(
            "dir_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9, leading=12, textColor=BURGUNDY, spaceAfter=2,
        ),
        "dir_title": ParagraphStyle(
            "dir_title", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=CHARCOAL, spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=8, leading=10, textColor=STONE, spaceBefore=30,
        ),
    }


def _similarity_color(sim: str) -> colors.Color:
    return {
        "Strong": EMERALD,
        "Adjacent": CHARCOAL,
        "Moderate": STONE,
        "Weak": colors.HexColor("#9A938A"),
    }.get(sim, STONE)


def render(report: AnalysisReport, *, images: list[bytes] | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.7 * inch,
        title="SIGNAL Brief", author="SIGNAL",
    )
    s = _styles()
    story: list = []

    story.append(Paragraph("SIGNAL", s["h1"]))
    mode_label = report.mode.replace("_", " ").title()
    story.append(Paragraph(
        f"{mode_label} &middot; {report.image_count} image{'s' if report.image_count != 1 else ''}",
        s["kicker"],
    ))

    # Image gallery: top N inputs as a tidy grid, before the brief.
    if images:
        thumb_block = _image_grid(images[:MAX_EMBEDDED_IMAGES])
        if thumb_block is not None:
            story.append(Paragraph("INPUT IMAGES", s["section"]))
            story.append(thumb_block)

    story.append(Paragraph("OBSERVATION", s["section"]))
    story.append(Paragraph(report.observation, s["observation"]))
    if report.summary:
        story.append(Paragraph(report.summary, s["body"]))

    story.append(Paragraph("BRAND SIGNALS", s["section"]))
    rows = []
    for sig in report.brand_signals:
        rows.append([
            Paragraph(sig.brand, s["brand_name"]),
            Paragraph(
                f'<font color="{_similarity_color(sig.similarity).hexval()}">'
                f'<b>{sig.similarity}</b></font>',
                s["brand_meta"],
            ),
            Paragraph(sig.rationale, s["brand_meta"]),
        ])
    if rows:
        tbl = Table(rows, colWidths=[1.6 * inch, 1.0 * inch, 3.8 * inch])
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#E6E2D8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)

    if report.commentary:
        story.append(Paragraph("MARKET COMMENTARY", s["section"]))
        story.append(Paragraph(report.commentary, s["body"]))

    story.append(Paragraph("RECOMMENDED DIRECTIONS", s["section"]))
    for d in report.directions:
        story.append(Paragraph(d.label.upper(), s["dir_label"]))
        story.append(Paragraph(d.title, s["dir_title"]))
        story.append(Paragraph(d.description, s["body"]))
        story.append(Spacer(1, 6))

    if report.keywords:
        story.append(Paragraph("KEYWORDS", s["section"]))
        story.append(Paragraph(" &middot; ".join(report.keywords), s["body"]))

    story.append(Paragraph(
        "Analysis focuses on apparel/design attributes, not personal identity. "
        "Images are processed in memory and not retained.",
        s["footer"],
    ))

    doc.build(story)
    return buf.getvalue()


def _image_grid(images: list[bytes]) -> Table | None:
    """Lay images out 4 per row, square thumbnails. Skip any that fail to decode."""
    cells: list[RLImage] = []
    for raw in images:
        try:
            # ReportLab needs a seekable stream; downsizing keeps PDFs small.
            buf = io.BytesIO()
            with PILImage.open(io.BytesIO(raw)) as im:
                im = im.convert("RGB")
                im.thumbnail((400, 400))
                im.save(buf, "JPEG", quality=80, optimize=True)
            buf.seek(0)
            cells.append(RLImage(buf, width=THUMB_SIZE, height=THUMB_SIZE, kind="proportional"))
        except Exception:
            continue
    if not cells:
        return None
    cols = 4
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    # Pad final row so the Table is rectangular
    if rows and len(rows[-1]) < cols:
        rows[-1] += [""] * (cols - len(rows[-1]))
    tbl = Table(rows, colWidths=[THUMB_SIZE + 6] * cols)
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl

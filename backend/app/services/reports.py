"""Short-lived PDF storage.

We persist PDFs (not images) so the mobile client can fetch them. They TTL out
on a startup sweep — no DB needed for a hackathon.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from app.config import get_settings

log = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def save(report_id: str, pdf_bytes: bytes) -> Path:
    path = REPORTS_DIR / f"{report_id}.pdf"
    path.write_bytes(pdf_bytes)
    return path


def path_for(report_id: str) -> Path | None:
    path = REPORTS_DIR / f"{report_id}.pdf"
    return path if path.exists() else None


def sweep_expired() -> int:
    """Delete reports older than the TTL. Returns the count removed."""
    ttl_seconds = get_settings().report_ttl_hours * 3600
    now = time.time()
    removed = 0
    for p in REPORTS_DIR.glob("*.pdf"):
        try:
            if now - p.stat().st_mtime > ttl_seconds:
                p.unlink()
                removed += 1
        except OSError:
            continue
    if removed:
        log.info("Swept %d expired report(s)", removed)
    return removed

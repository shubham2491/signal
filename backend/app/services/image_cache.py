"""In-memory image cache.

Holds the normalized image blobs from /analyze so /export-report can
embed them in the PDF without persisting to disk. TTL matches reports.
"""
from __future__ import annotations

import time
from threading import Lock

from app.config import get_settings


_lock = Lock()
_cache: dict[str, tuple[float, list[bytes]]] = {}


def put(report_id: str, images: list[bytes]) -> None:
    with _lock:
        _cache[report_id] = (time.time(), images)


def get(report_id: str) -> list[bytes] | None:
    _sweep()
    with _lock:
        entry = _cache.get(report_id)
        if not entry:
            return None
        return entry[1]


def _sweep() -> None:
    ttl_s = get_settings().report_ttl_hours * 3600
    now = time.time()
    with _lock:
        stale = [k for k, (t, _) in _cache.items() if now - t > ttl_s]
        for k in stale:
            _cache.pop(k, None)

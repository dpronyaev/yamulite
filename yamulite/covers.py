"""Cover-art download and disk cache."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import requests

CACHE_DIR = Path.home() / ".yamulite" / "cache" / "covers"


def _ensure_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cover_url(uri_template: Optional[str], size: str) -> Optional[str]:
    if not uri_template:
        return None
    t = uri_template.replace("%%", size)
    if not t.startswith("http"):
        t = "https://" + t
    return t


def _cache_path(url: str) -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()
    return CACHE_DIR / f"{h}"


def download_cover(uri_template: Optional[str], size: str = "100x100") -> Optional[str]:
    """Download cover to cache; return local file path or None."""
    url = cover_url(uri_template, size)
    if not url:
        return None
    _ensure_dir()
    path = _cache_path(url)
    if path.exists() and path.stat().st_size > 0:
        return str(path)
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (yamulite)"},
        )
        r.raise_for_status()
        if not r.content:
            return None
        path.write_bytes(r.content)
        return str(path)
    except Exception as e:
        print(f"[covers] failed {url}: {e}")
        return None


def cover_uri_for(obj) -> Optional[str]:
    """Best-effort cover-URI extractor for yandex_music objects."""
    uri = getattr(obj, "cover_uri", None)
    if uri:
        return uri
    cover = getattr(obj, "cover", None)
    if cover is not None:
        u = getattr(cover, "uri", None)
        if u:
            return u
        items = getattr(cover, "items_uri", None)
        if items:
            return items[0]
    og = getattr(obj, "og_image", None)
    if og:
        return og
    op = getattr(obj, "op_image", None)
    if op:
        return op
    return None

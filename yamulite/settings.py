"""Persistent user preferences (theme, etc.) stored in ~/.yamulite/settings.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_FILE = Path.home() / ".yamulite" / "settings.json"

MAX_SEARCH_HISTORY = 20

DEFAULTS: dict[str, Any] = {
    "theme": "system",
    "search_history": [],
}


def load() -> dict[str, Any]:
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            data.update(json.loads(SETTINGS_FILE.read_text()))
        except Exception:
            pass
    return data


def save(data: dict[str, Any]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def get(key: str) -> Any:
    return load().get(key, DEFAULTS.get(key))


def set_value(key: str, value: Any) -> None:
    data = load()
    data[key] = value
    save(data)


def get_search_history() -> list[str]:
    hist = load().get("search_history") or []
    return [q for q in hist if isinstance(q, str) and q][:MAX_SEARCH_HISTORY]


def add_search_history(query: str) -> None:
    query = (query or "").strip()
    if not query:
        return
    data = load()
    hist = [q for q in (data.get("search_history") or []) if isinstance(q, str) and q]
    lower = query.lower()
    hist = [q for q in hist if q.lower() != lower]
    hist.insert(0, query)
    data["search_history"] = hist[:MAX_SEARCH_HISTORY]
    save(data)

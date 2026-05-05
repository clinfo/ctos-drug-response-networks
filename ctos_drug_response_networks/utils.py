from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Iterable

from .constants import CANONICAL_DRUGS


def make_run_id() -> str:
    now = datetime.utcnow()
    return now.strftime("RUN-%Y%m%d-%H%M%S")


ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"/(Users|home|mnt|Volumes)/[A-Za-z0-9_.\-/]+"),
    re.compile(r"[A-Za-z]:\\\\[^\s]+"),
]


def canonicalize_drug_name(value: str | None) -> str:
    if value is None:
        return "pretreatment"
    key = str(value).strip()
    if not key:
        return "pretreatment"
    key_low = key.lower()
    return CANONICAL_DRUGS.get(key_low, key)


def safe_slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return cleaned or "item"


def ensure_parent(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_lines(path: str | Path, lines: Iterable[str]) -> None:
    path = ensure_parent(path)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

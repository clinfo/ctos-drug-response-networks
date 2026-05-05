from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch
import json

from .constants import TEXT_FILE_SUFFIXES
from .errors import LeakageError
from .utils import ABSOLUTE_PATH_PATTERNS


IGNORED_PARTS = {
    "config", ".git", "__pycache__", "logs", "outputs", ".venv", "venv", ".tox",
    ".pytest_cache", ".mypy_cache", "dist", "build", "site-packages", ".idea", ".vscode"
}
IGNORED_GLOBS = {"*.egg-info"}


def _is_ignored(path: Path, repo_root: Path) -> bool:
    rel = path.relative_to(repo_root)
    for part in rel.parts:
        if part in IGNORED_PARTS:
            return True
        for pattern in IGNORED_GLOBS:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False


def scan_repo(repo_root: str | Path, forbidden_strings: list[str]) -> dict[str, Any]:
    repo_root = Path(repo_root)
    hits = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if _is_ignored(path, repo_root):
            continue
        if path.suffix not in TEXT_FILE_SUFFIXES and path.name not in {"LICENSE", ".zenodo.json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for forbidden in forbidden_strings:
            if forbidden and forbidden in text:
                hits.append({"path": str(path.relative_to(repo_root)), "type": "forbidden_string", "match": forbidden})
        for pattern in ABSOLUTE_PATH_PATTERNS:
            for m in pattern.finditer(text):
                hits.append({"path": str(path.relative_to(repo_root)), "type": "absolute_path", "match": m.group(0)})
    return {"repo_root": str(repo_root), "hit_count": len(hits), "hits": hits}


def write_leakage_report(report_path: str | Path, report: dict[str, Any]) -> None:
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def fail_if_hits(report: dict[str, Any]) -> None:
    if report["hit_count"]:
        raise LeakageError(f"Public-surface leakage scan found {report['hit_count']} hit(s).")

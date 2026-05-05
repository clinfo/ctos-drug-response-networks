from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import yaml

from .errors import ConfigError

REQUIRED_TOP_LEVEL_KEYS = {"project", "paths", "route", "figures", "validation", "policy"}


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse YAML config: {path}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config must be a mapping.")
    missing = REQUIRED_TOP_LEVEL_KEYS - set(data)
    if missing:
        raise ConfigError(f"Config is missing required keys: {sorted(missing)}")
    return data


def resolve_path(config: dict[str, Any], key: str, base_dir: str | Path | None = None) -> Path:
    value = config["paths"][key]
    if value is None:
        raise ConfigError(f"Config path key is null: {key}")
    path = Path(value)
    if not path.is_absolute():
        if base_dir is None:
            base_dir = Path.cwd()
        path = Path(base_dir) / path
    return path


def dump_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

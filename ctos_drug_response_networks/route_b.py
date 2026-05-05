from __future__ import annotations

from typing import Any

from .errors import UnsupportedRouteError


def describe_route_b(config: dict[str, Any]) -> str:
    mode = config["route"].get("raw_route_mode", "documented-only")
    lines = [
        "Route B is optional and is not the default responsibility of this repository.",
        f"Configured raw-route mode: {mode}",
        "Expected external requirements:",
        "- controlled-access authorization for the raw sequencing dataset",
        "- local installation of Trimmomatic, STAR, RSEM, BWA, SAMtools, Picard, GATK, VEP, and any additional helper tools you choose to use",
        "- user-managed reference resources such as hg38 and the matching annotations",
        "- manual staging of the resulting derived assets into the Route A schema",
        "",
        "This repository ships example wrapper scripts and templates, but it does not promise a complete end-to-end raw rerun.",
    ]
    return "\n".join(lines)


def handle_raw_route(config: dict[str, Any]) -> None:
    mode = config["route"].get("raw_route_mode", "documented-only")
    if mode in {"documented-only", "asset-consume", None}:
        raise UnsupportedRouteError(
            "Raw-route execution is intentionally not implemented in this release. Use `describe-route-b` to inspect the documented boundary."
        )
    raise UnsupportedRouteError("Raw-route execution is not supported in this release.")

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .errors import MissingAssetError, RuntimeExecutionError, UnsupportedRouteError
from .modules.genomics import generate_fig2
from .modules.transcriptomics import generate_fig3
from .modules.networks import generate_fig4, generate_fig5
from .modules.qpcr_score import generate_fig6
from .route_b import handle_raw_route

GENERATOR_MAP = {
    "fig2": generate_fig2,
    "fig3": generate_fig3,
    "fig4": generate_fig4,
    "fig5": generate_fig5,
    "fig6": generate_fig6,
}


def reproduce(config: dict[str, Any], route: str, figures: list[str], outdir: str | Path) -> list[str]:
    if route == "raw":
        handle_raw_route(config)
    outputs: list[str] = []
    outdir = Path(outdir)
    main_out = outdir / "figures/main"
    main_out.mkdir(parents=True, exist_ok=True)
    for fig in figures:
        func = GENERATOR_MAP.get(fig)
        if func is None:
            raise UnsupportedRouteError(f"Unknown figure family: {fig}")
        try:
            outputs.extend(func(config, main_out))
        except MissingAssetError:
            raise
        except Exception as exc:
            raise RuntimeExecutionError(f"Figure generation failed for {fig}: {exc}") from exc
    return outputs

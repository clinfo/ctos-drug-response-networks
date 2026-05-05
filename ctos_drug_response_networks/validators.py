from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd
import json

from .constants import FIGURE_FAMILIES, METADATA_FILES
from .errors import InputSchemaError, MissingAssetError, ReleaseMetadataError

PLACEHOLDER_TOKENS = ["TBD", "TODO", "INSERT", "<", ">"]


REQUIRED_COLUMNS = {
    "sample_map": ["sample_id", "patient_id", "assay", "drug", "timepoint", "replicate", "source_class", "public_asset_path", "notes"],
    "figure_map": ["figure_family", "panel", "module", "primary_inputs", "primary_output", "notes"],
    "network_manifest": ["figure_panel", "drug", "patient_id", "asset_type", "file_name", "description"],
    "drug_sensitivity": ["patient_id", "drug", "viability_ratio", "response_label"],
}


FIGURE_REQUIREMENTS = {
    "fig2": [
        "drug_response/drug_sensitivity_table.tsv",
        "genomics/pathway_mutations.tsv",
        "genomics/pathway_cna.tsv",
    ],
    "fig3": [
        "drug_response/drug_sensitivity_table.tsv",
        "processed_expression/pathway_expression_long.tsv",
        "processed_expression/pathway_logfc_long.tsv",
        "processed_expression/deg_shared.tsv",
    ],
    "fig4": [
        "networks/patient_network_nodes.tsv",
        "networks/patient_network_edges.tsv",
    ],
    "fig5": [
        "networks/common_network_nodes.tsv",
        "networks/common_network_edges.tsv",
        "networks/resistant_missing_edges.tsv",
    ],
    "fig6": [
        "validation/qpcr_long.tsv",
    ],
}


def _check_columns(path: Path, required: list[str]) -> None:
    df = pd.read_csv(path, sep="\t")
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise InputSchemaError(f"{path} is missing required columns: {missing}")


def _check_release_metadata(repo_root: Path) -> list[str]:
    problems: list[str] = []
    for rel in METADATA_FILES:
        path = repo_root / rel
        if not path.exists():
            problems.append(f"Missing release metadata file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(token in text for token in PLACEHOLDER_TOKENS if token not in {"<", ">"}) and rel != "LICENSE":
            problems.append(f"Placeholder token found in {rel}")
    return problems


def validate_assets(config: dict[str, Any], config_path: str | Path | None = None, requested_figures: list[str] | None = None) -> dict[str, Any]:
    repo_root = Path.cwd() if config_path is None else Path(config_path).resolve().parent.parent
    sample_map = repo_root / config["paths"]["sample_map"]
    figure_map = repo_root / config["paths"]["figure_map"]
    network_manifest = repo_root / config["paths"]["network_manifest"]
    if not sample_map.exists():
        raise MissingAssetError(f"Missing sample map: {sample_map}")
    if not figure_map.exists():
        raise MissingAssetError(f"Missing figure-to-script map: {figure_map}")
    if not network_manifest.exists():
        raise MissingAssetError(f"Missing network manifest: {network_manifest}")
    _check_columns(sample_map, REQUIRED_COLUMNS["sample_map"])
    _check_columns(figure_map, REQUIRED_COLUMNS["figure_map"])
    _check_columns(network_manifest, REQUIRED_COLUMNS["network_manifest"])
    requested_figures = requested_figures or config["figures"]["enabled_families"]
    derived_root = repo_root / config["paths"]["derived_root"]
    missing_assets = []
    for fig in requested_figures:
        for rel in FIGURE_REQUIREMENTS.get(fig, []):
            path = derived_root / rel
            if not path.exists():
                missing_assets.append(str(Path(config["paths"]["derived_root"]) / rel))
    ds_path = derived_root / "drug_response/drug_sensitivity_table.tsv"
    if ds_path.exists():
        _check_columns(ds_path, REQUIRED_COLUMNS["drug_sensitivity"])
    metadata_problems = _check_release_metadata(repo_root)
    if metadata_problems:
        raise ReleaseMetadataError("; ".join(metadata_problems))
    if missing_assets:
        raise MissingAssetError("Missing required assets for requested figures: " + ", ".join(sorted(set(missing_assets))))
    return {
        "status": "ok",
        "requested_figures": requested_figures,
        "validated_paths": [str(sample_map), str(figure_map), str(network_manifest)],
    }

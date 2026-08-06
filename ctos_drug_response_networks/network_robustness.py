"""Contract-governed ECv network robustness analyses for the JTM revision.

This module intentionally has no dependency on the release ``load_config``
helper.  Its configuration and output surface are defined by the frozen
network-robustness contract.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from itertools import combinations, permutations
import json
from math import comb
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

import networkx as nx
import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

from .errors import ConfigError, InputSchemaError, MissingAssetError, RuntimeExecutionError, TruthLockError


PROHIBITED_EXTENSIONS = {".pdf", ".png", ".svg", ".xlsx", ".docx", ".md"}
SELECTED_CONDITIONS = ("N", "L", "C")


@dataclass(frozen=True)
class EcvData:
    edges: pd.DataFrame
    column_map: pd.DataFrame
    deltas: dict[str, dict[str, np.ndarray]]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_tsv(frame: pd.DataFrame, path: Path, *, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, float_format="%.12g", compression=compression)


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _as_path(value: str | Path, repo_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def _require(mapping: dict[str, Any], key: str, label: str) -> Any:
    if key not in mapping or mapping[key] is None:
        raise ConfigError(f"Missing required config key: {label}")
    return mapping[key]


def load_network_robustness_config(config_path: str | Path) -> tuple[dict[str, Any], Path]:
    """Load and validate only the dedicated network-robustness YAML schema."""
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Could not parse network robustness config: {path}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("Network robustness config must be a mapping.")
    if raw.get("schema_version") != 1:
        raise ConfigError("schema_version must be 1.")

    paths = _require(raw, "paths", "paths")
    matrix_schema = _require(raw, "matrix_schema", "matrix_schema")
    analysis = _require(raw, "analysis", "analysis")
    cutoffs = _require(raw, "response_cutoffs", "response_cutoffs")
    reference = _require(raw, "reference_reproduction", "reference_reproduction")
    if not all(isinstance(item, dict) for item in (paths, matrix_schema, analysis, cutoffs, reference)):
        raise ConfigError("paths, matrix_schema, analysis, response_cutoffs, and reference_reproduction must be mappings.")

    for key in ("repo_root", "ecv_matrix", "drug_sensitivity_table", "reference_common_edges"):
        _require(paths, key, f"paths.{key}")
    for key in ("source_column", "target_column", "raw_ecv_prefix", "column_regex"):
        _require(matrix_schema, key, f"matrix_schema.{key}")
    for key in ("organoid_lines", "drugs", "thresholds", "baseline_threshold", "threshold_operator"):
        _require(analysis, key, f"analysis.{key}")
    if analysis["threshold_operator"] != "gt":
        raise ConfigError("analysis.threshold_operator must be 'gt'.")
    thresholds = analysis["thresholds"]
    if not isinstance(thresholds, list) or sorted(thresholds) != [0.25, 0.30, 0.35]:
        raise ConfigError("analysis.thresholds must be exactly [0.25, 0.30, 0.35].")
    if float(analysis["baseline_threshold"]) != 0.30:
        raise ConfigError("analysis.baseline_threshold must be 0.30.")
    lines = analysis["organoid_lines"]
    if not isinstance(lines, list) or len(lines) != 10 or len(set(lines)) != 10:
        raise ConfigError("analysis.organoid_lines must contain exactly 10 unique lines.")
    for drug in ("LDN193189", "cetuximab"):
        if drug not in analysis["drugs"] or not isinstance(analysis["drugs"][drug], dict):
            raise ConfigError(f"analysis.drugs.{drug} is required.")
        _require(analysis["drugs"][drug], "condition_code", f"analysis.drugs.{drug}.condition_code")
        if drug not in reference or not isinstance(reference[drug], dict):
            raise ConfigError(f"reference_reproduction.{drug} is required.")
        for key in ("sensitive_lines", "expected_edge_count"):
            _require(reference[drug], key, f"reference_reproduction.{drug}.{key}")
    if float(_require(cutoffs, "high_max_inclusive", "response_cutoffs.high_max_inclusive")) != 0.40:
        raise ConfigError("response_cutoffs.high_max_inclusive must be 0.40.")
    if float(_require(cutoffs, "resistant_min_inclusive", "response_cutoffs.resistant_min_inclusive")) != 0.70:
        raise ConfigError("response_cutoffs.resistant_min_inclusive must be 0.70.")
    try:
        re.compile(str(matrix_schema["column_regex"]))
    except re.error as exc:
        raise ConfigError("matrix_schema.column_regex is invalid.") from exc
    return raw, path


def _resolve_inputs(config: dict[str, Any]) -> dict[str, Path]:
    paths = config["paths"]
    repo_root = _as_path(paths["repo_root"], Path.cwd()).resolve()
    return {
        "repo_root": repo_root,
        "ecv_matrix": _as_path(paths["ecv_matrix"], repo_root),
        "drug_sensitivity_table": _as_path(paths["drug_sensitivity_table"], repo_root),
        "reference_common_edges": _as_path(paths["reference_common_edges"], repo_root),
    }


def _require_files(inputs: dict[str, Path]) -> None:
    for role in ("ecv_matrix", "drug_sensitivity_table", "reference_common_edges"):
        if not inputs[role].is_file():
            raise MissingAssetError(f"Required {role} file not found: {inputs[role]}")


def _parse_ecv_columns(header: list[str], config: dict[str, Any]) -> tuple[pd.DataFrame, dict[tuple[str, str], list[str]]]:
    schema = config["matrix_schema"]
    prefix = str(schema["raw_ecv_prefix"])
    pattern = re.compile(str(schema["column_regex"]))
    lines = set(config["analysis"]["organoid_lines"])
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    seen_tokens: set[tuple[str, str, str]] = set()
    for column in header:
        if not column.startswith(prefix):
            continue
        if column.endswith("_mean") or column.endswith("_delta"):
            rows.append({"raw_column": column, "patient_id": "", "condition_code": "", "replicate_token": "", "selected_for_analysis": False, "parse_status": "excluded_derived"})
            continue
        match = pattern.fullmatch(column)
        if not match:
            rows.append({"raw_column": column, "patient_id": "", "condition_code": "", "replicate_token": "", "selected_for_analysis": False, "parse_status": "unmatched"})
            continue
        patient_id = match.group("line")
        condition = match.group("condition")
        replicate = match.group("replicate")
        token_key = (patient_id, condition, replicate)
        if token_key in seen_tokens:
            raise InputSchemaError(f"Duplicate ECv replicate token: {patient_id}/{condition}/{replicate}")
        seen_tokens.add(token_key)
        selected = patient_id in lines and condition in SELECTED_CONDITIONS
        rows.append({"raw_column": column, "patient_id": patient_id, "condition_code": condition, "replicate_token": replicate, "selected_for_analysis": selected, "parse_status": "ok"})
        if patient_id in lines:
            grouped[(patient_id, condition)].append(column)
    column_map = pd.DataFrame(rows, columns=["raw_column", "patient_id", "condition_code", "replicate_token", "selected_for_analysis", "parse_status"])
    for line in config["analysis"]["organoid_lines"]:
        for condition in SELECTED_CONDITIONS:
            observed = grouped.get((line, condition), [])
            if len(observed) != 3:
                raise InputSchemaError(f"Expected exactly 3 ECv columns for {line}/{condition}; found {len(observed)}.")
    bad = column_map.loc[column_map["parse_status"] == "unmatched", "raw_column"].tolist()
    if bad:
        raise InputSchemaError(f"Unparseable raw ECv column(s): {', '.join(bad[:3])}")
    return column_map, grouped


def _load_ecv_data(config: dict[str, Any], matrix_path: Path, strict: bool) -> EcvData:
    try:
        header = pd.read_csv(matrix_path, sep="\t", nrows=0).columns.tolist()
    except Exception as exc:  # pandas errors need a stable contract class
        raise InputSchemaError(f"Could not read ECv matrix header: {matrix_path.name}") from exc
    schema = config["matrix_schema"]
    source, target = schema["source_column"], schema["target_column"]
    if source not in header or target not in header:
        raise InputSchemaError(f"ECv matrix requires {source} and {target} columns.")
    column_map, grouped = _parse_ecv_columns(header, config)
    usecols = [source, target] + ([schema["edge_name_column"]] if schema.get("edge_name_column") in header else [])
    usecols += column_map.loc[column_map["selected_for_analysis"], "raw_column"].tolist()
    try:
        matrix = pd.read_csv(matrix_path, sep="\t", usecols=usecols)
    except Exception as exc:
        raise InputSchemaError(f"Could not load ECv matrix selected columns: {matrix_path.name}") from exc
    if matrix[source].isna().any() or matrix[target].isna().any():
        raise InputSchemaError("ECv matrix contains missing Parent or Child values.")
    matrix[source] = matrix[source].astype(str)
    matrix[target] = matrix[target].astype(str)
    if matrix.duplicated([source, target]).any():
        raise InputSchemaError("ECv matrix contains duplicate directed edges.")
    edge_name = schema.get("edge_name_column")
    if strict and edge_name in matrix.columns:
        expected = matrix[source] + ":" + matrix[target]
        if (matrix[edge_name].astype(str) != expected).any():
            raise InputSchemaError("ECv matrix name column does not equal Parent:Child in strict mode.")
    matrix = matrix.sort_values([source, target], kind="mergesort").reset_index(drop=True)
    selected = column_map.loc[column_map["selected_for_analysis"], "raw_column"].tolist()
    numeric = matrix[selected].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise InputSchemaError("ECv matrix contains nonfinite selected ECv values.")
    matrix[selected] = numeric
    expected = config.get("expected_input", {})
    if strict and expected.get("edge_rows") is not None and len(matrix) != int(expected["edge_rows"]):
        raise InputSchemaError(f"ECv matrix edge row count is {len(matrix)}, expected {expected['edge_rows']}.")
    if strict and expected.get("raw_ecv_columns_total") is not None:
        observed_raw = int((column_map["parse_status"] == "ok").sum())
        if observed_raw != int(expected["raw_ecv_columns_total"]):
            raise InputSchemaError(f"ECv matrix raw ECv column count is {observed_raw}, expected {expected['raw_ecv_columns_total']}.")
    edges = pd.DataFrame({"source": matrix[source], "target": matrix[target]})
    edges["edge_id"] = edges["source"] + ":" + edges["target"]
    deltas: dict[str, dict[str, np.ndarray]] = {drug: {} for drug in config["analysis"]["drugs"]}
    for drug, drug_config in config["analysis"]["drugs"].items():
        condition = drug_config["condition_code"]
        for line in config["analysis"]["organoid_lines"]:
            baseline = matrix[grouped[(line, "N")]].to_numpy(dtype=float).mean(axis=1)
            treated = matrix[grouped[(line, condition)]].to_numpy(dtype=float).mean(axis=1)
            deltas[drug][line] = np.abs(treated - baseline)
    return EcvData(edges=edges, column_map=column_map, deltas=deltas)


def _canonical_drug(value: Any, config: dict[str, Any]) -> str | None:
    normal = str(value).strip().lower()
    for drug, drug_config in config["analysis"]["drugs"].items():
        aliases = [drug, *drug_config.get("aliases", [])]
        if normal in {str(alias).strip().lower() for alias in aliases}:
            return drug
    return None


def _derive_label(viability: float) -> str:
    if viability <= 0.40:
        return "high_sensitivity"
    if viability < 0.70:
        return "moderate"
    return "resistant"


def _load_response_groups(config: dict[str, Any], table_path: Path, strict: bool) -> pd.DataFrame:
    try:
        table = pd.read_csv(table_path, sep="\t")
    except Exception as exc:
        raise InputSchemaError(f"Could not load drug sensitivity table: {table_path.name}") from exc
    required = {"patient_id", "drug", "viability_ratio", "response_label"}
    if missing := required - set(table.columns):
        raise InputSchemaError(f"Drug sensitivity table missing columns: {sorted(missing)}")
    table = table.copy()
    table["drug"] = table["drug"].map(lambda value: _canonical_drug(value, config))
    table = table.loc[table["drug"].notna()].copy()
    table["patient_id"] = table["patient_id"].astype(str)
    table["viability_ratio"] = pd.to_numeric(table["viability_ratio"], errors="coerce")
    if not np.isfinite(table["viability_ratio"].to_numpy(dtype=float)).all():
        raise InputSchemaError("Drug sensitivity table contains nonfinite viability_ratio.")
    expected = pd.MultiIndex.from_product([list(config["analysis"]["drugs"]), config["analysis"]["organoid_lines"]], names=["drug", "patient_id"])
    observed = table.set_index(["drug", "patient_id"])
    if observed.index.duplicated().any():
        raise InputSchemaError("Drug sensitivity table contains duplicate drug/patient rows.")
    missing = expected.difference(observed.index)
    if len(missing):
        raise InputSchemaError(f"Drug sensitivity table lacks target line/drug rows: {list(missing)[:3]}")
    table = observed.loc[expected].reset_index()
    table["input_response_label"] = table["response_label"].astype(str)
    table["derived_response_label"] = table["viability_ratio"].map(_derive_label)
    table["is_label_match"] = table["input_response_label"] == table["derived_response_label"]
    table["is_canonical_high"] = table["derived_response_label"] == "high_sensitivity"
    table["is_canonical_moderate"] = table["derived_response_label"] == "moderate"
    table["is_canonical_resistant"] = table["derived_response_label"] == "resistant"
    if strict and not table["is_label_match"].all():
        mismatch = table.loc[~table["is_label_match"], ["drug", "patient_id"]].iloc[0].to_dict()
        raise InputSchemaError(f"Input response_label mismatch in strict mode: {mismatch}")
    return table[["drug", "patient_id", "viability_ratio", "input_response_label", "derived_response_label", "is_label_match", "is_canonical_high", "is_canonical_moderate", "is_canonical_resistant"]]


def _read_reference_edges(path: Path, config: dict[str, Any]) -> dict[str, set[tuple[str, str]]]:
    try:
        frame = pd.read_csv(path, sep="\t")
    except Exception as exc:
        raise InputSchemaError(f"Could not load reference common edges: {path.name}") from exc
    required = {"drug", "source", "target"}
    if missing := required - set(frame.columns):
        raise InputSchemaError(f"Reference common edges missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["drug"] = frame["drug"].map(lambda value: _canonical_drug(value, config))
    if frame["drug"].isna().any() or frame.duplicated(["drug", "source", "target"]).any():
        raise InputSchemaError("Reference common edges have unknown drug or duplicate directed edge.")
    return {drug: set(map(tuple, frame.loc[frame["drug"] == drug, ["source", "target"]].astype(str).to_numpy())) for drug in config["analysis"]["drugs"]}


def _common_mask(deltas: dict[str, np.ndarray], lines: Iterable[str], threshold: float) -> np.ndarray:
    selected = [deltas[line] > threshold for line in lines]
    if not selected:
        raise RuntimeExecutionError("A common network requires at least one line.")
    return np.logical_and.reduce(selected)


def _edge_set(edges: pd.DataFrame, mask: np.ndarray) -> set[tuple[str, str]]:
    return set(map(tuple, edges.loc[mask, ["source", "target"]].to_numpy()))


def _network_metrics(edges: pd.DataFrame, mask: np.ndarray) -> tuple[int, int, int, int]:
    selected = edges.loc[mask, ["source", "target"]]
    graph = nx.DiGraph()
    graph.add_edges_from(selected.itertuples(index=False, name=None))
    if graph.number_of_nodes() == 0:
        return 0, 0, 0, 0
    components = list(nx.weakly_connected_components(graph))
    largest = max(components, key=lambda component: (len(component), sorted(component)))
    return graph.number_of_nodes(), len(components), len(largest), graph.subgraph(largest).number_of_edges()


def _jaccard(left: np.ndarray, right: np.ndarray) -> float:
    union = int(np.logical_or(left, right).sum())
    return 1.0 if union == 0 else float(np.logical_and(left, right).sum() / union)


def _truth_lock(ecv: EcvData, config: dict[str, Any], reference: dict[str, set[tuple[str, str]]]) -> tuple[dict[str, np.ndarray], pd.DataFrame, pd.DataFrame]:
    threshold = float(config["analysis"]["baseline_threshold"])
    observed_masks: dict[str, np.ndarray] = {}
    summary_rows: list[dict[str, Any]] = []
    diff_rows: list[dict[str, Any]] = []
    failed = False
    for drug in config["analysis"]["drugs"]:
        legacy_lines = config["reference_reproduction"][drug]["sensitive_lines"]
        observed_mask = _common_mask(ecv.deltas[drug], legacy_lines, threshold)
        observed_masks[drug] = observed_mask
        observed = _edge_set(ecv.edges, observed_mask)
        expected = reference[drug]
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        passed = not missing and not extra and len(expected) == int(config["reference_reproduction"][drug]["expected_edge_count"])
        failed = failed or not passed
        summary_rows.append({"drug": drug, "legacy_reference_lines": ",".join(legacy_lines), "expected_edge_count": len(expected), "observed_edge_count": len(observed), "missing_edge_count": len(missing), "extra_edge_count": len(extra), "status": "passed" if passed else "failed"})
        for kind, edge_list in (("missing_from_observed", missing), ("extra_in_observed", extra)):
            for source, target in edge_list:
                diff_rows.append({"drug": drug, "difference_type": kind, "source": source, "target": target, "edge_id": f"{source}:{target}"})
    summary = pd.DataFrame(summary_rows)
    diff = pd.DataFrame(diff_rows, columns=["drug", "difference_type", "source", "target", "edge_id"])
    if failed:
        raise TruthLockError("Reference truth-lock mismatch; canonical analyses were not run.")
    return observed_masks, summary, diff


def _threshold_analysis(ecv: EcvData, groups: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, np.ndarray]]:
    thresholds = [float(value) for value in config["analysis"]["thresholds"]]
    baseline = float(config["analysis"]["baseline_threshold"])
    summary_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    canonical_masks: dict[str, np.ndarray] = {}
    for drug in config["analysis"]["drugs"]:
        sensitive_lines = groups.loc[(groups["drug"] == drug) & groups["is_canonical_high"], "patient_id"].tolist()
        masks = {threshold: _common_mask(ecv.deltas[drug], sensitive_lines, threshold) for threshold in thresholds}
        baseline_mask = masks[baseline]
        canonical_masks[drug] = baseline_mask
        baseline_nodes = set(ecv.edges.loc[baseline_mask, ["source", "target"]].to_numpy().ravel())
        for threshold in thresholds:
            mask = masks[threshold]
            node_count, component_count, largest_node_count, largest_edge_count = _network_metrics(ecv.edges, mask)
            nodes = set(ecv.edges.loc[mask, ["source", "target"]].to_numpy().ravel())
            retention = 1.0 if int(baseline_mask.sum()) == 0 else float(np.logical_and(mask, baseline_mask).sum() / baseline_mask.sum())
            node_union = len(nodes | baseline_nodes)
            node_jaccard = 1.0 if node_union == 0 else len(nodes & baseline_nodes) / node_union
            summary_rows.append({"drug": drug, "threshold": threshold, "sensitive_lines": ",".join(sensitive_lines), "common_edge_count": int(mask.sum()), "node_count": node_count, "weak_component_count": component_count, "largest_component_node_count": largest_node_count, "largest_component_edge_count": largest_edge_count, "edge_jaccard_vs_baseline": _jaccard(mask, baseline_mask), "node_jaccard_vs_baseline": node_jaccard, "baseline_edge_retention": retention, "is_baseline_threshold": threshold == baseline})
            selected_indices = np.flatnonzero(mask)
            for index in selected_indices:
                row = ecv.edges.iloc[index]
                edge_rows.append({"drug": drug, "threshold": threshold, "source": row.source, "target": row.target, "edge_id": row.edge_id, "in_baseline": bool(baseline_mask[index]), "in_all_thresholds": bool(all(item[index] for item in masks.values()))})
        if not (np.all(masks[0.35] <= masks[0.30]) and np.all(masks[0.30] <= masks[0.25])):
            raise RuntimeExecutionError(f"Threshold nesting violation for {drug}.")
    return pd.DataFrame(summary_rows), pd.DataFrame(edge_rows, columns=["drug", "threshold", "source", "target", "edge_id", "in_baseline", "in_all_thresholds"]), canonical_masks


def _line_support(ecv: EcvData, groups: pd.DataFrame, canonical_masks: dict[str, np.ndarray], config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    threshold = float(config["analysis"]["baseline_threshold"])
    for drug in config["analysis"]["drugs"]:
        mask = canonical_masks[drug]
        edge_count = int(mask.sum())
        for group_row in groups.loc[groups["drug"] == drug].itertuples(index=False):
            values = ecv.deltas[drug][group_row.patient_id][mask]
            dre = values > threshold
            rows.append({"drug": drug, "patient_id": group_row.patient_id, "viability_ratio": group_row.viability_ratio, "response_label": group_row.derived_response_label, "reference_edge_count": edge_count, "mean_delta_ecv": float(values.mean()) if edge_count else np.nan, "median_delta_ecv": float(np.median(values)) if edge_count else np.nan, "dre_count_on_reference": int(dre.sum()), "coverage_fraction": float(dre.mean()) if edge_count else np.nan, "circular_discovery_member": bool(group_row.is_canonical_high)})
            for index in np.flatnonzero(mask):
                edge = ecv.edges.iloc[index]
                support_rows.append({"drug": drug, "patient_id": group_row.patient_id, "source": edge.source, "target": edge.target, "edge_id": edge.edge_id, "delta_ecv": ecv.deltas[drug][group_row.patient_id][index], "is_dre": bool(ecv.deltas[drug][group_row.patient_id][index] > threshold)})
    return pd.DataFrame(rows), pd.DataFrame(support_rows, columns=["drug", "patient_id", "source", "target", "edge_id", "delta_ecv", "is_dre"])


def _exact_group_test(values: np.ndarray, labels: np.ndarray) -> tuple[float, float, float, int]:
    moderate = values[labels == "moderate"]
    resistant = values[labels == "resistant"]
    observed = float(moderate.mean() - resistant.mean())
    n, n_moderate = len(values), len(moderate)
    assignments = []
    for moderate_idx in combinations(range(n), n_moderate):
        selected = np.zeros(n, dtype=bool)
        selected[list(moderate_idx)] = True
        assignments.append(float(values[selected].mean() - values[~selected].mean()))
    distribution = np.asarray(assignments)
    return observed, float((distribution >= observed - 1e-12).mean()), float((np.abs(distribution) >= abs(observed) - 1e-12).mean()), len(assignments)


def _exact_spearman(values: np.ndarray, viability: np.ndarray) -> tuple[float, float, int]:
    rho = float(spearmanr(values, viability).statistic)
    if not np.isfinite(rho):
        return np.nan, np.nan, 0
    distribution = np.asarray([spearmanr(permuted, viability).statistic for permuted in permutations(values)])
    return rho, float((np.abs(distribution) >= abs(rho) - 1e-12).mean()), len(distribution)


def _response_continuum(line_summary: pd.DataFrame, ecv: EcvData, groups: pd.DataFrame, canonical_masks: dict[str, np.ndarray], config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    test_rows: list[dict[str, Any]] = []
    continuum_rows: list[dict[str, Any]] = []
    loso_rows: list[dict[str, Any]] = []
    metrics = ("mean_delta_ecv", "median_delta_ecv", "dre_count_on_reference", "coverage_fraction")
    threshold = float(config["analysis"]["baseline_threshold"])
    for drug in config["analysis"]["drugs"]:
        subset = line_summary.loc[(line_summary["drug"] == drug) & (line_summary["response_label"] != "high_sensitivity")].copy()
        moderate = subset.loc[subset["response_label"] == "moderate"]
        resistant = subset.loc[subset["response_label"] == "resistant"]
        for metric in metrics:
            if len(moderate) and len(resistant) and subset[metric].notna().all():
                observed, one_sided, two_sided, assignments = _exact_group_test(subset[metric].to_numpy(dtype=float), subset["response_label"].to_numpy())
                test_rows.append({"drug": drug, "metric": metric, "n_moderate": len(moderate), "n_resistant": len(resistant), "observed_difference": observed, "alternative": "moderate_greater_than_resistant", "exact_p_one_sided": one_sided, "exact_p_two_sided": two_sided, "n_assignments": assignments})
            else:
                test_rows.append({"drug": drug, "metric": metric, "n_moderate": len(moderate), "n_resistant": len(resistant), "observed_difference": np.nan, "alternative": "moderate_greater_than_resistant", "exact_p_one_sided": np.nan, "exact_p_two_sided": np.nan, "n_assignments": 0})
            values = subset[metric].to_numpy(dtype=float)
            viability = subset["viability_ratio"].to_numpy(dtype=float)
            if len(values) >= 3 and np.isfinite(values).all():
                rho, pvalue, permutations_count = _exact_spearman(values, viability)
                status = "success" if np.isfinite(rho) else "not_estimable"
            else:
                rho, pvalue, permutations_count, status = np.nan, np.nan, 0, "not_estimable"
            continuum_rows.append({"drug": drug, "metric": metric, "n_non_high": len(values), "spearman_rho": rho, "exact_p_two_sided": pvalue, "n_permutations": permutations_count, "status": status})
        high_lines = groups.loc[(groups["drug"] == drug) & groups["is_canonical_high"], "patient_id"].tolist()
        for held_out in high_lines:
            reference_lines = [line for line in high_lines if line != held_out]
            reference_mask = _common_mask(ecv.deltas[drug], reference_lines, threshold)
            values = ecv.deltas[drug][held_out][reference_mask]
            dre = values > threshold
            count = int(reference_mask.sum())
            loso_rows.append({"drug": drug, "held_out_line": held_out, "reference_lines": ",".join(reference_lines), "reference_edge_count": count, "held_out_mean_delta_ecv": float(values.mean()) if count else np.nan, "held_out_median_delta_ecv": float(np.median(values)) if count else np.nan, "held_out_dre_count_on_reference": int(dre.sum()), "held_out_coverage_fraction": float(dre.mean()) if count else np.nan, "status": "success" if count else "not_estimable_empty_reference"})
    return pd.DataFrame(test_rows), pd.DataFrame(continuum_rows), pd.DataFrame(loso_rows)


def _subset_permutation(ecv: EcvData, groups: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    threshold = float(config["analysis"]["baseline_threshold"])
    lines = config["analysis"]["organoid_lines"]
    for drug in config["analysis"]["drugs"]:
        observed_lines = groups.loc[(groups["drug"] == drug) & groups["is_canonical_high"], "patient_id"].tolist()
        subset_size = len(observed_lines)
        rows_for_drug: list[dict[str, Any]] = []
        for ordinal, subset in enumerate(combinations(lines, subset_size), start=1):
            masks = [ecv.deltas[drug][line] > threshold for line in subset]
            common = np.logical_and.reduce(masks)
            union = np.logical_or.reduce(masks)
            individual_counts = [int(mask.sum()) for mask in masks]
            common_count, union_count = int(common.sum()), int(union.sum())
            min_count = min(individual_counts)
            rows_for_drug.append({"drug": drug, "subset_size": subset_size, "subset_id": f"{drug}-{ordinal:03d}", "subset_lines": ",".join(subset), "is_observed_canonical_subset": tuple(subset) == tuple(observed_lines), "common_edge_count": common_count, "union_edge_count": union_count, "multiway_jaccard": (common_count / union_count) if union_count else 1.0, "overlap_coefficient": (common_count / min_count) if min_count else 0.0, "min_individual_dre_count": min_count, "max_individual_dre_count": max(individual_counts)})
        if len(rows_for_drug) != comb(10, subset_size):
            raise RuntimeExecutionError(f"Unexpected subset enumeration count for {drug}.")
        observed = next((row for row in rows_for_drug if row["is_observed_canonical_subset"]), None)
        if observed is None:
            raise RuntimeExecutionError(f"Canonical subset not enumerated for {drug}.")
        observed_count = observed["common_edge_count"]
        counts = np.asarray([row["common_edge_count"] for row in rows_for_drug])
        rank = 1 + int((counts > observed_count).sum())
        ties = int((counts == observed_count).sum())
        primary = float((counts >= observed_count).mean())
        summary_rows.append({"drug": drug, "subset_size": subset_size, "observed_lines": ",".join(observed_lines), "observed_common_edge_count": observed_count, "observed_union_edge_count": observed["union_edge_count"], "observed_multiway_jaccard": observed["multiway_jaccard"], "observed_overlap_coefficient": observed["overlap_coefficient"], "n_subsets": len(rows_for_drug), "rank_min_desc": rank, "tie_count": ties, "percentile": float((counts <= observed_count).mean() * 100), "exact_p_one_sided": primary, "holm_p_primary": np.nan})
        all_rows.extend(rows_for_drug)
    raw_pvalues = sorted(((row["exact_p_one_sided"], index) for index, row in enumerate(summary_rows)), key=lambda item: (item[0], summary_rows[item[1]]["drug"]))
    running = 0.0
    total = len(raw_pvalues)
    for rank, (pvalue, index) in enumerate(raw_pvalues, start=1):
        running = max(running, min(1.0, pvalue * (total - rank + 1)))
        summary_rows[index]["holm_p_primary"] = running
    return pd.DataFrame(all_rows), pd.DataFrame(summary_rows)


def _reference_vs_canonical(ecv: EcvData, groups: pd.DataFrame, truth_masks: dict[str, np.ndarray], canonical_masks: dict[str, np.ndarray], config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, Any]] = []
    edge_rows: list[dict[str, Any]] = []
    for drug in config["analysis"]["drugs"]:
        legacy_lines = config["reference_reproduction"][drug]["sensitive_lines"]
        canonical_lines = groups.loc[(groups["drug"] == drug) & groups["is_canonical_high"], "patient_id"].tolist()
        truth, canonical = truth_masks[drug], canonical_masks[drug]
        summary_rows.append({"drug": drug, "legacy_reference_lines": ",".join(legacy_lines), "canonical_high_lines": ",".join(canonical_lines), "reference_edge_count": int(truth.sum()), "canonical_edge_count": int(canonical.sum()), "overlap_edge_count": int(np.logical_and(truth, canonical).sum())})
        for index in np.flatnonzero(np.logical_or(truth, canonical)):
            edge = ecv.edges.iloc[index]
            edge_rows.append({"drug": drug, "source": edge.source, "target": edge.target, "edge_id": edge.edge_id, "in_legacy_reference": bool(truth[index]), "in_canonical": bool(canonical[index])})
    return pd.DataFrame(summary_rows), pd.DataFrame(edge_rows, columns=["drug", "source", "target", "edge_id", "in_legacy_reference", "in_canonical"])


def _write_delta_output(ecv: EcvData, config: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = True
    for drug in config["analysis"]["drugs"]:
        for line in config["analysis"]["organoid_lines"]:
            frame = ecv.edges.copy()
            frame.insert(0, "patient_id", line)
            frame.insert(0, "drug", drug)
            frame["delta_ecv"] = ecv.deltas[drug][line]
            frame.to_csv(path, sep="\t", index=False, mode="wt" if header else "at", header=header, compression="gzip", float_format="%.12g")
            header = False


def _output_paths(run_dir: Path) -> dict[str, Path]:
    names = [
        "qc/qc_summary.json", "qc/ecv_column_map.tsv", "qc/response_label_audit.tsv", "qc/reference_reproduction_summary.tsv", "qc/reference_edge_diff.tsv",
        "data/delta_ecv_selected_drugs.tsv.gz", "data/canonical_response_groups.tsv", "data/reference_vs_canonical_summary.tsv", "data/reference_vs_canonical_edges.tsv.gz", "data/threshold_summary.tsv", "data/common_edges_by_threshold.tsv.gz", "data/line_support_summary.tsv", "data/sensitive_loso_support.tsv", "data/common_edge_support_long.tsv.gz", "data/response_continuum_summary.tsv", "data/moderate_resistant_exact_tests.tsv", "data/exact_permutation_all_subsets.tsv.gz", "data/exact_permutation_summary.tsv",
        "logs/run_manifest.json", "logs/analysis_summary.json",
    ]
    return {name: run_dir / name for name in names}


def _check_output_extensions(run_dir: Path) -> None:
    bad = sorted(path.name for path in run_dir.rglob("*") if path.is_file() and path.suffix.lower() in PROHIBITED_EXTENSIONS)
    if bad:
        raise RuntimeExecutionError(f"Prohibited runtime output extension(s): {bad}")


def run_network_robustness(config_path: str | Path, outdir: str | Path, run_id: str | None = None, strict: bool = True, overwrite: bool = False) -> dict[str, Any]:
    """Run the frozen-contract network robustness workflow and return its manifest."""
    config, _ = load_network_robustness_config(config_path)
    inputs = _resolve_inputs(config)
    _require_files(inputs)
    run_id = run_id or datetime.now(timezone.utc).strftime("RUN-%Y%m%d-%H%M%S")
    run_dir = Path(outdir) / run_id
    if run_dir.exists():
        if not overwrite:
            raise RuntimeExecutionError(f"Run directory already exists: {run_dir}")
        shutil.rmtree(run_dir)
    paths = _output_paths(run_dir)
    run_dir.mkdir(parents=True)
    for directory in (run_dir / "qc", run_dir / "data", run_dir / "logs"):
        directory.mkdir()
    warnings: list[str] = []
    try:
        ecv = _load_ecv_data(config, inputs["ecv_matrix"], strict)
        _write_tsv(ecv.column_map, paths["qc/ecv_column_map.tsv"])
        groups = _load_response_groups(config, inputs["drug_sensitivity_table"], strict)
        _write_tsv(groups, paths["qc/response_label_audit.tsv"])
        reference = _read_reference_edges(inputs["reference_common_edges"], config)
        try:
            truth_masks, reproduction, difference = _truth_lock(ecv, config, reference)
        except TruthLockError:
            # QC files remain available, but CPATCH-004 prevents all canonical data outputs.
            _, reproduction, difference = _truth_lock_report(ecv, config, reference)
            _write_tsv(reproduction, paths["qc/reference_reproduction_summary.tsv"])
            _write_tsv(difference, paths["qc/reference_edge_diff.tsv"])
            _write_json({"status": "failed", "truth_lock_status": "failed"}, paths["qc/qc_summary.json"])
            raise
        _write_tsv(reproduction, paths["qc/reference_reproduction_summary.tsv"])
        _write_tsv(difference, paths["qc/reference_edge_diff.tsv"])
        _write_tsv(groups, paths["data/canonical_response_groups.tsv"])
        thresholds, common_edges, canonical_masks = _threshold_analysis(ecv, groups, config)
        _write_delta_output(ecv, config, paths["data/delta_ecv_selected_drugs.tsv.gz"])
        _write_tsv(thresholds, paths["data/threshold_summary.tsv"])
        _write_tsv(common_edges, paths["data/common_edges_by_threshold.tsv.gz"], compression="gzip")
        line_summary, support_long = _line_support(ecv, groups, canonical_masks, config)
        _write_tsv(line_summary, paths["data/line_support_summary.tsv"])
        _write_tsv(support_long, paths["data/common_edge_support_long.tsv.gz"], compression="gzip")
        exact_tests, continuum, loso = _response_continuum(line_summary, ecv, groups, canonical_masks, config)
        _write_tsv(exact_tests, paths["data/moderate_resistant_exact_tests.tsv"])
        _write_tsv(continuum, paths["data/response_continuum_summary.tsv"])
        _write_tsv(loso, paths["data/sensitive_loso_support.tsv"])
        subset_all, subset_summary = _subset_permutation(ecv, groups, config)
        _write_tsv(subset_all, paths["data/exact_permutation_all_subsets.tsv.gz"], compression="gzip")
        _write_tsv(subset_summary, paths["data/exact_permutation_summary.tsv"])
        comparison, comparison_edges = _reference_vs_canonical(ecv, groups, truth_masks, canonical_masks, config)
        _write_tsv(comparison, paths["data/reference_vs_canonical_summary.tsv"])
        _write_tsv(comparison_edges, paths["data/reference_vs_canonical_edges.tsv.gz"], compression="gzip")
        for drug, mask in canonical_masks.items():
            if not mask.any():
                warnings.append(f"{drug}: canonical common network is empty; this is a scientific null result.")
        _write_json({"status": "success", "truth_lock_status": "passed", "ecv_rows": len(ecv.edges), "selected_raw_ecv_columns": int(ecv.column_map["selected_for_analysis"].sum()), "scientific_warnings": warnings}, paths["qc/qc_summary.json"])
        # The manifest and analysis summary are themselves required outputs, so
        # the declared list is the contract inventory rather than a pre-write
        # filesystem snapshot.
        relative_outputs = sorted(paths)
        manifest = {"schema_version": 1, "run_id": run_id, "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "strict": bool(strict), "inputs": [{"role": role, "basename": path.name, "size_bytes": path.stat().st_size, "sha256": _sha256(path)} for role, path in inputs.items() if role != "repo_root"], "outputs": relative_outputs}
        summary = {"overall_status": "success", "truth_lock_status": "passed", "analyses": {"threshold_sensitivity": "success", "response_continuum": "success", "exact_subset_permutation": "success"}, "scientific_warnings": warnings, "manuscript_blocker_candidates": [], "not_estimable": [], "output_files": relative_outputs}
        _write_json(manifest, paths["logs/run_manifest.json"])
        _write_json(summary, paths["logs/analysis_summary.json"])
        _check_output_extensions(run_dir)
        return {"status": "success", "run_id": run_id, "run_dir": str(run_dir), "strict": bool(strict), "truth_lock_status": "passed", "analysis_status": summary["analyses"], "outputs": relative_outputs}
    except (ConfigError, MissingAssetError, InputSchemaError, TruthLockError, RuntimeExecutionError):
        raise
    except Exception as exc:
        raise RuntimeExecutionError(f"Network robustness runtime failure: {exc}") from exc


def _truth_lock_report(ecv: EcvData, config: dict[str, Any], reference: dict[str, set[tuple[str, str]]]) -> tuple[dict[str, np.ndarray], pd.DataFrame, pd.DataFrame]:
    """Return truth-lock QC tables without changing the failure semantics."""
    threshold = float(config["analysis"]["baseline_threshold"])
    observed_masks: dict[str, np.ndarray] = {}
    summary_rows: list[dict[str, Any]] = []
    diff_rows: list[dict[str, Any]] = []
    for drug in config["analysis"]["drugs"]:
        legacy_lines = config["reference_reproduction"][drug]["sensitive_lines"]
        mask = _common_mask(ecv.deltas[drug], legacy_lines, threshold)
        observed_masks[drug] = mask
        observed, expected = _edge_set(ecv.edges, mask), reference[drug]
        missing, extra = sorted(expected - observed), sorted(observed - expected)
        passed = not missing and not extra and len(expected) == int(config["reference_reproduction"][drug]["expected_edge_count"])
        summary_rows.append({"drug": drug, "legacy_reference_lines": ",".join(legacy_lines), "expected_edge_count": len(expected), "observed_edge_count": len(observed), "missing_edge_count": len(missing), "extra_edge_count": len(extra), "status": "passed" if passed else "failed"})
        for kind, edge_list in (("missing_from_observed", missing), ("extra_in_observed", extra)):
            diff_rows.extend({"drug": drug, "difference_type": kind, "source": source, "target": target, "edge_id": f"{source}:{target}"} for source, target in edge_list)
    return observed_masks, pd.DataFrame(summary_rows), pd.DataFrame(diff_rows, columns=["drug", "difference_type", "source", "target", "edge_id"])

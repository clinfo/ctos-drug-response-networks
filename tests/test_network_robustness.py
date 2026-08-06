import gzip
import json
from pathlib import Path

import pandas as pd
import pytest

from ctos_drug_response_networks.errors import ConfigError, TruthLockError
from ctos_drug_response_networks.network_robustness import _common_mask, load_network_robustness_config, run_network_robustness


LINES = ["C45", "C132", "C138", "C166", "C307", "C324", "CB3", "KUC3", "KUC17", "KUC21"]


def _write_inputs(tmp_path: Path, *, bad_reference: bool = False) -> Path:
    matrix_rows = []
    for source, target in [("A", "B"), ("B", "A")]:
        row = {"Parent": source, "Child": target, "name": f"{source}:{target}"}
        for line in LINES:
            for condition in ("N", "L", "C"):
                for replicate in range(1, 4):
                    value = 0.0
                    if source == "A" and target == "B":
                        if condition == "L" and line in {"C45", "C307", "CB3"}:
                            value = 0.5
                        if condition == "C" and line in {"C45", "C132", "C324", "KUC3"}:
                            value = 0.5
                    row[f"ECv:{line}_{condition}{replicate}:{len(row)}"] = value
        matrix_rows.append(row)
    pd.DataFrame(matrix_rows).to_csv(tmp_path / "matrix.tsv", sep="\t", index=False)

    response_rows = []
    for drug, high in (("LDN193189", {"C45", "C307", "CB3"}), ("cetuximab", {"C45", "C132", "C324", "KUC3"})):
        for line in LINES:
            viability = 0.3 if line in high else (0.5 if line in {"C166", "C324", "CB3", "KUC3"} else 0.8)
            label = "high_sensitivity" if viability <= 0.4 else ("moderate" if viability < 0.7 else "resistant")
            response_rows.append({"patient_id": line, "drug": drug, "viability_ratio": viability, "response_label": label})
    pd.DataFrame(response_rows).to_csv(tmp_path / "response.tsv", sep="\t", index=False)

    reference_rows = [{"drug": "LDN193189", "source": "A", "target": "B"}, {"drug": "cetuximab", "source": "A", "target": "B"}]
    if bad_reference:
        reference_rows[1]["target"] = "A"
    pd.DataFrame(reference_rows).to_csv(tmp_path / "reference.tsv", sep="\t", index=False)
    config = {
        "schema_version": 1,
        "paths": {"repo_root": str(tmp_path), "ecv_matrix": "matrix.tsv", "drug_sensitivity_table": "response.tsv", "reference_common_edges": "reference.tsv"},
        "matrix_schema": {"source_column": "Parent", "target_column": "Child", "edge_name_column": "name", "raw_ecv_prefix": "ECv:", "column_regex": "^ECv:(?P<line>[^_]+)_(?P<condition>[A-Z])_?(?P<replicate>.*)$"},
        "analysis": {"organoid_lines": LINES, "drugs": {"LDN193189": {"condition_code": "L", "aliases": ["LDN193189"]}, "cetuximab": {"condition_code": "C", "aliases": ["cetuximab"]}}, "thresholds": [0.25, 0.30, 0.35], "baseline_threshold": 0.30, "threshold_operator": "gt"},
        "response_cutoffs": {"high_max_inclusive": 0.40, "resistant_min_inclusive": 0.70},
        "reference_reproduction": {"LDN193189": {"sensitive_lines": ["C45", "C307", "CB3"], "expected_edge_count": 1}, "cetuximab": {"sensitive_lines": ["C45", "C132", "KUC3"], "expected_edge_count": 1}},
    }
    config_path = tmp_path / "network.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def test_network_robustness_full_contract_surface(tmp_path):
    result = run_network_robustness(_write_inputs(tmp_path), tmp_path / "outputs", run_id="RUN-TEST", strict=True)
    run_dir = Path(result["run_dir"])
    assert result["truth_lock_status"] == "passed"
    assert "logs/run_manifest.json" in result["outputs"]
    assert "logs/analysis_summary.json" in result["outputs"]
    manifest = json.loads((run_dir / "logs/run_manifest.json").read_text())
    assert all("/" not in item["basename"] for item in manifest["inputs"])
    groups = pd.read_csv(run_dir / "data/canonical_response_groups.tsv", sep="\t")
    assert groups.loc[(groups.drug == "cetuximab") & groups.is_canonical_high, "patient_id"].tolist() == ["C45", "C132", "C324", "KUC3"]
    with gzip.open(run_dir / "data/exact_permutation_all_subsets.tsv.gz", "rt") as handle:
        permutation = pd.read_csv(handle, sep="\t")
    assert (permutation.drug == "LDN193189").sum() == 120
    assert (permutation.drug == "cetuximab").sum() == 210
    assert all(path.suffix.lower() not in {".pdf", ".png", ".svg", ".xlsx", ".docx", ".md"} for path in run_dir.rglob("*"))


def test_truth_lock_stops_before_canonical_outputs(tmp_path):
    with pytest.raises(TruthLockError):
        run_network_robustness(_write_inputs(tmp_path, bad_reference=True), tmp_path / "outputs", run_id="RUN-BAD", strict=True)
    assert not (tmp_path / "outputs/RUN-BAD/data/canonical_response_groups.tsv").exists()
    assert (tmp_path / "outputs/RUN-BAD/qc/reference_edge_diff.tsv").exists()


def test_threshold_is_strictly_greater_than_boundary():
    mask = _common_mask({"C45": pd.Series([0.30, 0.31]).to_numpy(), "C307": pd.Series([0.30, 0.50]).to_numpy()}, ["C45", "C307"], 0.30)
    assert mask.tolist() == [False, True]


def test_config_requires_ecv_path(tmp_path):
    config = {"schema_version": 1, "paths": {}}
    path = tmp_path / "bad.yaml"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_network_robustness_config(path)


def test_column_order_does_not_change_delta_ecv(tmp_path):
    config = _write_inputs(tmp_path)
    first = run_network_robustness(config, tmp_path / "outputs", run_id="RUN-ONE", strict=True)
    matrix = pd.read_csv(tmp_path / "matrix.tsv", sep="\t")
    fixed = ["Parent", "Child", "name"]
    matrix = matrix[fixed + list(reversed([column for column in matrix.columns if column not in fixed]))]
    matrix.to_csv(tmp_path / "matrix.tsv", sep="\t", index=False)
    second = run_network_robustness(config, tmp_path / "outputs", run_id="RUN-TWO", strict=True)
    with gzip.open(Path(first["run_dir"]) / "data/delta_ecv_selected_drugs.tsv.gz", "rt") as handle:
        left = pd.read_csv(handle, sep="\t")
    with gzip.open(Path(second["run_dir"]) / "data/delta_ecv_selected_drugs.tsv.gz", "rt") as handle:
        right = pd.read_csv(handle, sep="\t")
    pd.testing.assert_frame_equal(left, right)


@pytest.mark.parametrize("kind", ["name", "duplicate", "label"])
def test_strict_input_qc_rejects_contract_violations(tmp_path, kind):
    config = _write_inputs(tmp_path)
    if kind == "name":
        matrix = pd.read_csv(tmp_path / "matrix.tsv", sep="\t")
        matrix.loc[0, "name"] = "not-directed"
        matrix.to_csv(tmp_path / "matrix.tsv", sep="\t", index=False)
    elif kind == "duplicate":
        matrix = pd.read_csv(tmp_path / "matrix.tsv", sep="\t")
        pd.concat([matrix, matrix.iloc[[0]]], ignore_index=True).to_csv(tmp_path / "matrix.tsv", sep="\t", index=False)
    else:
        response = pd.read_csv(tmp_path / "response.tsv", sep="\t")
        response.loc[0, "response_label"] = "resistant"
        response.to_csv(tmp_path / "response.tsv", sep="\t", index=False)
    from ctos_drug_response_networks.errors import InputSchemaError
    with pytest.raises(InputSchemaError):
        run_network_robustness(config, tmp_path / "outputs", run_id=f"RUN-{kind}", strict=True)


def test_threshold_line_support_and_exact_summary_contract(tmp_path):
    result = run_network_robustness(_write_inputs(tmp_path), tmp_path / "outputs", run_id="RUN-METRICS", strict=True)
    run_dir = Path(result["run_dir"])
    threshold = pd.read_csv(run_dir / "data/threshold_summary.tsv", sep="\t")
    ldn = threshold.loc[(threshold.drug == "LDN193189") & (threshold.threshold == 0.30)].iloc[0]
    assert ldn.common_edge_count == 1
    assert ldn.edge_jaccard_vs_baseline == 1.0
    support = pd.read_csv(run_dir / "data/line_support_summary.tsv", sep="\t")
    c45 = support.loc[(support.drug == "LDN193189") & (support.patient_id == "C45")].iloc[0]
    assert c45.dre_count_on_reference == 1 and c45.coverage_fraction == 1.0
    summary = pd.read_csv(run_dir / "data/exact_permutation_summary.tsv", sep="\t")
    assert set(summary.n_subsets) == {120, 210}
    assert summary.rank_min_desc.ge(1).all() and summary.holm_p_primary.between(0, 1).all()


def test_empty_canonical_network_is_a_success_with_warning(tmp_path):
    config = _write_inputs(tmp_path)
    matrix = pd.read_csv(tmp_path / "matrix.tsv", sep="\t")
    for column in matrix.columns:
        if column.startswith("ECv:C324_C"):
            matrix[column] = 0.1
    matrix.to_csv(tmp_path / "matrix.tsv", sep="\t", index=False)
    result = run_network_robustness(config, tmp_path / "outputs", run_id="RUN-NULL", strict=True)
    summary = json.loads((Path(result["run_dir"]) / "logs/analysis_summary.json").read_text())
    assert result["status"] == "success"
    assert any("cetuximab" in warning for warning in summary["scientific_warnings"])

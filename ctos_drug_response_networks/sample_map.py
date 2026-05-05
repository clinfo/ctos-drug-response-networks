from __future__ import annotations

from pathlib import Path
import math
import pandas as pd

from .errors import InputSchemaError
from .utils import canonicalize_drug_name

REQUIRED_COLUMNS = [
    "sample_id",
    "patient_id",
    "experiment",
    "drug",
    "timepoint",
    "replicate",
]


ASSAY_MAP = {
    "wxs": "WES",
    "wes": "WES",
    "rna-seq": "RNAseq",
    "rnaseq": "RNAseq",
}


TIMEPOINT_MAP = {
    "before drug administration": "pre",
    "8 h after drug administration": "8h",
    "48 h after drug administration": "48h",
    "pre": "pre",
    "8h": "8h",
    "48h": "48h",
}


def _normalize_replicate(value: object) -> object:
    if value is None:
        return pd.NA
    try:
        if pd.isna(value):
            return pd.NA
    except Exception:
        pass
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "" or stripped.lower() == "nan":
            return pd.NA
        try:
            numeric = float(stripped)
        except ValueError:
            return stripped
        if math.isfinite(numeric) and numeric.is_integer():
            return int(numeric)
        return stripped
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return int(value)
        return value
    return value


def _normalize_drug(value: object) -> str | pd._libs.missing.NAType:
    try:
        if pd.isna(value):
            return pd.NA
    except Exception:
        pass
    normalized = canonicalize_drug_name(value)
    if normalized in {"", "nan", "NaN", "None"}:
        return pd.NA
    return normalized


def build_sample_map(metadata_path: str | Path) -> pd.DataFrame:
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        raise InputSchemaError(f"Metadata file not found: {metadata_path}")
    df = pd.read_csv(metadata_path, sep="\t")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise InputSchemaError(f"Metadata file is missing required columns: {missing}")

    out = pd.DataFrame()
    out["sample_id"] = df["sample_id"].astype(str)
    out["patient_id"] = df["patient_id"].astype(str)
    out["assay"] = (
        df["experiment"].astype(str).str.lower().map(ASSAY_MAP).fillna(df["experiment"].astype(str))
    )
    out["drug"] = df["drug"].apply(_normalize_drug)
    out["timepoint"] = (
        df["timepoint"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({k.lower(): v for k, v in TIMEPOINT_MAP.items()})
        .fillna(df["timepoint"].astype(str))
    )
    out["replicate"] = df["replicate"].apply(_normalize_replicate)

    wes_mask = out["assay"] == "WES"
    out.loc[wes_mask, "drug"] = "pretreatment"
    out.loc[wes_mask, "timepoint"] = "pre"
    out.loc[wes_mask, "replicate"] = pd.NA

    pretreatment_mask = out["timepoint"] == "pre"
    out.loc[pretreatment_mask & out["drug"].isna(), "drug"] = "pretreatment"

    out["source_class"] = "raw"
    out["public_asset_path"] = pd.NA
    out["notes"] = pd.NA

    if out["sample_id"].duplicated().any():
        raise InputSchemaError("Duplicate sample_id values were found in the generated sample map.")
    return out


def write_sample_map(metadata_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    out = build_sample_map(metadata_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, sep="\t", index=False)
    return out

from pathlib import Path
import pandas as pd
from pandas.testing import assert_frame_equal

from ctos_drug_response_networks.sample_map import build_sample_map


def test_build_sample_map_has_required_columns():
    df = build_sample_map(Path("docs/source_sample_metadata.tsv"))
    required = {"sample_id", "patient_id", "assay", "drug", "timepoint", "replicate", "source_class", "public_asset_path", "notes"}
    assert required.issubset(df.columns)
    assert not df["sample_id"].duplicated().any()


def test_build_sample_map_matches_canonical_release_map():
    generated = build_sample_map(Path("docs/source_sample_metadata.tsv"))
    expected = pd.read_csv(Path("docs/sample_map.tsv"), sep="\t")
    generated = generated.fillna('')
    expected = expected.fillna('')
    assert_frame_equal(generated.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=False)

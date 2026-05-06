# Release inventory

| component | purpose | status | primary files |
|---|---|---|---|
| Python package | CLI, validators, figure builders | included | `ctos_drug_response_networks/` |
| Route A wrappers | reproduction, validation, leakage scan | included | `scripts/*.sh` |
| Route B notes | controlled-access boundary documentation | included | `data_stub/*.md` |
| Canonical sample map | public normalized sample inventory | included | `docs/sample_map.tsv` |
| Figure-to-script map | traceability | included | `docs/figure_to_script_map.tsv` |
| Network manifest | traceability | included | `docs/network_manifest.tsv` |
| Path map | logical asset routing | included | `docs/path_map.tsv` |
| Software versions | reproducibility metadata | included | `docs/software_versions.tsv` |
| Data provenance note | bundled asset governance | included | `docs/data_provenance.md` |
| Panel-support asset manifest | asset-level provenance and fidelity classes | included | `docs/panel_support_asset_manifest.tsv` |
| Drug sensitivity table | exact bundled derived asset | included | `derived_data/drug_response/drug_sensitivity_table.tsv` |
| TMB table | exact bundled derived asset | included | `derived_data/genomics/tmb.tsv` |
| Pathway mutation/CNA summaries | public Route A comparator summaries | included | `derived_data/genomics/pathway_mutations.tsv`; `derived_data/genomics/pathway_cna.tsv` |
| Expression support matrices | public Route A clustering support | included | `derived_data/processed_expression/*.tsv` |
| Common-network and resistant-gap tables | archived edge-set support tables | included | `derived_data/networks/common_network_edges.tsv`; `derived_data/networks/resistant_missing_edges.tsv` |
| Patient-network support tables | public Route A schematic panel support | included | `derived_data/networks/patient_network_nodes.tsv`; `derived_data/networks/patient_network_edges.tsv` |
| Primer list | exact bundled validation asset | included | `derived_data/validation/primer_list.tsv` |
| qPCR long-format matrix | exact bundled validation support asset | included | `derived_data/validation/qpcr_long.tsv` |
| Score coefficients | exact bundled validation asset | included | `derived_data/validation/score_model_*_coefficients.tsv` |
| Score summary | release-safe recomputed validation summary | included | `derived_data/validation/score_summary.tsv` |
| Synthetic smoke fixtures | prove runtime path | included | `tests/fixtures/demo_derived_data/` |

## Notes

- The machine-readable trace lives in `docs/figure_to_script_map.tsv`, `docs/network_manifest.tsv`, and `docs/panel_support_asset_manifest.tsv`.
- Release-boundary decisions and validation status are recorded in `NONCOMPLIANCE_LEDGER.md` and `RELEASE_CHECKLIST.md`.

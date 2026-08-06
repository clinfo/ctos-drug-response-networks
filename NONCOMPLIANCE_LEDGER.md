# Release boundary ledger

This file records release-boundary decisions for the public derived-data repository. Blocking release items have been resolved. Remaining entries describe intentionally conservative data boundaries or external records that are maintained outside this repository.

| id | area | release decision | user impact | status |
|---|---|---|---|---|
| NCL-001 | Public release license | Source code is released under the MIT License. Bundled documentation and figure-used processed or derived data are released under CC BY 4.0 unless otherwise noted. | Reuse rights are explicit in `LICENSE` and `LICENSE-data`. | Resolved |
| NCL-002 | Release metadata | The GitHub URL and existing Zenodo DOI are listed across `README.md`, `CITATION.cff`, `.zenodo.json`, and `config/default.yaml`. No new Zenodo version is created for this revision. | Users can cite `10.5281/zenodo.20043756` as the existing archived release and cite the GitHub commit for this revision. | Resolved |
| NCL-003 | Public release surface | The repository is public at `https://github.com/clinfo/ctos-drug-response-networks`; the existing Zenodo record is retained without an upload, publication, or version change for this revision. | GitHub `main` is the source for this revision, while the existing Zenodo record remains available as an earlier archive. | Resolved |
| NCL-004 | Route A asset fidelity | Several bundled Route A assets are curated panel-support summaries rather than full upstream exports. | Users should not interpret Route A as a raw-to-paper exact rebuild. | Accepted boundary |
| NCL-005 | Cohort-level genomics exports | The repository ships pathway-level public comparator summaries rather than a full released MAF or CNA matrix. | Users cannot reconstruct every cohort-level genomics table from this repository alone. | Accepted boundary |
| NCL-006 | Controlled-access and registry links | Raw sequencing access and foundation-network registry access are described through external controlled-access or registry records. | External records remain the source of truth for raw data and network-registry access. | External-record dependency |
| NCL-007 | Pretreatment expression support matrix | `pathway_expression_long.tsv` is a curated public Route A support asset. | The clustering-family rebuild remains a release-safe schematic path, not a full pretreatment-expression export. | Accepted boundary |

## Bundled asset classes

The repository currently includes:

- exact or recomputed drug-sensitivity, tumor-mutation-burden, qPCR, and selected network support tables
- a canonical sample map generated from sequencing metadata
- pathway-level mutation and copy-number comparator summaries for the public Route A rebuild
- curated expression and patient-network support assets sufficient for schematic figure-family regeneration
- synthetic smoke-test fixtures

These assets are sufficient for the configured validation and smoke-test path. The boundaries above are intentional release decisions, not repository blockers.

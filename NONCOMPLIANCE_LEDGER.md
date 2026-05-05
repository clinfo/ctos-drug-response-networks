# Release boundary ledger

This file records unresolved or intentionally conservative release items. It should stay with the repository until each item is either resolved or explicitly accepted by the project owners.

| id | area | current state | impact | required action |
|---|---|---|---|---|
| NCL-001 | Public release license | the repository still uses a restrictive evaluation-only license file | the repository is not ready for open reuse | replace `LICENSE` with the owner-approved public release license before public publication |
| NCL-002 | Release metadata | reserved Zenodo new-version DOI and GitHub URL are now recorded in repository metadata | citation metadata can still drift if manuscript-side wording is not updated | sync manuscript availability wording, Key Resources Table, and submission-form entries with `10.5281/zenodo.20042701` |
| NCL-003 | Availability statement sync | repository, controlled-access record, network registry record, and manuscript wording still need a final cross-check | release links or access wording may become stale | lock the final data/code availability wording on the release day |
| NCL-004 | Route A asset fidelity | several bundled Route A assets are curated panel-support summaries rather than full upstream exports | users should not interpret Route A as a raw-to-paper exact rebuild | keep `docs/panel_support_asset_manifest.tsv` and `docs/data_provenance.md` with the release |
| NCL-005 | Cohort-level genomics exports | the repository ships pathway-level public comparator summaries rather than a full released MAF or CNA matrix | users cannot reconstruct every cohort-level genomics table from this repository alone | keep the controlled-access and manuscript-level boundary explicit in Route B docs |
| NCL-006 | Controlled-access and registry links | the EGA and NDEx records are staged but require release-day confirmation | stale registry links would reduce release trust | re-check the access records before public publication |
| NCL-007 | Pretreatment expression support matrix | `pathway_expression_long.tsv` is a curated public Route A support asset | the clustering-family rebuild remains a release-safe schematic path, not a full pretreatment-expression export | retain the provenance note in `docs/panel_support_asset_manifest.tsv` and `docs/data_provenance.md` |

## Bundled asset classes

The repository currently includes:

- exact or recomputed drug-sensitivity, tumor-mutation-burden, qPCR, score, and selected network support tables
- a canonical sample map generated from sequencing metadata
- pathway-level mutation and copy-number comparator summaries for the public Route A rebuild
- curated expression and patient-network support assets sufficient for schematic figure-family regeneration
- synthetic smoke-test fixtures

These assets are sufficient for the configured validation and smoke-test path. They do not remove the release-day checks above.

# Data provenance

## Bundled Route A assets

The repository includes derived assets for the public Route A rebuild. Some assets are exact archived extractions or exact recomputations; others are curated support summaries included only to support the public figure-facing route.

### Exact archived extractions or exact recomputations

- normalized drug sensitivity values
- the canonical sample map generated from the sequencing metadata table
- tumor mutation burden values
- primer sequences from the validation primer workbook
- LDN193189 and cetuximab support-panel logFC tables reconstructed from archived notebook outputs
- a release-safe pretreatment expression support matrix for the same public Route A panel universe; this is shipped as a curated support asset rather than claimed as a full upstream export
- the 36-gene shared LDN193189 DEG panel with exact mean logFC values reconstructed from the publication-support figure table
- qPCR long-format tables reconstructed from archived notebook outputs
- LDN193189 and cetuximab common sensitivity edge sets reconstructed from archived notebook outputs
- resistant missing-edge tables reconstructed from archived notebook outputs
- integrated score summaries recomputed from the released logistic coefficients and the bundled qPCR long-format matrix

### Curated public Route A panel-support summaries

- pathway-level mutation and CNA comparator summaries aligned to the described figure examples
- patient-network node and edge tables ordered to regenerate public-safe schematic LDN193189 network panels
- node-color support values that use exact sample-level values where available and panel means as conservative fallbacks where direct per-sample release tables were not present

## What is not redistributed here

This repository does **not** redistribute:

- controlled-access human WES FASTQ files
- controlled-access human RNA-seq FASTQ files
- a full released MAF export
- a full released cohort-wide CNA matrix
- private upstream notebook working directories

## Governance note

The release separates three things:

1. bundled release-safe assets that are sufficient for the public Route A figure-family rebuild
2. controlled-access or request-only assets that are documented but not redistributed
3. synthetic smoke-test fixtures used only to verify runtime behavior

Asset-level provenance and fidelity classes are enumerated in `docs/panel_support_asset_manifest.tsv`.

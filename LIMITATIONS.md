# Limitations

This repository is a public release package for the derived-data reproduction route.

## What this release supports

- Validation of the bundled Route A assets.
- Rebuilding supported figure families from processed or derived release assets.
- Documentation of the controlled-access raw-data boundary.
- Smoke tests for the public code path.

## What this release does not support

- Redistribution of raw human whole-exome or RNA-seq files.
- A one-command end-to-end raw FASTQ-to-figure workflow.
- A complete released MAF export or cohort-wide CNA matrix.
- Redistribution of private upstream notebook workspaces.
- A claim that the public Route A outputs are exact journal-production artwork.

## Interpretation

The bundled Route A assets are intended to support transparent review of the
public figure-facing route. Asset-level provenance and fidelity classes are
recorded in `docs/panel_support_asset_manifest.tsv` and
`docs/data_provenance.md`.

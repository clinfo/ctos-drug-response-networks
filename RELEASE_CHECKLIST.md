# Release checklist

This checklist records the public release state for the GitHub and Zenodo derived-data archive. It is retained as a release validation record, not as a remaining action list.

## Local preflight

- [x] Confirm the repository name and GitHub destination: `https://github.com/clinfo/ctos-drug-response-networks`.
- [x] Confirm that `LICENSE` has the final public release software license: MIT.
- [x] Confirm that bundled documentation and figure-used processed or derived data are covered by `LICENSE-data`: CC BY 4.0 unless otherwise noted.
- [x] Confirm that no raw human sequencing files, private notebooks, local paths, credentials, or internal work logs are intentionally included.
- [x] Confirm that `.gitignore` excludes local environments, generated outputs, caches, and macOS metadata.
- [x] Build the public release archive from a clean Git HEAD.
- [x] Confirm that no file larger than the chosen GitHub release threshold is included unintentionally.
- [x] Run the public leakage scan and confirm zero hits.

## Reproducibility checks

- [x] Run `ctos-repro validate-assets --config config/default.yaml`.
- [x] Run `ctos-repro reproduce --route derived --figure all --config config/default.yaml --outdir outputs/`.
- [x] Run `pytest -q`.
- [x] Confirm that `docs/generated/sample_map_from_source.tsv` matches the intended public sample map.
- [x] Review `docs/panel_support_asset_manifest.tsv` and `docs/data_provenance.md`.

## Access and citation checks

- [x] Keep raw sequencing files outside this repository and describe controlled-access handling in `data_stub/ega_access_instructions.md`.
- [x] Keep foundation-network registry handling outside this repository and describe access in `data_stub/ndex_access_instructions.md`.
- [x] Reserve the Zenodo new-version DOI: `10.5281/zenodo.20043756`.
- [x] Update `README.md`, `CITATION.cff`, `.zenodo.json`, and `config/default.yaml` with the reserved DOI and release URL.
- [x] Align repository metadata with the manuscript-facing GitHub and Zenodo availability wording.

## GitHub and Zenodo workflow

- [x] Initialize a fresh public-release Git history after local preflight.
- [x] Push the release commits to `clinfo/ctos-drug-response-networks`.
- [x] Check the GitHub file browser, README rendering, license display, and release-surface files.
- [x] Prepare the Zenodo archive from the DOI-synchronized Git HEAD.
- [x] Confirm that the GitHub repository is public.

## Future extensions

The following items are not blockers for this public release:

- archived reference figures for visual diffing against Route A outputs
- a richer release note that cross-links the controlled-access record, network registry record, manuscript DOI, GitHub release URL, and Zenodo archive after manuscript acceptance
- a container recipe if future reuse requires stricter environment pinning

# ctos-drug-response-networks

A public release repository for reproducing derived, figure-facing analyses from colorectal cancer organoid drug-response and resistance data.

Repository URL: `https://github.com/clinfo/ctos-drug-response-networks`

Archived release DOI: `10.5281/zenodo.20043756`

Previous archived release DOI: `10.5281/zenodo.19645738`

## Scope

This repository supports a derived-data release path. It validates bundled release assets, rebuilds the supported figure families, and documents the boundary between public derived assets and controlled-access sequencing data.

It does not redistribute raw human sequencing files, private notebook workspaces, or a one-command raw FASTQ-to-figure workflow.

## Execution routes

- Route A is the default public route. It uses bundled processed or derived assets to rebuild the supported figure families.
- Route B documents the controlled-access raw-data route. It records expected inputs and processing steps, but the raw files are not shipped here.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Validate the bundled assets:

```bash
ctos-repro validate-assets --config config/default.yaml
```

Rebuild all supported figure families:

```bash
ctos-repro reproduce --route derived --figure all --config config/default.yaml --outdir outputs/
```

Run the public-surface leakage scan:

```bash
ctos-repro scan-leakage --repo-root ./
```

Rebuild the canonical sample map:

```bash
ctos-repro build-sample-map --metadata docs/source_sample_metadata.tsv --out docs/generated/sample_map_from_source.tsv
```

Show the Route B boundary:

```bash
ctos-repro describe-route-b --config config/default.yaml
```

## Tests

```bash
python -m pip install -r env/requirements.txt
pytest -q
```

The tests check schemas, smoke-test fixtures, route boundaries, and the public leakage scanner. They are not intended to make scientific claims beyond runtime and release-surface integrity.

## Repository layout

```text
ctos-drug-response-networks/
  ctos_drug_response_networks/   Python package and CLI
  config/                        release and fixture configuration
  data_stub/                     controlled-access instructions and schema templates
  derived_data/                  bundled Route A release assets
  docs/                          provenance, manifests, sample maps, and software versions
  env/                           Python dependency list
  figures/                       default output location for regenerated figures
  scripts/                       wrapper scripts and optional helpers
  tests/                         smoke and schema tests
```

## Bundled Route A assets

The release bundle includes:

- normalized drug-sensitivity tables
- tumor mutation burden summaries
- pathway-level mutation and copy-number comparator summaries
- expression, differential-expression, network, qPCR, and score-support tables
- a canonical sample map regenerated from sequencing metadata
- synthetic fixture data for smoke testing

Asset-level provenance and fidelity classes are recorded in `docs/panel_support_asset_manifest.tsv`. The broader data boundary is summarized in `docs/data_provenance.md`.

## Data access

Raw whole-exome and RNA-seq files are not redistributed in this repository. The controlled-access route is described in `data_stub/ega_access_instructions.md`.

The foundation network registry record is described in `data_stub/ndex_access_instructions.md`.

Bundled derived assets should be interpreted as release assets for the public Route A rebuild, not as a complete redistribution of the upstream cohort data.

## Release status

This repository is the public derived-data release for the accompanying manuscript. The release archive DOI is `10.5281/zenodo.20043756`.

Release-surface validation and accepted data-boundary limitations are summarized in `RELEASE_CHECKLIST.md` and `NONCOMPLIANCE_LEDGER.md`.

## Citation

If you use this repository, cite the accompanying manuscript and the archived software release:

Ota, K., and Sakuragi, M. (2026). ctos-drug-response-networks: derived-data release for colorectal cancer organoid drug-response and resistance analyses. Zenodo. https://doi.org/10.5281/zenodo.20043756

## License

Source code in this repository is released under the MIT License. Bundled documentation and figure-used processed or derived data are released under CC BY 4.0 unless otherwise noted.

See `LICENSE` for the software license and `LICENSE-data` for the bundled documentation and data license.

## Notes

See `docs/data_provenance.md` for asset provenance details and `LIMITATIONS.md` for the scope and limitations of the bundled release.

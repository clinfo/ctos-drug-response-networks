# Release checklist

## Local preflight

- [ ] Confirm the repository name and GitHub destination.
- [ ] Confirm that `LICENSE` has the final owner-approved public release license.
- [ ] Confirm that no raw human sequencing files, private notebooks, local paths, credentials, or internal work logs are included.
- [ ] Confirm that `.gitignore` excludes local environments, generated outputs, caches, and macOS metadata.
- [ ] Build any public release archive from a clean Git tree or GitHub release archive, not from the local working directory.
- [ ] Confirm that no file larger than the chosen GitHub release threshold is included unintentionally.
- [ ] Run the public leakage scan and confirm zero hits.

## Reproducibility checks

- [ ] Run `ctos-repro validate-assets --config config/default.yaml`.
- [ ] Run `ctos-repro reproduce --route derived --figure all --config config/default.yaml --outdir outputs/`.
- [ ] Run `pytest -q`.
- [ ] Confirm that `docs/generated/sample_map_from_source.tsv` matches the intended public sample map.
- [ ] Review `docs/panel_support_asset_manifest.tsv` and `docs/data_provenance.md`.

## Access and citation checks

- [ ] Confirm the controlled-access sequencing accession and wording on the release day.
- [ ] Confirm the foundation-network registry record on the release day.
- [x] Reserve the Zenodo new-version DOI: `10.5281/zenodo.20042701`.
- [x] Update `README.md`, `CITATION.cff`, `.zenodo.json`, and `config/default.yaml` with the reserved DOI and release URL.
- [ ] Update the manuscript availability statements with the final DOI and release URL.
- [ ] Re-check that manuscript data/code availability wording matches the repository, EGA record, NDEx record, GitHub release, and Zenodo archive.

## GitHub and Zenodo workflow

- [ ] Initialize a fresh public-release Git history only after local preflight is clean.
- [ ] Create the GitHub repository as private first.
- [ ] Push the initial release commit to the private repository.
- [ ] Check the GitHub file browser, README rendering, license display, and release-surface files.
- [ ] Publish the Zenodo record only after the final release archive and metadata are aligned.
- [ ] Make the GitHub repository public only after GitHub and Zenodo checks pass.

## Optional hardening

- [ ] Add archived reference figures for visual diffing against the Route A outputs.
- [ ] Add a richer release note that cross-links the controlled-access record, network registry record, manuscript DOI, GitHub release URL, and Zenodo archive.
- [ ] Add a container recipe after the final license and archive metadata are fixed.

# Pipeline overview

## Route A (default)

1. Load normalized derived assets.
2. Validate schemas and release metadata.
3. Regenerate figure families:
   - `fig2`: genomic comparator summaries
   - `fig3`: expression-only clustering and shared DEGs
   - `fig4`: patient-specific network rewiring views
   - `fig5`: common sensitivity networks and resistant missing-edge maps
   - `fig6`: qPCR follow-up and optional score summary
4. Emit run manifests and validation reports.
5. Run the public-surface leakage scan.

## Route B (optional)

The raw-data route remains documented-only in this first implementation.

Historically, the RNA-seq path was:

`FASTQ -> Trimmomatic -> STAR -> RSEM -> counts / TPM`

Historically, the WES helper path included:

`BWA -> SAMtools -> Picard -> GATK / Mutect2 -> annotation -> downstream summary tables`

The historical network path was:

`filtered TPM matrix -> Bayesian-network estimation -> ECv -> ΔECv -> DRE -> patient-specific subnetworks`

## Design notes

- The default public responsibility is the derived-data route.
- The foundation network is treated as a public input asset rather than a default rerun target.
- The score module remains secondary to the qPCR follow-up outputs.

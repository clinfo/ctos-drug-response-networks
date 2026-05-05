#!/usr/bin/env bash
set -euo pipefail

RSEM_PREPARE_REFERENCE="${RSEM_PREPARE_REFERENCE:?set RSEM_PREPARE_REFERENCE to rsem-prepare-reference}"
REF_FASTA="${REF_FASTA:?set REF_FASTA to the hg38 fasta path}"
REF_GTF="${REF_GTF:?set REF_GTF to the matching GTF path}"
RSEM_REF_PREFIX="${RSEM_REF_PREFIX:?set RSEM_REF_PREFIX to the output prefix}"
THREADS="${THREADS:-10}"

"$RSEM_PREPARE_REFERENCE" --gtf "$REF_GTF" --p "$THREADS" "$REF_FASTA" "$RSEM_REF_PREFIX"

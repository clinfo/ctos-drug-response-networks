#!/usr/bin/env bash
set -euo pipefail

RSEM_CALCULATE_EXPRESSION="${RSEM_CALCULATE_EXPRESSION:?set RSEM_CALCULATE_EXPRESSION to rsem-calculate-expression}"
ALIGNMENT_BAM="${1:?Aligned.toTranscriptome.out.bam required}"
RSEM_REF_PREFIX="${2:?reference prefix required}"
OUTPUT_PREFIX="${3:?output prefix required}"
THREADS="${THREADS:-10}"

"$RSEM_CALCULATE_EXPRESSION" \
  --alignments \
  --paired-end \
  -p "$THREADS" \
  --strandedness reverse \
  --append-names \
  --estimate-rspd \
  "$ALIGNMENT_BAM" \
  "$RSEM_REF_PREFIX" \
  "$OUTPUT_PREFIX"

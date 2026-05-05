#!/usr/bin/env bash
set -euo pipefail

STAR_BIN="${STAR_BIN:?set STAR_BIN to the STAR executable}"
STAR_INDEX_DIR="${STAR_INDEX_DIR:?set STAR_INDEX_DIR to the STAR index directory}"
READ1="${1:?paired read1 required}"
READ2="${2:?paired read2 required}"
OUT_PREFIX="${3:?output prefix required}"
THREADS="${THREADS:-10}"

"$STAR_BIN" \
  --genomeDir "$STAR_INDEX_DIR" \
  --runThreadN "$THREADS" \
  --outFileNamePrefix "$OUT_PREFIX" \
  --quantMode TranscriptomeSAM \
  --outSAMtype BAM SortedByCoordinate \
  --readFilesIn "$READ1" "$READ2"

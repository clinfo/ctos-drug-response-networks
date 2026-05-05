#!/usr/bin/env bash
set -euo pipefail

STAR_BIN="${STAR_BIN:?set STAR_BIN to the STAR executable}"
REF_FASTA="${REF_FASTA:?set REF_FASTA to the hg38 fasta path}"
REF_GTF="${REF_GTF:?set REF_GTF to the matching GTF path}"
STAR_INDEX_DIR="${STAR_INDEX_DIR:?set STAR_INDEX_DIR to the desired index directory}"
THREADS="${THREADS:-10}"
SJDB_OVERHANG="${SJDB_OVERHANG:-99}"

mkdir -p "$STAR_INDEX_DIR"
"$STAR_BIN" --runMode genomeGenerate \
  --genomeDir "$STAR_INDEX_DIR" \
  --runThreadN "$THREADS" \
  --sjdbOverhang "$SJDB_OVERHANG" \
  --genomeFastaFiles "$REF_FASTA" \
  --sjdbGTFfile "$REF_GTF"

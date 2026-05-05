#!/usr/bin/env bash
set -euo pipefail

READ1="${1:?read1 fastq required}"
READ2="${2:?read2 fastq required}"
OUTDIR="${3:?output directory required}"
HEAP="${4:-4G}"
TRIMMOMATIC_JAR="${TRIMMOMATIC_JAR:?set TRIMMOMATIC_JAR to the trimmomatic jar path}"

mkdir -p "$OUTDIR"
java -Xmx"$HEAP" -jar "$TRIMMOMATIC_JAR" \
  PE -phred33 \
  -trimlog "$OUTDIR/trimmomatic.log" \
  "$READ1" "$READ2" \
  "$OUTDIR/paired_output_1.fq" "$OUTDIR/unpaired_output_1.fq" \
  "$OUTDIR/paired_output_2.fq" "$OUTDIR/unpaired_output_2.fq" \
  ILLUMINACLIP:adapters/TruSeq3-PE-2.fa:2:30:10 \
  LEADING:20 TRAILING:20 SLIDINGWINDOW:4:15 MINLEN:36

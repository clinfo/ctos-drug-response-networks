#!/usr/bin/env bash
set -euo pipefail

GATK_BIN="${GATK_BIN:?set GATK_BIN to the gatk executable}"
INPUT="${1:?feature file required}"
"$GATK_BIN" IndexFeatureFile -I "$INPUT"

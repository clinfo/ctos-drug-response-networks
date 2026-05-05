#!/usr/bin/env bash
set -euo pipefail
python -m ctos_drug_response_networks.cli scan-leakage "$@"

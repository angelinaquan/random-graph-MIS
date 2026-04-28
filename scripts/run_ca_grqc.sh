#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f data/ca-GrQc.txt.gz ]]; then
  scripts/download_ca_grqc.sh
fi

PYTHONPATH=src python3 -m mis_project.experiments snap \
  data/ca-GrQc.txt.gz \
  --greedy-repeats 100 \
  --time-limit 300 \
  --output results/ca_grqc_results.csv

PYTHONPATH=src python3 -m mis_project.plots snap \
  results/ca_grqc_results.csv \
  --output figures/ca_grqc_comparison.png

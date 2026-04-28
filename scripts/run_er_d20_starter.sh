#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m mis_project.experiments er \
  --d 20 \
  --n-values 100 200 \
  --seeds 0 1 2 \
  --greedy-repeats 50 \
  --time-limit 30 \
  --output results/er_d20_starter_results.csv

PYTHONPATH=src python3 -m mis_project.plots er \
  results/er_d20_starter_results.csv \
  --output figures/er_d20_starter_fraction.png

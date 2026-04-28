#!/usr/bin/env bash
set -euo pipefail

mkdir -p data
curl -L -o data/ca-GrQc.txt.gz https://snap.stanford.edu/data/ca-GrQc.txt.gz

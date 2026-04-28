# Maximum Independent Set Project

This repository compares greedy and integer-programming approaches for maximum independent set on Erdos-Renyi graphs `G(n, d/n)` and on one SNAP real network.

## Mathematical Formulation

For a graph `G = (V, E)`, use binary variables `x_i`, where `x_i = 1` means
vertex `i` is in the independent set:

```text
maximize    sum_i x_i
subject to  x_u + x_v <= 1      for every edge (u, v) in E
            x_i in {0, 1}       for every vertex i in V
```

For `G(n, d/n)`, the project compares the algorithmic and theoretical scales:

```text
greedy scale:   (log d / d) n
optimum scale:  (2 log d / d) n
```

For `d = 20`, these are approximately `0.1498n` and `0.2996n`.

## Run ER Experiments

Use the local source tree directly:

```bash
PYTHONPATH=src python3 -m mis_project.experiments er \
  --d 20 \
  --n-values 100 200 500 1000 \
  --seeds 0 1 2 \
  --greedy-repeats 100 \
  --time-limit 120 \
  --output results/er_results.csv
```

For a quick run without IP:

```bash
PYTHONPATH=src python3 -m mis_project.experiments er \
  --d 20 --n-values 100 200 500 --skip-ip
```

## Run SNAP Experiment

Download one SNAP edge list, for example `ca-GrQc.txt.gz` or `facebook_combined.txt.gz`,
into `data/`. Then run:

```bash
PYTHONPATH=src python3 -m mis_project.experiments snap \
  data/ca-GrQc.txt.gz \
  --greedy-repeats 200 \
  --time-limit 600 \
  --output results/snap_results.csv
```

SNAP dataset index: <https://snap.stanford.edu/data/index.html>

Good first choices:

- `ca-GrQc`: 5,242 nodes and 14,496 edges, undirected collaboration network.
- `ego-Facebook`: 4,039 nodes and 88,234 edges, undirected Facebook ego network.

## Make Plots

```bash
PYTHONPATH=src python3 -m mis_project.plots er \
  results/er_results.csv \
  --output figures/er_fraction.png

PYTHONPATH=src python3 -m mis_project.plots snap \
  results/snap_results.csv \
  --output figures/snap_comparison.png
```

## Suggested Experiment Grid

Start small enough to verify everything:

```text
d = 20
n = 100, 200, 500
seeds = 0, 1, 2
time limit = 60 seconds
```

Then scale up:

```text
n = 1000, 2000, 5000
time limit = 300 to 900 seconds
```

For large `n`, the IP may return a strong incumbent without proving optimality.
That still answers part of the project: compare the incumbent against the
greedy threshold and record the solver gap/status.

## Output Columns

The experiment CSVs include:

- graph statistics: `n`, `m`, `avg_degree`, components, density
- theory columns: `theory_greedy`, `theory_optimum`
- greedy result: size, runtime, status
- IP result: incumbent size, runtime, status, best bound, MIP gap

## Report

Use `report_template.md` as the writeup scaffold. Fill in tables from
`results/*.csv` and plots from `figures/*.png`.

# Maximum Independent Set: Computational Project

## 1. Problem

We study maximum independent set on Erdos-Renyi graphs `G(n, d/n)` with fixed
`d`, and on one real network from the Stanford SNAP collection.

The integer-programming formulation is:

```text
maximize    sum_i x_i
subject to  x_u + x_v <= 1      for every edge (u, v)
            x_i in {0, 1}
```

## 2. Algorithms

### Greedy

The greedy baseline repeatedly scans vertices in random order and adds a vertex
if none of its neighbors has already been chosen. We run many random orders and
keep the best solution. The implementation also tests a minimum-degree greedy
variant and keeps the better result.

### Integer Programming

The IP model uses one binary variable per vertex and one constraint per edge.
The solver is SciPy's MILP interface to HiGHS, with a fixed time limit. We record
the incumbent, solver status, best bound, and MIP gap.

## 3. Erdos-Renyi Experiments

Parameters:

```text
d = 20
n values =
seeds =
IP time limit =
greedy repeats =
```

For `d = 20`,

```text
(log d / d)n    ≈ 0.1498n
(2 log d / d)n  ≈ 0.2996n
```

Table:

```text
Paste or summarize results/er_results.csv here.
```

Figure:

```text
figures/er_fraction.png
```

Discussion:

- Does IP find solutions above the greedy threshold?
- For which `n` does IP prove optimality?
- How does the MIP gap change as `n` grows?
- Are observed optima close to `(2 log d / d)n`?

## 4. SNAP Experiment

Dataset:

```text
Name =
n =
m =
average degree =
components =
```

Table:

```text
Paste or summarize results/snap_results.csv here.
```

Figure:

```text
figures/snap_comparison.png
```

Discussion:

- Can IP find or prove the optimum?
- How does greedy compare with IP?
- Is the ER prediction based on average degree accurate for this network?
- What real-network structure might explain deviations?

## 5. Conclusion

Summarize the computational findings:

- IP vs greedy on random graphs.
- Solver scalability as `n` grows.
- Performance on the real SNAP network.
- Whether the theoretical ER predictions are useful for the observed graphs.

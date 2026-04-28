"""Greedy and integer-programming solvers for maximum independent set."""

from __future__ import annotations

import itertools
import random
import time
from dataclasses import dataclass
from typing import Hashable, Iterable, Sequence

import networkx as nx

from .graph_io import relabel_consecutive


@dataclass
class IndependentSetResult:
    method: str
    size: int
    vertices: list[Hashable]
    status: str
    runtime_seconds: float
    objective_bound: float | None = None
    mip_gap: float | None = None
    message: str = ""


def is_independent_set(graph: nx.Graph, vertices: Iterable[Hashable]) -> bool:
    selected = set(vertices)
    return all(not (u in selected and v in selected) for u, v in graph.edges())


def greedy_random_order(graph: nx.Graph, seed: int | None = None) -> IndependentSetResult:
    """One pass greedy algorithm using a random vertex order."""
    start = time.perf_counter()
    rng = random.Random(seed)
    order = list(graph.nodes())
    rng.shuffle(order)

    selected = []
    forbidden = set()
    for vertex in order:
        if vertex not in forbidden:
            selected.append(vertex)
            forbidden.update(graph.neighbors(vertex))

    return IndependentSetResult(
        method="greedy_random_order",
        size=len(selected),
        vertices=selected,
        status="feasible",
        runtime_seconds=time.perf_counter() - start,
    )


def greedy_min_degree(graph: nx.Graph, seed: int | None = None) -> IndependentSetResult:
    """Greedy heuristic that repeatedly picks a current minimum-degree vertex."""
    start = time.perf_counter()
    rng = random.Random(seed)
    remaining = graph.copy()
    selected = []

    while remaining.number_of_nodes() > 0:
        degrees = dict(remaining.degree())
        min_degree = min(degrees.values())
        candidates = [node for node, degree in degrees.items() if degree == min_degree]
        vertex = rng.choice(candidates)
        selected.append(vertex)
        to_remove = set(remaining.neighbors(vertex))
        to_remove.add(vertex)
        remaining.remove_nodes_from(to_remove)

    return IndependentSetResult(
        method="greedy_min_degree",
        size=len(selected),
        vertices=selected,
        status="feasible",
        runtime_seconds=time.perf_counter() - start,
    )


def repeated_greedy(
    graph: nx.Graph,
    repeats: int = 50,
    seed: int = 0,
    include_min_degree: bool = True,
) -> IndependentSetResult:
    """Run greedy many times and keep the largest independent set found."""
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    start = time.perf_counter()
    best: IndependentSetResult | None = None
    rng = random.Random(seed)

    for _ in range(repeats):
        result = greedy_random_order(graph, seed=rng.randrange(2**32))
        if best is None or result.size > best.size:
            best = result

    if include_min_degree:
        result = greedy_min_degree(graph, seed=rng.randrange(2**32))
        if best is None or result.size > best.size:
            best = result

    assert best is not None
    best.method = "repeated_greedy"
    best.runtime_seconds = time.perf_counter() - start
    return best


def solve_mis_ip_scipy(
    graph: nx.Graph,
    time_limit: float | None = 60.0,
    mip_rel_gap: float | None = None,
    verbose: bool = False,
) -> IndependentSetResult:
    """Solve maximum independent set exactly, or with a time-limited MIP run.

    Formulation:
        maximize sum_i x_i
        s.t. x_u + x_v <= 1 for each edge (u, v)
             x_i binary
    """
    start = time.perf_counter()
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import coo_matrix
    except Exception as exc:  # pragma: no cover - depends on local install
        return IndependentSetResult(
            method="ip_scipy",
            size=0,
            vertices=[],
            status="unavailable",
            runtime_seconds=time.perf_counter() - start,
            message=f"SciPy MILP unavailable: {exc}",
        )

    relabeled, reverse = relabel_consecutive(graph)
    n = relabeled.number_of_nodes()
    m = relabeled.number_of_edges()

    if n == 0:
        return IndependentSetResult("ip_scipy", 0, [], "optimal", time.perf_counter() - start)
    if m == 0:
        return IndependentSetResult(
            "ip_scipy",
            n,
            [reverse[i] for i in range(n)],
            "optimal",
            time.perf_counter() - start,
            objective_bound=float(n),
            mip_gap=0.0,
        )

    rows = []
    cols = []
    data = []
    for row, (u, v) in enumerate(relabeled.edges()):
        rows.extend([row, row])
        cols.extend([u, v])
        data.extend([1.0, 1.0])

    constraints = LinearConstraint(
        coo_matrix((data, (rows, cols)), shape=(m, n)),
        lb=-np.inf * np.ones(m),
        ub=np.ones(m),
    )
    options = {"disp": verbose}
    if time_limit is not None:
        options["time_limit"] = time_limit
    if mip_rel_gap is not None:
        options["mip_rel_gap"] = mip_rel_gap

    result = milp(
        c=-np.ones(n),
        integrality=np.ones(n),
        bounds=Bounds(np.zeros(n), np.ones(n)),
        constraints=constraints,
        options=options,
    )

    if result.x is None:
        selected = []
    else:
        selected = [i for i, value in enumerate(result.x) if value >= 0.5]

    status_map = {
        0: "optimal",
        1: "limit_reached",
        2: "infeasible",
        3: "unbounded",
        4: "solver_error",
    }
    status = status_map.get(getattr(result, "status", None), "unknown")

    dual_bound = getattr(result, "mip_dual_bound", None)
    objective_bound = None if dual_bound is None else -float(dual_bound)
    mip_gap = getattr(result, "mip_gap", None)
    mip_gap = None if mip_gap is None else float(mip_gap)

    vertices = [reverse[i] for i in selected]
    return IndependentSetResult(
        method="ip_scipy",
        size=len(vertices),
        vertices=vertices,
        status=status,
        runtime_seconds=time.perf_counter() - start,
        objective_bound=objective_bound,
        mip_gap=mip_gap,
        message=str(getattr(result, "message", "")),
    )


def solve_mis_bruteforce(graph: nx.Graph, max_nodes: int = 25) -> IndependentSetResult:
    """Tiny-graph exact solver used for testing and sanity checks."""
    start = time.perf_counter()
    nodes = list(graph.nodes())
    if len(nodes) > max_nodes:
        raise ValueError(f"bruteforce only supports at most {max_nodes} nodes")

    best = []
    for mask in range(1 << len(nodes)):
        if bin(mask).count("1") <= len(best):
            continue
        candidate = [nodes[i] for i in range(len(nodes)) if mask & (1 << i)]
        if is_independent_set(graph, candidate):
            best = candidate

    return IndependentSetResult(
        method="bruteforce",
        size=len(best),
        vertices=best,
        status="optimal",
        runtime_seconds=time.perf_counter() - start,
        objective_bound=float(len(best)),
        mip_gap=0.0,
    )

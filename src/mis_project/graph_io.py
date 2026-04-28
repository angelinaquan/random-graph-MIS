"""Graph generation, loading, and summary utilities."""

from __future__ import annotations

import gzip
import math
import urllib.request
from pathlib import Path
from typing import Dict, Hashable, Iterable, Tuple

import networkx as nx


def generate_er_graph(n: int, d: float, seed: int | None = None) -> nx.Graph:
    """Generate an Erdos-Renyi graph G(n, d/n)."""
    if n <= 0:
        raise ValueError("n must be positive")
    if d < 0:
        raise ValueError("d must be nonnegative")

    p = min(1.0, d / n)
    graph = nx.fast_gnp_random_graph(n, p, seed=seed)
    graph.remove_edges_from(nx.selfloop_edges(graph))
    return graph


def relabel_consecutive(graph: nx.Graph) -> Tuple[nx.Graph, Dict[int, Hashable]]:
    """Return a graph relabeled to 0..n-1 and a reverse label map."""
    nodes = list(graph.nodes())
    forward = {node: i for i, node in enumerate(nodes)}
    reverse = {i: node for node, i in forward.items()}
    relabeled = nx.relabel_nodes(graph, forward, copy=True)
    return relabeled, reverse


def clean_undirected_graph(graph: nx.Graph) -> nx.Graph:
    """Convert to a simple undirected graph with self-loops removed."""
    undirected = nx.Graph()
    undirected.add_nodes_from(graph.nodes())
    undirected.add_edges_from((u, v) for u, v in graph.edges() if u != v)
    undirected.remove_edges_from(nx.selfloop_edges(undirected))
    return undirected


def load_snap_edge_list(path: str | Path, largest_component: bool = False) -> nx.Graph:
    """Load a SNAP-style edge list.

    SNAP files generally contain whitespace-separated node pairs and comment
    lines beginning with '#'. Directed files are converted to simple undirected
    graphs because independent set is defined here on undirected conflicts.
    """
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open

    graph = nx.Graph()
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 2:
                continue
            u, v = parts[0], parts[1]
            if u != v:
                graph.add_edge(u, v)

    graph = clean_undirected_graph(graph)
    if largest_component and graph.number_of_nodes() > 0:
        component = max(nx.connected_components(graph), key=len)
        graph = graph.subgraph(component).copy()
    relabeled, _ = relabel_consecutive(graph)
    return relabeled


def download_file(url: str, output_path: str | Path) -> Path:
    """Download a dataset file.

    This is intentionally small and boring so the project does not depend on a
    SNAP-specific downloader. For many SNAP datasets, use the direct .txt.gz URL
    from the dataset page.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, output_path)
    return output_path


def graph_stats(graph: nx.Graph) -> dict:
    """Compute summary statistics used in experiment tables."""
    n = graph.number_of_nodes()
    m = graph.number_of_edges()
    avg_degree = 0.0 if n == 0 else 2.0 * m / n
    components = nx.number_connected_components(graph) if n else 0
    largest_component = 0 if n == 0 else len(max(nx.connected_components(graph), key=len))
    return {
        "n": n,
        "m": m,
        "avg_degree": avg_degree,
        "components": components,
        "largest_component": largest_component,
        "density": nx.density(graph) if n > 1 else 0.0,
    }


def er_theory(n: int, d: float) -> dict:
    """Return the common asymptotic predictions for G(n, d/n)."""
    if d <= 1:
        return {
            "theory_greedy": math.nan,
            "theory_optimum": math.nan,
            "theory_greedy_fraction": math.nan,
            "theory_optimum_fraction": math.nan,
        }

    greedy_fraction = math.log(d) / d
    optimum_fraction = 2.0 * math.log(d) / d
    return {
        "theory_greedy": greedy_fraction * n,
        "theory_optimum": optimum_fraction * n,
        "theory_greedy_fraction": greedy_fraction,
        "theory_optimum_fraction": optimum_fraction,
    }

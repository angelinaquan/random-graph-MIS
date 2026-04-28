import networkx as nx

from mis_project.graph_io import er_theory, generate_er_graph
from mis_project.solvers import (
    is_independent_set,
    repeated_greedy,
    solve_mis_bruteforce,
    solve_mis_ip_scipy,
)


def test_greedy_returns_independent_set():
    graph = generate_er_graph(40, 6, seed=0)
    result = repeated_greedy(graph, repeats=5, seed=0)
    assert result.size == len(result.vertices)
    assert is_independent_set(graph, result.vertices)


def test_ip_matches_bruteforce_on_small_graph():
    graph = nx.cycle_graph(7)
    exact = solve_mis_bruteforce(graph)
    ip = solve_mis_ip_scipy(graph, time_limit=10)
    assert ip.status == "optimal"
    assert ip.size == exact.size
    assert is_independent_set(graph, ip.vertices)


def test_er_theory_d20():
    theory = er_theory(1000, 20)
    assert round(theory["theory_greedy"], 1) == 149.8
    assert round(theory["theory_optimum"], 1) == 299.6

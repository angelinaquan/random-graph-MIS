"""Command-line experiment runners for the MIS project."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from .graph_io import er_theory, generate_er_graph, graph_stats, load_snap_edge_list
from .solvers import is_independent_set, repeated_greedy, solve_mis_ip_scipy


def result_fields(prefix: str, result) -> dict[str, Any]:
    return {
        f"{prefix}_method": result.method,
        f"{prefix}_size": result.size,
        f"{prefix}_status": result.status,
        f"{prefix}_runtime_seconds": result.runtime_seconds,
        f"{prefix}_objective_bound": result.objective_bound,
        f"{prefix}_mip_gap": result.mip_gap,
        f"{prefix}_message": result.message,
    }


def write_rows(rows: list[dict[str, Any]], output: str | Path) -> pd.DataFrame:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(output, index=False)
    return frame


def run_er(args: argparse.Namespace) -> None:
    rows = []
    for n in args.n_values:
        for seed in args.seeds:
            graph = generate_er_graph(n=n, d=args.d, seed=seed)
            stats = graph_stats(graph)
            greedy = repeated_greedy(graph, repeats=args.greedy_repeats, seed=seed)
            if not is_independent_set(graph, greedy.vertices):
                raise RuntimeError("greedy returned a non-independent set")

            row: dict[str, Any] = {
                "graph_type": "er",
                "n_requested": n,
                "d_requested": args.d,
                "seed": seed,
                **stats,
                **er_theory(n, args.d),
                **result_fields("greedy", greedy),
            }

            if not args.skip_ip:
                ip = solve_mis_ip_scipy(
                    graph,
                    time_limit=args.time_limit,
                    mip_rel_gap=args.mip_rel_gap,
                    verbose=args.verbose_solver,
                )
                if ip.vertices and not is_independent_set(graph, ip.vertices):
                    raise RuntimeError("IP returned a non-independent set")
                row.update(result_fields("ip", ip))

            rows.append(row)
            print(
                f"ER n={n} d={args.d} seed={seed}: "
                f"greedy={greedy.size}"
                + ("" if args.skip_ip else f", ip={row.get('ip_size')} ({row.get('ip_status')})")
            )

    frame = write_rows(rows, args.output)
    print(f"\nWrote {len(frame)} rows to {args.output}")
    print(frame.to_string(index=False))


def run_snap(args: argparse.Namespace) -> None:
    graph = load_snap_edge_list(args.path, largest_component=args.largest_component)
    stats = graph_stats(graph)
    greedy = repeated_greedy(graph, repeats=args.greedy_repeats, seed=args.seed)
    if not is_independent_set(graph, greedy.vertices):
        raise RuntimeError("greedy returned a non-independent set")

    row: dict[str, Any] = {
        "graph_type": "snap",
        "dataset": Path(args.path).name,
        "seed": args.seed,
        "largest_component_only": args.largest_component,
        **stats,
        **er_theory(stats["n"], max(stats["avg_degree"], 0.0)),
        **result_fields("greedy", greedy),
    }

    if not args.skip_ip:
        ip = solve_mis_ip_scipy(
            graph,
            time_limit=args.time_limit,
            mip_rel_gap=args.mip_rel_gap,
            verbose=args.verbose_solver,
        )
        if ip.vertices and not is_independent_set(graph, ip.vertices):
            raise RuntimeError("IP returned a non-independent set")
        row.update(result_fields("ip", ip))

    frame = write_rows([row], args.output)
    print(f"Wrote SNAP result to {args.output}")
    print(frame.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maximum independent set experiments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    er = subparsers.add_parser("er", help="Run Erdos-Renyi experiments")
    er.add_argument("--d", type=float, default=20.0)
    er.add_argument("--n-values", type=int, nargs="+", default=[100, 200, 500])
    er.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    er.add_argument("--greedy-repeats", type=int, default=50)
    er.add_argument("--time-limit", type=float, default=60.0)
    er.add_argument("--mip-rel-gap", type=float, default=None)
    er.add_argument("--skip-ip", action="store_true")
    er.add_argument("--verbose-solver", action="store_true")
    er.add_argument("--output", default="results/er_results.csv")
    er.set_defaults(func=run_er)

    snap = subparsers.add_parser("snap", help="Run one SNAP dataset experiment")
    snap.add_argument("path", help="Path to a SNAP .txt or .txt.gz edge list")
    snap.add_argument("--seed", type=int, default=0)
    snap.add_argument("--greedy-repeats", type=int, default=100)
    snap.add_argument("--time-limit", type=float, default=300.0)
    snap.add_argument("--mip-rel-gap", type=float, default=None)
    snap.add_argument("--largest-component", action="store_true")
    snap.add_argument("--skip-ip", action="store_true")
    snap.add_argument("--verbose-solver", action="store_true")
    snap.add_argument("--output", default="results/snap_results.csv")
    snap.set_defaults(func=run_snap)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

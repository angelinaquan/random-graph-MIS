"""Plot helpers for experiment CSVs."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mis_project_matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_er(input_csv: str | Path, output: str | Path) -> None:
    frame = pd.read_csv(input_csv)
    frame = frame[frame["graph_type"] == "er"].copy()
    if frame.empty:
        raise ValueError("input CSV has no ER rows")

    grouped = frame.groupby("n_requested", as_index=False).mean(numeric_only=True)
    x = grouped["n_requested"]

    plt.figure(figsize=(7, 4.5))
    plt.plot(x, grouped["greedy_size"] / x, marker="o", label="Greedy")
    if "ip_size" in grouped:
        plt.plot(x, grouped["ip_size"] / x, marker="o", label="IP incumbent")
    plt.plot(x, grouped["theory_greedy_fraction"], linestyle="--", label="(log d / d)")
    plt.plot(x, grouped["theory_optimum_fraction"], linestyle="--", label="(2 log d / d)")
    plt.xlabel("n")
    plt.ylabel("independent set fraction")
    plt.title("Maximum independent set on G(n, d/n)")
    plt.legend()
    plt.tight_layout()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200)
    print(f"Wrote {output}")


def plot_snap(input_csv: str | Path, output: str | Path) -> None:
    frame = pd.read_csv(input_csv)
    frame = frame[frame["graph_type"] == "snap"].copy()
    if frame.empty:
        raise ValueError("input CSV has no SNAP rows")

    row = frame.iloc[0]
    labels = ["Greedy", "ER greedy pred.", "ER optimum pred."]
    values = [
        row["greedy_size"],
        row["theory_greedy"],
        row["theory_optimum"],
    ]
    if "ip_size" in frame.columns and pd.notna(row.get("ip_size")):
        labels.insert(1, "IP incumbent")
        values.insert(1, row["ip_size"])

    plt.figure(figsize=(7, 4.5))
    plt.bar(labels, values)
    plt.ylabel("independent set size")
    plt.title(f"SNAP result: {row['dataset']}")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=200)
    print(f"Wrote {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot MIS experiment CSVs")
    parser.add_argument("kind", choices=["er", "snap"])
    parser.add_argument("input_csv")
    parser.add_argument("--output", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.kind == "er":
        plot_er(args.input_csv, args.output)
    else:
        plot_snap(args.input_csv, args.output)


if __name__ == "__main__":
    main()

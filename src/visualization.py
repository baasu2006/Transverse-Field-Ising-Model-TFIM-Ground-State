# solution_tfim_simulation/src/visualization.py
"""
Visualization module to generate publication-grade figures for Phase 1 submission:
- Processor coupling graphs
- Logical vs transpiled circuit comparison
- Processor A vs Processor B performance comparisons
- Architecture trade-offs
"""

from typing import Dict, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def draw_processor_graph(
    proc: Dict[str, Any],
    title: str,
    out_path: str,
    pos: Optional[Dict[int, tuple]] = None
) -> None:
    """
    Renders and exports the processor coupling topology graph.
    """
    G = nx.Graph()
    G.add_nodes_from(range(proc["num_qubits"]))
    G.add_edges_from(map(tuple, proc["coupling_map"]))

    fig, ax = plt.subplots(figsize=(6, 5))
    if pos is None:
        pos = nx.spring_layout(G, seed=42)

    nx.draw_networkx_nodes(
        G, pos, ax=ax, node_color="#4C9AFF", node_size=800, edgecolors="#172B4D", linewidths=2
    )
    nx.draw_networkx_edges(
        G, pos, ax=ax, edge_color="#172B4D", width=2.5
    )
    nx.draw_networkx_labels(
        G, pos, ax=ax, font_size=12, font_family="sans-serif", font_weight="bold", font_color="white"
    )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.axis("off")
    plt.tight_layout()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_ab_comparison(df_ab: pd.DataFrame, out_path: str) -> None:
    """
    Generates a bar plot comparing architecture metrics between Processor A and B.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5))
    df_ab[["Processor A", "Processor B"]].plot(
        kind="bar", ax=ax, color=["#0052CC", "#36B37E"], edgecolor="black"
    )
    ax.set_ylabel("Metric Count / Value", fontsize=12, fontweight="bold")
    ax.set_title("Architecture-Aware Resource Metrics: Processor A vs B", fontsize=13, fontweight="bold")
    plt.xticks(rotation=15, ha="right", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_logical_vs_transpiled(
    metrics_log: Dict[str, Any],
    metrics_A: Dict[str, Any],
    metrics_B: Dict[str, Any],
    out_path: str
) -> None:
    """
    Visualizes circuit compilation overhead from logical to physical architectures.
    """
    categories = ["depth", "total_ops", "two_qubit_ops_estimate", "swap_count"]
    labels = ["Circuit Depth", "Total Ops", "2-Qubit Gates", "SWAP Gates"]

    data = {
        "Logical": [metrics_log.get(k, 0) for k in categories],
        "Processor A": [metrics_A.get(k, 0) for k in categories],
        "Processor B": [metrics_B.get(k, 0) for k in categories],
    }
    df = pd.DataFrame(data, index=labels)

    fig, ax = plt.subplots(figsize=(9, 5))
    df.plot(kind="bar", ax=ax, color=["#6554C0", "#0052CC", "#36B37E"], edgecolor="black")
    ax.set_ylabel("Operation / Layer Count", fontsize=12, fontweight="bold")
    ax.set_title("Compilation Impact: Logical Circuit vs Processor A vs Processor B", fontsize=13, fontweight="bold")
    plt.xticks(rotation=0, fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_architecture_tradeoffs(
    summary_df: pd.DataFrame,
    out_path: str
) -> None:
    """
    Generates a scatter/tradeoff plot relating circuit depth / 2Q gates to observed noisy energy error.
    """
    fig, ax = plt.subplots(figsize=(8, 4.5))

    for _, row in summary_df.iterrows():
        name = row["Processor"]
        color = "#0052CC" if "A" in name else "#36B37E"
        ax.scatter(row["Depth"], row["Energy Error"], s=250, color=color, edgecolors="black", linewidths=2, label=name)
        ax.annotate(
            f"{name}\n(2Q: {row['2Q Gates']}, SWAPs: {row['SWAPs']})",
            (row["Depth"], row["Energy Error"]),
            textcoords="offset points",
            xytext=(10, 10),
            fontsize=10,
            fontweight="bold"
        )

    ax.set_xlabel("Compiled Circuit Depth", fontsize=12, fontweight="bold")
    ax.set_ylabel("Ground-State Energy Error |E_noisy - E_exact|", fontsize=12, fontweight="bold")
    ax.set_title("Architecture Trade-offs: Compilation Overhead vs Error Exposure", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

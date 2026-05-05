from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from .common import finalize_figure, add_panel_label


def _draw_network(ax, nodes: pd.DataFrame, edges: pd.DataFrame, title: str) -> None:
    g = nx.DiGraph()
    for _, row in nodes.iterrows():
        g.add_node(row["node_id"], logfc=float(row.get("logfc", 0.0)))
    for _, row in edges.iterrows():
        g.add_edge(row["source"], row["target"], delta_ecv=float(row.get("delta_ecv", 0.0)))
    pos = nx.spring_layout(g, seed=42)
    node_colors = [g.nodes[n].get("logfc", 0.0) for n in g.nodes]
    edge_widths = [1 + abs(g.edges[e].get("delta_ecv", 0.0)) * 2 for e in g.edges]
    nx.draw_networkx_nodes(g, pos, node_color=node_colors, cmap="coolwarm", node_size=400, ax=ax)
    nx.draw_networkx_edges(g, pos, width=edge_widths, alpha=0.6, arrows=True, ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=8, ax=ax)
    ax.set_title(title)
    ax.axis("off")


def generate_fig4(config: dict, outdir: str | Path) -> list[str]:
    root = Path(config["paths"]["derived_root"])
    nodes = pd.read_csv(root / "networks/patient_network_nodes.tsv", sep="\t")
    edges = pd.read_csv(root / "networks/patient_network_edges.tsv", sep="\t")
    drug = "LDN193189"
    patients = list(dict.fromkeys(nodes[nodes["drug"] == drug]["patient_id"].tolist()))[:4]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, patient, label in zip(axes.ravel(), patients, ["A", "B", "C", "D"]):
        nsub = nodes[(nodes["drug"] == drug) & (nodes["patient_id"] == patient)]
        esub = edges[(edges["drug"] == drug) & (edges["patient_id"] == patient)]
        _draw_network(ax, nsub, esub, f"{drug} / {patient}")
        add_panel_label(ax, label)
    output = finalize_figure(fig, Path(outdir) / "fig4.png")
    return [output]


def generate_fig5(config: dict, outdir: str | Path) -> list[str]:
    root = Path(config["paths"]["derived_root"])
    common_nodes = pd.read_csv(root / "networks/common_network_nodes.tsv", sep="\t")
    common_edges = pd.read_csv(root / "networks/common_network_edges.tsv", sep="\t")
    missing = pd.read_csv(root / "networks/resistant_missing_edges.tsv", sep="\t")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, drug, label in zip([axes[0,0], axes[0,1]], ["LDN193189", "cetuximab"], ["A", "B"]):
        nsub = common_nodes[common_nodes["drug"] == drug]
        esub = common_edges[common_edges["drug"] == drug]
        _draw_network(ax, nsub, esub, f"Common sensitivity network ({drug})")
        add_panel_label(ax, label)

    for ax, drug, label in zip([axes[1,0], axes[1,1]], ["LDN193189", "cetuximab"], ["C", "D"]):
        nsub = common_nodes[common_nodes["drug"] == drug].copy()
        msub = missing[missing["drug"] == drug].copy()
        edges = msub.rename(columns={"status_weight": "delta_ecv"})
        if "status_weight" not in edges.columns:
            edges["delta_ecv"] = edges.get("is_missing", 1).astype(float)
        _draw_network(ax, nsub, edges[["source","target","delta_ecv"]], f"Resistant missing-edge map ({drug})")
        add_panel_label(ax, label)

    output = finalize_figure(fig, Path(outdir) / "fig5.png")
    return [output]

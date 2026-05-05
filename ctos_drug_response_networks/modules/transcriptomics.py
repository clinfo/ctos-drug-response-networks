from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list

from .common import finalize_figure, add_panel_label


def _clustered_matrix(df_long: pd.DataFrame, drug: str) -> pd.DataFrame:
    sub = df_long[df_long["drug"] == drug].copy()
    mat = sub.pivot(index="gene", columns="patient_id", values="value")
    mat = mat.fillna(0.0)
    if mat.shape[0] > 1:
        row_order = leaves_list(linkage(mat.values, method="average"))
        mat = mat.iloc[row_order]
    if mat.shape[1] > 1:
        col_order = leaves_list(linkage(mat.values.T, method="average"))
        mat = mat.iloc[:, col_order]
    return mat


def generate_fig3(config: dict, outdir: str | Path) -> list[str]:
    root = Path(config["paths"]["derived_root"])
    expr = pd.read_csv(root / "processed_expression/pathway_expression_long.tsv", sep="\t")
    logfc = pd.read_csv(root / "processed_expression/pathway_logfc_long.tsv", sep="\t")
    deg = pd.read_csv(root / "processed_expression/deg_shared.tsv", sep="\t")

    drugs = ["LDN193189", "cetuximab"]
    fig, axes = plt.subplots(3, 2, figsize=(12, 12), height_ratios=[1, 1, 0.8])
    labels = ["A", "B", "C", "D", "E", "F"]
    idx = 0
    for col, drug in enumerate(drugs):
        mat = _clustered_matrix(expr, drug)
        ax = axes[0, col]
        im = ax.imshow(mat.values, aspect="auto", cmap="viridis")
        ax.set_title(f"Expression clustering ({drug})")
        ax.set_xticks(range(mat.shape[1]))
        ax.set_xticklabels(mat.columns, rotation=90)
        ax.set_yticks(range(mat.shape[0]))
        ax.set_yticklabels(mat.index)
        add_panel_label(ax, labels[idx]); idx += 1

        mat2 = _clustered_matrix(logfc, drug)
        ax2 = axes[1, col]
        ax2.imshow(mat2.values, aspect="auto", cmap="bwr", vmin=-max(abs(mat2.values.min()), abs(mat2.values.max())), vmax=max(abs(mat2.values.min()), abs(mat2.values.max())))
        ax2.set_title(f"logFC clustering ({drug})")
        ax2.set_xticks(range(mat2.shape[1]))
        ax2.set_xticklabels(mat2.columns, rotation=90)
        ax2.set_yticks(range(mat2.shape[0]))
        ax2.set_yticklabels(mat2.index)
        add_panel_label(ax2, labels[idx]); idx += 1

    deg_sub = deg[deg["drug"] == "LDN193189"].copy().sort_values("mean_logfc")
    ax = axes[2, 0]
    ax.barh(deg_sub["gene"], deg_sub["mean_logfc"])
    ax.set_title("Shared DEGs (LDN193189)")
    ax.set_xlabel("mean logFC")
    add_panel_label(ax, labels[idx]); idx += 1

    ax = axes[2, 1]
    ax.axis("off")
    ax.text(0, 1, "DEG table preview", fontsize=11, fontweight="bold", va="top")
    preview = deg_sub[["gene", "mean_logfc"]].head(12)
    y = 0.9
    for _, row in preview.iterrows():
        ax.text(0.0, y, f"{row['gene']}: {row['mean_logfc']:.3f}", family="monospace")
        y -= 0.07
    add_panel_label(ax, labels[idx])

    output = finalize_figure(fig, Path(outdir) / "fig3.png")
    table_path = Path(outdir) / "tables/fig3_deg_shared.tsv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    deg.to_csv(table_path, sep="\t", index=False)
    return [output, str(table_path)]

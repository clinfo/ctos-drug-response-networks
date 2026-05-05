from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from .common import finalize_figure, add_panel_label

RESPONSE_COLOR = {
    "high_sensitivity": "#c0392b",
    "moderate": "#7f8c8d",
    "resistant": "#2980b9",
}

ALTERATION_COLOR = {
    "mutation": "#e67e22",
    "missense": "#27ae60",
    "frameshift": "#d35400",
    "nonsense": "#8e44ad",
    "inframe": "#c0392b",
}


def _draw_binary_matrix(ax, matrix: pd.DataFrame, colors: pd.DataFrame | None = None) -> None:
    ax.set_xlim(0, matrix.shape[1])
    ax.set_ylim(0, matrix.shape[0])
    ax.invert_yaxis()
    for r, gene in enumerate(matrix.index):
        for c, patient in enumerate(matrix.columns):
            ax.add_patch(plt.Rectangle((c, r), 1, 1, facecolor="white", edgecolor="#cccccc", lw=0.8))
            if matrix.loc[gene, patient]:
                color = colors.loc[gene, patient] if colors is not None else "#34495e"
                ax.add_patch(plt.Rectangle((c + 0.1, r + 0.1), 0.8, 0.8, facecolor=color, edgecolor="none"))
    ax.set_xticks(np.arange(matrix.shape[1]) + 0.5)
    ax.set_xticklabels(matrix.columns, rotation=90)
    ax.set_yticks(np.arange(matrix.shape[0]) + 0.5)
    ax.set_yticklabels(matrix.index)


def generate_fig2(config: dict, outdir: str | Path) -> list[str]:
    root = Path(config["paths"]["derived_root"])
    sens = pd.read_csv(root / "drug_response/drug_sensitivity_table.tsv", sep="\t")
    muts = pd.read_csv(root / "genomics/pathway_mutations.tsv", sep="\t")
    cna = pd.read_csv(root / "genomics/pathway_cna.tsv", sep="\t")
    patients = list(dict.fromkeys(sens["patient_id"].tolist()))

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), height_ratios=[1, 1.2])
    panels = [("LDN193189", "BMP", "A"), ("cetuximab", "EGFR", "B")]
    for ax, (drug, pathway, label) in zip(axes, panels):
        sub = muts[(muts["drug"] == drug) & (muts["pathway"] == pathway)].copy()
        genes = list(dict.fromkeys(sub["gene"].tolist()))
        matrix = pd.DataFrame(False, index=genes, columns=patients)
        color_matrix = pd.DataFrame("#34495e", index=genes, columns=patients)
        for _, row in sub.iterrows():
            if row["patient_id"] in matrix.columns and row["gene"] in matrix.index:
                matrix.loc[row["gene"], row["patient_id"]] = True
                color_matrix.loc[row["gene"], row["patient_id"]] = ALTERATION_COLOR.get(str(row.get("alteration_type", "mutation")).lower(), "#34495e")
        _draw_binary_matrix(ax, matrix, color_matrix)
        ax.set_title(f"{pathway} pathway alterations ({drug})")
        add_panel_label(ax, label)
    output = finalize_figure(fig, Path(outdir) / "fig2.png")

    # auxiliary CNA summary table
    cna_summary = cna.groupby(["drug", "gene"], as_index=False)["cna_value"].mean()
    table_path = Path(outdir) / "tables/fig2_cna_summary.tsv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    cna_summary.to_csv(table_path, sep="\t", index=False)
    return [output, str(table_path)]

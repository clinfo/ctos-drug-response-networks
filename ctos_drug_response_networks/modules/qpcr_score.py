from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from .common import finalize_figure, add_panel_label


def generate_fig6(config: dict, outdir: str | Path) -> list[str]:
    root = Path(config["paths"]["derived_root"])
    qpcr = pd.read_csv(root / "validation/qpcr_long.tsv", sep="\t")
    score_path = root / "validation/score_summary.tsv"
    score = pd.read_csv(score_path, sep="\t") if score_path.exists() else None

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    panels = [
        ("LDN193189", "8h", "A"),
        ("LDN193189", "48h", "B"),
        ("cetuximab", "8h", "C"),
        ("cetuximab", "48h", "D"),
    ]
    for ax, drug, timepoint, label in zip(axes.ravel(), [p[0] for p in panels], [p[1] for p in panels], [p[2] for p in panels]):
        sub = qpcr[(qpcr["drug"] == drug) & (qpcr["timepoint"] == timepoint)]
        if sub.empty:
            ax.axis("off")
            ax.text(0.5, 0.5, f"No qPCR data for {drug} {timepoint}", ha="center", va="center")
            add_panel_label(ax, label)
            continue
        pivot = sub.pivot_table(index="gene", columns="patient_id", values="value")
        ax.imshow(pivot.values, aspect="auto", cmap="coolwarm")
        ax.set_xticks(range(pivot.shape[1]))
        ax.set_xticklabels(pivot.columns, rotation=90)
        ax.set_yticks(range(pivot.shape[0]))
        ax.set_yticklabels(pivot.index)
        ax.set_title(f"{drug} / {timepoint}")
        add_panel_label(ax, label)
    output = finalize_figure(fig, Path(outdir) / "fig6.png")
    outputs = [output]
    if score is not None:
        score_out = Path(outdir) / "tables/fig6_score_summary.tsv"
        score_out.parent.mkdir(parents=True, exist_ok=True)
        score.to_csv(score_out, sep="\t", index=False)
        outputs.append(str(score_out))
    return outputs

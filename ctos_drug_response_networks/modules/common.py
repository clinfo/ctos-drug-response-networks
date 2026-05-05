from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def finalize_figure(fig, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


def add_panel_label(ax, label: str) -> None:
    ax.text(-0.05, 1.05, label, transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")

"""
Make confusion-matrix images for both models (numbers from your TEST results, no model/GPU needed).

Writes: reports/confusion_arthritis.png
        reports/confusion_osteoporosis.png

Run from the project root:
    pip install matplotlib numpy
    python scripts/confusion_images.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "reports"

MODELS = {
    "arthritis": {
        "title": "Arthritis model - KL grade (DenseNet-121)",
        "subtitle": "Test set n=1,100  |  Accuracy 73.5%  |  QWK 0.862  |  Within-1-grade 95.5%",
        "classes": ["KL0", "KL1", "KL2", "KL3", "KL4"],
        "cm": [[343, 63, 20, 0, 0],
               [67, 109, 24, 0, 0],
               [24, 52, 188, 21, 2],
               [0, 3, 8, 135, 1],
               [0, 0, 0, 7, 33]],
    },
    "osteoporosis": {
        "title": "Osteoporosis model (DenseNet-121, from arthritis model)",
        "subtitle": "Test set n=68  |  Accuracy 76.5%  |  AUC 0.892  |  Bone-loss sensitivity 91.5%",
        "classes": ["Normal", "Osteopenia", "Osteoporosis"],
        "cm": [[16, 2, 3],
               [3, 19, 2],
               [1, 5, 17]],
    },
}


def plot(name, cfg):
    cm = np.array(cfg["cm"])
    pct = cm / cm.sum(axis=1, keepdims=True)          # % of each TRUE class -> diagonal = recall
    classes, n = cfg["classes"], len(cfg["classes"])

    fig, ax = plt.subplots(figsize=(1.7 * n + 3, 1.5 * n + 2.2))
    im = ax.imshow(pct, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n), classes, fontsize=11)
    ax.set_yticks(range(n), classes, fontsize=11)
    ax.set_xlabel("Predicted by model", fontsize=12, labelpad=8)
    ax.set_ylabel("True label (doctor)", fontsize=12, labelpad=8)
    ax.set_title(f"{cfg['title']} - normalised confusion matrix\n{cfg['subtitle']}", fontsize=11.5, pad=12)

    for i in range(n):
        for j in range(n):
            color = "white" if pct[i, j] > 0.5 else "#1f2937"
            ax.text(j, i, f"{pct[i, j]:.2f}", ha="center", va="center", color=color,
                    fontsize=14 if n <= 3 else 12, fontweight="bold" if i == j else "normal")

    ax.set_xticks(np.arange(-0.5, n), minor=True)       # thin white grid between cells
    ax.set_yticks(np.arange(-0.5, n), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Fraction of true class (row-normalised)", fontsize=10)
    fig.tight_layout()
    path = OUT / f"confusion_{name}.png"
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, cfg in MODELS.items():
        plot(name, cfg)
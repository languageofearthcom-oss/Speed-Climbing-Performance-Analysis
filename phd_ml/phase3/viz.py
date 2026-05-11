"""Diagnostic figures for Phase 3."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from . import config
from .training import FoldResult


def _save(fig, name: str) -> Path:
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURE_DIR / name
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_training_curves(fold_results: list[FoldResult]) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    for fr in fold_results:
        ax.plot(fr.train_loss_history, alpha=0.5,
                label=f"fold {fr.fold} train", linestyle="--")
        ax.plot(fr.val_loss_history, alpha=0.8,
                label=f"fold {fr.fold} val")
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss")
    ax.set_title("Phase 3 — training & validation loss per fold")
    ax.legend(fontsize=7, ncol=2)
    return _save(fig, "training_curves.png")


def plot_confusion_matrices(per_fold_metrics: list[dict]) -> Path:
    """Single pooled confusion matrix across folds."""
    cm = np.zeros((2, 2), dtype=int)
    for m in per_fold_metrics:
        cm += np.asarray(m["confusion_matrix"], dtype=int)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], ["advanced", "beginner"])
    ax.set_yticks([0, 1], ["advanced", "beginner"])
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title("Phase 3 — pooled confusion (CNN)")
    fig.colorbar(im, ax=ax)
    return _save(fig, "confusion_matrix.png")


def plot_metric_summary(metrics_aggregated: dict, phase2_path: Path | None = None) -> Path:
    """Bar chart of headline metrics; optional phase 2 overlay."""
    keys = ["f1_macro", "f1_minority", "roc_auc", "pr_auc"]
    means = [metrics_aggregated.get(f"{k}_mean") or 0.0 for k in keys]
    stds = [metrics_aggregated.get(f"{k}_std") or 0.0 for k in keys]
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(keys))
    ax.bar(x, means, yerr=stds, capsize=4, label="CNN 1D")
    ax.axhline(0.978, ls="--", color="red", alpha=0.6,
               label="Phase-2 logreg target (0.978)")
    ax.set_xticks(x, keys)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score (mean ± std across folds)")
    ax.set_title("Phase 3 — CNN metrics vs Phase 2 reference")
    ax.legend()
    return _save(fig, "metric_summary.png")

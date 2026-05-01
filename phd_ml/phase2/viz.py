"""Phase 2 figures — saved to figures/phd_ml/phase2/.

Plots:
  1. confusion_matrices.png      — one matrix per model, side-by-side
  2. roc_curves.png              — overlaid CV-aggregated ROC curves
  3. pr_curves.png               — overlaid CV-aggregated PR curves
  4. metric_comparison.png       — bar chart with macro-F1, F1-minority, ROC-AUC, PR-AUC
  5. feature_importance.png      — top-15 features per method, faceted by model
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)

from . import config
from .evaluation import ModelCVResult


def _ensure_dir() -> Path:
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    return config.FIGURE_DIR


def plot_confusion_matrices(results: list[ModelCVResult]) -> Path:
    """One pooled confusion matrix per model (sum across folds)."""
    n = len(results)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 4.0 * rows))
    axes = np.atleast_1d(axes).ravel()

    for ax, r in zip(axes, results):
        y_true = np.concatenate([f.y_true for f in r.folds])
        y_pred = np.concatenate([f.y_pred for f in r.folds])
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        ConfusionMatrixDisplay(cm, display_labels=["advanced", "beginner"]).plot(
            ax=ax, cmap="Blues", colorbar=False, values_format="d",
        )
        ax.set_title(r.name, fontsize=10)
    for ax in axes[len(results):]:
        ax.axis("off")

    fig.suptitle("Confusion matrices (pooled across folds)", fontsize=12)
    fig.tight_layout()
    out = _ensure_dir() / "confusion_matrices.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def _pooled_curves(results: list[ModelCVResult]):
    """Yield (name, y_true, y_proba) for models that produced probabilities."""
    for r in results:
        if all(f.y_proba is None for f in r.folds):
            continue
        y_true = np.concatenate([f.y_true for f in r.folds])
        y_proba = np.concatenate([
            f.y_proba if f.y_proba is not None else np.zeros_like(f.y_true, dtype=float)
            for f in r.folds
        ])
        yield r.name, y_true, y_proba


def plot_roc_curves(results: list[ModelCVResult]) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for name, y_true, y_proba in _pooled_curves(results):
        try:
            fpr, tpr, _ = roc_curve(y_true, y_proba)
            ax.plot(fpr, tpr, label=name, linewidth=1.5)
        except ValueError:
            continue
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=0.8)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC curves (pooled across folds)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    out = _ensure_dir() / "roc_curves.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_pr_curves(results: list[ModelCVResult]) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for name, y_true, y_proba in _pooled_curves(results):
        try:
            prec, rec, _ = precision_recall_curve(y_true, y_proba)
            ax.plot(rec, prec, label=name, linewidth=1.5)
        except ValueError:
            continue
    ax.set_xlabel("Recall (minority)")
    ax.set_ylabel("Precision (minority)")
    ax.set_title("Precision-Recall curves (pooled across folds)")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    out = _ensure_dir() / "pr_curves.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_metric_comparison(results: list[ModelCVResult]) -> Path:
    metrics = ["f1_macro", "f1_minority", "roc_auc", "pr_auc"]
    names = [r.name for r in results]
    vals = {m: [] for m in metrics}
    errs = {m: [] for m in metrics}
    for r in results:
        for m in metrics:
            v = r.metrics_aggregated.get(f"{m}_mean")
            e = r.metrics_aggregated.get(f"{m}_std", 0.0)
            vals[m].append(v if v is not None else 0.0)
            errs[m].append(e if e is not None else 0.0)

    x = np.arange(len(names))
    width = 0.20
    fig, ax = plt.subplots(figsize=(max(8, 1.3 * len(names)), 5))
    for i, m in enumerate(metrics):
        ax.bar(x + (i - 1.5) * width, vals[m], width,
               yerr=errs[m], label=m, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="grey", linewidth=0.5, linestyle="--")
    ax.set_ylabel("Score (mean ± std across folds)")
    ax.set_title("Phase 2 — model comparison on imbalance-aware metrics")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out = _ensure_dir() / "metric_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_feature_importance(df: pd.DataFrame, top_k: int = 15) -> Path:
    """One panel per model, two bars per feature (native + permutation)."""
    if df.empty:
        return _ensure_dir() / "feature_importance.png"

    models = sorted(df["model"].unique())
    cols = min(2, len(models))
    rows = (len(models) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(7.5 * cols, 4.5 * rows))
    axes = np.atleast_1d(axes).ravel()

    for ax, model in zip(axes, models):
        sub = df[df["model"] == model].copy()
        # Rank by permutation if present, else native
        rank_method = "permutation" if (sub["method"] == "permutation").any() else "native"
        ranking = (
            sub[sub["method"] == rank_method]
            .sort_values("score", ascending=False)
            .head(top_k)["feature"].tolist()
        )
        sub = sub[sub["feature"].isin(ranking)].copy()
        sub["feature"] = pd.Categorical(sub["feature"], categories=ranking, ordered=True)
        sub = sub.sort_values("feature")
        pivot = sub.pivot(index="feature", columns="method", values="score").fillna(0)
        err = sub.pivot(index="feature", columns="method", values="score_std").fillna(0)

        pivot.plot(kind="barh", ax=ax, xerr=err, capsize=2)
        ax.invert_yaxis()
        ax.set_title(f"{model} — top {len(ranking)} features", fontsize=10)
        ax.set_xlabel("Importance")
    for ax in axes[len(models):]:
        ax.axis("off")

    fig.tight_layout()
    out = _ensure_dir() / "feature_importance.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out

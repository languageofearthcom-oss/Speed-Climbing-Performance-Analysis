"""Phase 4 diagnostic figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from . import config


def _ensure_dir() -> Path:
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    return config.FIGURE_DIR


def _ordered(df: pd.DataFrame) -> pd.DataFrame:
    present = [m for m in config.MODEL_ORDER if m in set(df["model"])]
    return df.set_index("model").loc[present].reset_index()


def plot_common_metric_comparison(metrics_df: pd.DataFrame) -> Path:
    metrics = ["f1_macro", "f1_beginner", "roc_auc", "pr_auc"]
    labels = ["Macro-F1", "F1 beginner", "ROC-AUC", "PR-AUC"]
    df = _ordered(metrics_df)

    x = np.arange(len(df))
    width = 0.20
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = ["#4E79A7", "#F28E2B", "#59A14F", "#B07AA1"]
    for i, (metric_name, label) in enumerate(zip(metrics, labels)):
        vals = df[metric_name].fillna(0.0).to_numpy(dtype=float)
        ax.bar(x + (i - 1.5) * width, vals, width, label=label, color=colors[i])

    ax.set_xticks(x)
    ax.set_xticklabels(df["model"], rotation=25, ha="right", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score on common lane-matched samples")
    ax.set_title("Phase 4 fair comparison: identical sample_index subset")
    ax.axhline(0.5, color="#777777", linewidth=0.8, linestyle=":")
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.20))
    fig.tight_layout()
    out = _ensure_dir() / "common_metric_comparison.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_beginner_focus(metrics_df: pd.DataFrame) -> Path:
    df = _ordered(metrics_df)
    x = np.arange(len(df))
    width = 0.32
    fig, ax = plt.subplots(figsize=(10.5, 5))
    ax.bar(
        x - width / 2,
        df["precision_beginner"],
        width,
        label="Precision beginner",
        color="#76B7B2",
    )
    ax.bar(
        x + width / 2,
        df["recall_beginner"],
        width,
        label="Recall beginner",
        color="#E15759",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(df["model"], rotation=25, ha="right", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Minority-class behavior on the shared subset")
    ax.legend(fontsize=9)
    fig.tight_layout()
    out = _ensure_dir() / "beginner_precision_recall.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_reference_confusions(paired: pd.DataFrame) -> Path:
    y_true = paired["y_true"].to_numpy(dtype=int)
    panels = [
        (config.REFERENCE_MODEL, paired["reference_y_pred"].to_numpy(dtype=int)),
        (config.CNN_MODEL, paired["cnn_y_pred"].to_numpy(dtype=int)),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.2))
    for ax, (name, y_pred) in zip(axes, panels):
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        ConfusionMatrixDisplay(
            cm,
            display_labels=[config.NEGATIVE_CLASS_NAME, config.POSITIVE_CLASS_NAME],
        ).plot(ax=ax, cmap="Blues", colorbar=False, values_format="d")
        ax.set_title(name)
    fig.suptitle("Pooled confusion matrices on identical 107 samples", fontsize=12)
    fig.tight_layout()
    out = _ensure_dir() / "reference_vs_cnn_confusion.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_curves(common_long: pd.DataFrame) -> Path:
    keep = [config.REFERENCE_MODEL, config.CNN_MODEL, "dummy_majority"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for model in keep:
        sub = common_long[common_long["model"] == model]
        if sub.empty or sub["y_true"].nunique() < 2:
            continue
        y_true = sub["y_true"].to_numpy(dtype=int)
        y_prob = sub["y_prob_positive"].to_numpy(dtype=float)
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        roc = roc_auc_score(y_true, y_prob)
        pr = average_precision_score(y_true, y_prob)
        axes[0].plot(fpr, tpr, linewidth=2, label=f"{model} ({roc:.3f})")
        axes[1].plot(recall, precision, linewidth=2, label=f"{model} ({pr:.3f})")

    axes[0].plot([0, 1], [0, 1], color="#777777", linestyle=":", linewidth=1)
    axes[0].set_title("ROC curve")
    axes[0].set_xlabel("False positive rate")
    axes[0].set_ylabel("True positive rate")
    axes[1].set_title("Precision-Recall curve")
    axes[1].set_xlabel("Recall beginner")
    axes[1].set_ylabel("Precision beginner")
    for ax in axes:
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
    fig.suptitle("Probability ranking on common samples", fontsize=12)
    fig.tight_layout()
    out = _ensure_dir() / "reference_vs_cnn_curves.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def plot_data_bottleneck(audit: dict) -> Path:
    labels = ["Phase 1/2 labels", "Phase 3 lane-matched"]
    total = [audit["phase2_total_samples"], audit["common_n_samples"]]
    beginner = [audit["phase2_beginner_samples"], audit["common_beginner_samples"]]

    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.bar(x - width / 2, total, width, label="Total samples", color="#4E79A7")
    ax.bar(x + width / 2, beginner, width, label="Beginner samples", color="#E15759")
    for xi, value in zip(x - width / 2, total):
        ax.text(xi, value + 3, str(value), ha="center", va="bottom", fontsize=10)
    for xi, value in zip(x + width / 2, beginner):
        ax.text(xi, value + 3, str(value), ha="center", va="bottom", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Sample count")
    ax.set_title("The binding constraint: lane-matched beginner data")
    ax.legend(fontsize=9)
    fig.tight_layout()
    out = _ensure_dir() / "lane_matched_data_bottleneck.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


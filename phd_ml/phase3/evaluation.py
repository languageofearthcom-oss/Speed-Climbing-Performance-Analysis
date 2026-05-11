"""Metric aggregation paired with Phase 2.

Mirrors phd_ml.phase2.evaluation so the Phase-4 report can compare
baselines and CNN on identical metrics. Where possible, helper signatures
match the Phase 2 module to ease side-by-side use.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .training import FoldResult


@dataclass
class CVResult:
    name: str
    family: str = "cnn"
    strategy: str = "cost_sensitive+aug"
    notes: str = "1D-CNN over BlazePose time-series"
    metrics_per_fold: list[dict] = None
    metrics_aggregated: dict = None


def _safe_roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, y_prob))


def _safe_pr_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(average_precision_score(y_true, y_prob))


def fold_metrics(fr: FoldResult) -> dict:
    cm = confusion_matrix(fr.y_val, fr.y_pred, labels=[0, 1]).tolist()
    return {
        "fold": fr.fold,
        "epochs": fr.epochs_trained,
        "best_val_loss": fr.best_val_loss,
        "f1_macro": float(f1_score(fr.y_val, fr.y_pred, average="macro")),
        "f1_minority": float(f1_score(fr.y_val, fr.y_pred, pos_label=1,
                                       zero_division=0)),
        "precision_minority": float(precision_score(fr.y_val, fr.y_pred,
                                                     pos_label=1, zero_division=0)),
        "recall_minority": float(recall_score(fr.y_val, fr.y_pred,
                                                pos_label=1, zero_division=0)),
        "precision_majority": float(precision_score(fr.y_val, fr.y_pred,
                                                     pos_label=0, zero_division=0)),
        "recall_majority": float(recall_score(fr.y_val, fr.y_pred,
                                                pos_label=0, zero_division=0)),
        "support_minority": int((fr.y_val == 1).sum()),
        "support_majority": int((fr.y_val == 0).sum()),
        "confusion_matrix": cm,
        "roc_auc": _safe_roc_auc(fr.y_val, fr.y_prob),
        "pr_auc": _safe_pr_auc(fr.y_val, fr.y_prob),
    }


def aggregate(per_fold: list[dict]) -> dict:
    keys = [
        "f1_macro", "f1_minority",
        "precision_minority", "recall_minority",
        "precision_majority", "recall_majority",
        "roc_auc", "pr_auc",
        "epochs", "best_val_loss",
    ]
    out: dict = {}
    for k in keys:
        vals = [m[k] for m in per_fold if m.get(k) is not None]
        if not vals:
            out[f"{k}_mean"] = None
            out[f"{k}_std"] = None
            continue
        out[f"{k}_mean"] = float(np.mean(vals))
        out[f"{k}_std"] = float(np.std(vals))
    return out


def to_cv_predictions_df(fold_results: list[FoldResult]) -> pd.DataFrame:
    """Long-format predictions DataFrame keyed by sample_index (race_id).

    Matches the Phase-2 cv_predictions.csv schema so the Phase-4 paired
    comparison can join on `sample_index` directly.
    """
    rows: list[dict] = []
    for fr in fold_results:
        for sid, yt, yp, prob in zip(fr.sample_ids_val, fr.y_val, fr.y_pred, fr.y_prob):
            rows.append({
                "sample_index": sid,
                "fold": fr.fold,
                "y_true": int(yt),
                "y_pred": int(yp),
                "y_prob_positive": float(prob),
                "model": "cnn1d",
            })
    return pd.DataFrame(rows)

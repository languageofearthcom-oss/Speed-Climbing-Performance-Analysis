"""Stratified K-Fold cross-validation harness with imbalance-aware metrics.

The harness is the same for every model so that the comparison is apples-to-
apples. SMOTE is applied INSIDE the fold (training split only) to prevent
test-time leakage — a common but invalidating mistake noted by Saito &
Rehmsmeier (2015).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

from . import config
from .models import ModelSpec

try:
    from imblearn.over_sampling import SMOTE
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False


@dataclass
class FoldResult:
    fold: int
    test_indices: np.ndarray   # original sample indices in this fold's test split
    y_true: np.ndarray
    y_pred: np.ndarray
    y_proba: np.ndarray | None
    n_train: int
    n_test: int
    n_pos_train: int
    n_pos_test: int


@dataclass
class ModelCVResult:
    name: str
    family: str
    strategy: str
    notes: str
    folds: list[FoldResult] = field(default_factory=list)
    metrics_per_fold: list[dict] = field(default_factory=list)
    metrics_aggregated: dict = field(default_factory=dict)


def _predict_proba_safe(estimator, X) -> np.ndarray | None:
    """Return P(class=1) where supported, else None.

    DummyClassifier exposes predict_proba but the values are degenerate.
    We still return them for plotting consistency.
    """
    if hasattr(estimator, "predict_proba"):
        proba = estimator.predict_proba(X)
        if proba.ndim == 2 and proba.shape[1] >= 2:
            return proba[:, 1]
    if hasattr(estimator, "decision_function"):
        return estimator.decision_function(X)
    return None


def _compute_fold_metrics(y_true, y_pred, y_proba) -> dict:
    """All the numbers one needs to defend a result on imbalanced data."""
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    p_per, r_per, f1_per, support = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1], zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    metrics = {
        "accuracy": float((y_true == y_pred).mean()),
        "f1_macro": float(f1_macro),
        "f1_minority": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "precision_minority": float(p_per[1]),
        "recall_minority": float(r_per[1]),
        "precision_majority": float(p_per[0]),
        "recall_majority": float(r_per[0]),
        "support_minority": int(support[1]),
        "support_majority": int(support[0]),
        "confusion_matrix": cm.tolist(),
    }
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
            metrics["pr_auc"] = float(average_precision_score(y_true, y_proba))
        except ValueError:
            metrics["roc_auc"] = None
            metrics["pr_auc"] = None
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
    return metrics


def _aggregate(metrics_per_fold: list[dict]) -> dict:
    """Mean and std across folds for every scalar metric."""
    if not metrics_per_fold:
        return {}
    keys = [k for k, v in metrics_per_fold[0].items()
            if isinstance(v, (int, float)) and v is not None]
    out = {}
    for k in keys:
        vals = [m[k] for m in metrics_per_fold if m.get(k) is not None]
        if vals:
            out[f"{k}_mean"] = float(np.mean(vals))
            out[f"{k}_std"] = float(np.std(vals))
    return out


def cross_validate(
    spec: ModelSpec, X: np.ndarray, y: np.ndarray,
) -> ModelCVResult:
    skf = StratifiedKFold(
        n_splits=config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE,
    )
    result = ModelCVResult(
        name=spec.name, family=spec.family,
        strategy=spec.strategy, notes=spec.notes,
    )

    for fold_id, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_te, y_te = X[test_idx], y[test_idx]

        if spec.needs_smote:
            if not HAS_IMBLEARN:
                raise RuntimeError(
                    f"Model '{spec.name}' needs imbalanced-learn but "
                    f"`imbalanced-learn` is not installed."
                )
            smote = SMOTE(**config.SMOTE_PARAMS)
            X_tr, y_tr = smote.fit_resample(X_tr, y_tr)

        model = spec.factory()
        model.fit(X_tr, y_tr)

        y_pred = model.predict(X_te)
        y_proba = _predict_proba_safe(model, X_te)

        fold = FoldResult(
            fold=fold_id, test_indices=np.asarray(test_idx),
            y_true=y_te, y_pred=y_pred, y_proba=y_proba,
            n_train=len(train_idx), n_test=len(test_idx),
            n_pos_train=int((y[train_idx] == 1).sum()),
            n_pos_test=int((y_te == 1).sum()),
        )
        result.folds.append(fold)

        metrics = _compute_fold_metrics(y_te, y_pred, y_proba)
        metrics["fold"] = fold_id
        result.metrics_per_fold.append(metrics)

    result.metrics_aggregated = _aggregate(result.metrics_per_fold)
    return result


def collect_cv_predictions(
    cv_results: Iterable[ModelCVResult],
) -> pd.DataFrame:
    """Build a long-format dataframe with all held-out predictions.

    Columns: model, fold, sample_index, y_true, y_pred, y_proba.
    `sample_index` is the row index in the original feature matrix, so Phase 4
    can align CNN predictions and baseline predictions on identical held-out
    samples without re-running CV.
    """
    rows = []
    for r in cv_results:
        for fold in r.folds:
            for i in range(len(fold.y_true)):
                proba_val = (
                    float(fold.y_proba[i]) if fold.y_proba is not None else None
                )
                if proba_val is not None and not np.isfinite(proba_val):
                    proba_val = None
                rows.append({
                    "model": r.name,
                    "fold": int(fold.fold),
                    "sample_index": int(fold.test_indices[i]),
                    "y_true": int(fold.y_true[i]),
                    "y_pred": int(fold.y_pred[i]),
                    "y_proba": proba_val,
                })
    return pd.DataFrame(rows)

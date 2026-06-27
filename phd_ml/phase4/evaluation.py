"""Metric helpers for the Phase 2 vs Phase 3 paired comparison."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class MetricBundle:
    model: str
    source_phase: str
    n_samples: int
    support_advanced: int
    support_beginner: int
    accuracy: float
    balanced_accuracy: float
    f1_macro: float
    f1_beginner: float
    precision_beginner: float
    recall_beginner: float
    precision_advanced: float
    recall_advanced: float
    roc_auc: float | None
    pr_auc: float | None
    tn: int
    fp: int
    fn: int
    tp: int

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def safe_roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if y_prob is None or len(np.unique(y_true)) < 2:
        return None
    try:
        return float(roc_auc_score(y_true, y_prob))
    except ValueError:
        return None


def safe_pr_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if y_prob is None or len(np.unique(y_true)) < 2:
        return None
    try:
        return float(average_precision_score(y_true, y_prob))
    except ValueError:
        return None


def compute_metrics(df: pd.DataFrame, model: str, source_phase: str) -> MetricBundle:
    y_true = df["y_true"].to_numpy(dtype=int)
    y_pred = df["y_pred"].to_numpy(dtype=int)
    y_prob = df["y_prob_positive"].to_numpy(dtype=float)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = (int(x) for x in cm.ravel())

    return MetricBundle(
        model=model,
        source_phase=source_phase,
        n_samples=int(len(df)),
        support_advanced=int((y_true == 0).sum()),
        support_beginner=int((y_true == 1).sum()),
        accuracy=float((y_true == y_pred).mean()),
        balanced_accuracy=float(balanced_accuracy_score(y_true, y_pred)),
        f1_macro=float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        f1_beginner=float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        precision_beginner=float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        recall_beginner=float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        precision_advanced=float(precision_score(y_true, y_pred, pos_label=0, zero_division=0)),
        recall_advanced=float(recall_score(y_true, y_pred, pos_label=0, zero_division=0)),
        roc_auc=safe_roc_auc(y_true, y_prob),
        pr_auc=safe_pr_auc(y_true, y_prob),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
    )


def mcnemar_exact(paired: pd.DataFrame) -> dict:
    ref_correct = paired["reference_correct"].to_numpy(dtype=bool)
    cnn_correct = paired["cnn_correct"].to_numpy(dtype=bool)
    ref_only = int((ref_correct & ~cnn_correct).sum())
    cnn_only = int((~ref_correct & cnn_correct).sum())
    both_correct = int((ref_correct & cnn_correct).sum())
    both_wrong = int((~ref_correct & ~cnn_correct).sum())
    discordant = ref_only + cnn_only
    p_value = None
    if discordant > 0:
        p_value = float(
            binomtest(min(ref_only, cnn_only), n=discordant, p=0.5).pvalue
        )
    return {
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "reference_only_correct": ref_only,
        "cnn_only_correct": cnn_only,
        "discordant_pairs": discordant,
        "exact_binomial_p_value": p_value,
    }


def _metric_value(
    metric_name: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> float | None:
    n = len(y_true)
    if n == 0:
        return None
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    def div(num: float, den: float, zero: float | None = 0.0) -> float | None:
        if den == 0:
            return zero
        return float(num / den)

    recall_advanced = div(tn, tn + fp, zero=None)
    recall_beginner = div(tp, tp + fn, zero=None)
    precision_advanced = div(tn, tn + fn)
    precision_beginner = div(tp, tp + fp)

    def f1(precision: float | None, recall: float | None) -> float | None:
        if precision is None or recall is None:
            return None
        if precision + recall == 0:
            return 0.0
        return float(2 * precision * recall / (precision + recall))

    f1_advanced = f1(precision_advanced, recall_advanced)
    f1_beginner = f1(precision_beginner, recall_beginner)

    def rank_auc() -> float | None:
        pos = y_prob[y_true == 1]
        neg = y_prob[y_true == 0]
        if len(pos) == 0 or len(neg) == 0:
            return None
        greater = 0.0
        for score in pos:
            greater += float((score > neg).sum())
            greater += 0.5 * float((score == neg).sum())
        return float(greater / (len(pos) * len(neg)))

    def average_precision() -> float | None:
        n_pos = int((y_true == 1).sum())
        if n_pos == 0:
            return None
        order = np.argsort(-y_prob, kind="mergesort")
        sorted_true = y_true[order]
        tp_cum = np.cumsum(sorted_true == 1)
        ranks = np.arange(1, len(sorted_true) + 1)
        precisions = tp_cum / ranks
        return float(precisions[sorted_true == 1].sum() / n_pos)

    if metric_name == "accuracy":
        return float((y_true == y_pred).mean())
    if metric_name == "balanced_accuracy":
        if recall_advanced is None or recall_beginner is None:
            return None
        return float((recall_advanced + recall_beginner) / 2)
    if metric_name == "f1_macro":
        if f1_advanced is None or f1_beginner is None:
            return None
        return float((f1_advanced + f1_beginner) / 2)
    if metric_name == "f1_beginner":
        return f1_beginner
    if metric_name == "recall_beginner":
        return recall_beginner
    if metric_name == "precision_beginner":
        return precision_beginner
    if metric_name == "roc_auc":
        return rank_auc()
    if metric_name == "pr_auc":
        return average_precision()
    raise ValueError(f"Unknown metric: {metric_name}")


def paired_bootstrap(
    paired: pd.DataFrame,
    metrics: list[str],
    n_iterations: int,
    random_state: int,
) -> tuple[pd.DataFrame, list[dict]]:
    """Bootstrap paired metric differences on the common sample set.

    Difference direction is reference minus CNN. Positive values therefore mean
    the feature-engineered Phase-2 reference is better on that metric.
    """
    rng = np.random.default_rng(random_state)
    n = len(paired)
    rows: list[dict] = []

    y_true = paired["y_true"].to_numpy(dtype=int)
    ref_pred = paired["reference_y_pred"].to_numpy(dtype=int)
    ref_prob = paired["reference_y_prob"].to_numpy(dtype=float)
    cnn_pred = paired["cnn_y_pred"].to_numpy(dtype=int)
    cnn_prob = paired["cnn_y_prob"].to_numpy(dtype=float)

    for iteration in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        yt = y_true[idx]
        for metric_name in metrics:
            ref_val = _metric_value(metric_name, yt, ref_pred[idx], ref_prob[idx])
            cnn_val = _metric_value(metric_name, yt, cnn_pred[idx], cnn_prob[idx])
            if ref_val is None or cnn_val is None:
                continue
            rows.append({
                "iteration": iteration,
                "metric": metric_name,
                "reference_minus_cnn": float(ref_val - cnn_val),
            })

    diffs = pd.DataFrame(rows)
    summary: list[dict] = []
    for metric_name in metrics:
        vals = diffs.loc[
            diffs["metric"] == metric_name, "reference_minus_cnn"
        ].to_numpy(dtype=float)
        if len(vals) == 0:
            summary.append({
                "metric": metric_name,
                "reference_minus_cnn_mean": None,
                "ci95_low": None,
                "ci95_high": None,
                "n_effective": 0,
            })
            continue
        summary.append({
            "metric": metric_name,
            "reference_minus_cnn_mean": float(np.mean(vals)),
            "ci95_low": float(np.percentile(vals, 2.5)),
            "ci95_high": float(np.percentile(vals, 97.5)),
            "n_effective": int(len(vals)),
        })
    return diffs, summary

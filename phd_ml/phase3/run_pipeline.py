"""Phase 3 orchestrator.

Run with:
    python -m phd_ml.phase3.run_pipeline

Outputs (paths in config.py):
    data/phd_ml/phase3/results.json          — per-fold + aggregated metrics
    data/phd_ml/phase3/cv_predictions.csv    — held-out predictions per fold
    data/phd_ml/phase3/intersect_report.csv  — which samples were dropped, why
    figures/phd_ml/phase3/*.png              — training curves, confusion, summary
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from . import config, evaluation, loader, models, viz
from .training import train_one_fold


def _serialise(obj):
    if isinstance(obj, dict):
        return {str(k): _serialise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialise(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def _dataset_audit(ds: loader.PoseDataset) -> dict:
    status_counts = ds.intersect_report["status"].value_counts().to_dict()
    label_status = (
        ds.intersect_report.groupby(["label", "status"])
        .size()
        .rename("count")
        .reset_index()
        .to_dict(orient="records")
    )
    by_competition: dict[str, dict[str, int]] = defaultdict(lambda: {"advanced": 0, "beginner": 0})
    for sample_id, target in zip(ds.sample_ids, ds.y):
        comp = loader.competition_from_race_id(sample_id)
        label = ds.classes[int(target)]
        by_competition[comp][label] += 1
    return {
        "class_balance": dict(Counter(ds.classes[int(y)] for y in ds.y)),
        "intersect_status_counts": status_counts,
        "intersect_by_label_status": label_status,
        "retained_by_competition": dict(sorted(by_competition.items())),
    }


def _fold_composition(ds: loader.PoseDataset, fold_idx: int,
                      train_idx: np.ndarray, val_idx: np.ndarray) -> dict:
    def counts(idx: np.ndarray) -> dict:
        return dict(Counter(ds.classes[int(y)] for y in ds.y[idx]))

    return {
        "fold": fold_idx,
        "train_n": int(len(train_idx)),
        "val_n": int(len(val_idx)),
        "train_class_balance": counts(train_idx),
        "val_class_balance": counts(val_idx),
        "val_competitions": sorted({
            loader.competition_from_race_id(ds.sample_ids[i]) for i in val_idx
        }),
    }


def _write_training_log(fold_results) -> None:
    rows = []
    for fr in fold_results:
        for epoch, (train_loss, val_loss) in enumerate(
            zip(fr.train_loss_history, fr.val_loss_history), start=1
        ):
            rows.append({
                "fold": fr.fold,
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
            })
    pd.DataFrame(rows).to_csv(config.TRAINING_LOG, index=False)
    print(f"[main] training log -> {config.TRAINING_LOG}")


def main() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("Phase 3 — 1D-CNN on pose time-series")
    print("=" * 72)

    # ---- 1. Load + intersect ---------------------------------------------
    ds = loader.build_dataset()

    n_params = models.count_parameters(models.build_model())
    print(f"[main] model parameter count: {n_params:,}")

    # ---- 2. Cross-validate ------------------------------------------------
    fold_results = []
    per_fold_metrics = []
    fold_compositions = []
    for fold_idx, (train_idx, val_idx) in enumerate(loader.iter_splits(ds)):
        print(f"[main] fold {fold_idx} — train n={len(train_idx)}, val n={len(val_idx)}")
        fold_compositions.append(_fold_composition(ds, fold_idx, train_idx, val_idx))
        fr = train_one_fold(
            fold_idx, ds.X, ds.y, ds.sample_ids, ds.phase1_indices, train_idx, val_idx
        )
        m = evaluation.fold_metrics(fr)
        fold_results.append(fr)
        per_fold_metrics.append(m)
        print(
            f"        f1_macro={m['f1_macro']:.3f}  "
            f"f1_minority={m['f1_minority']:.3f}  "
            f"roc_auc={m['roc_auc']}  "
            f"epochs={m['epochs']}"
        )

    agg = evaluation.aggregate(per_fold_metrics)

    # ---- 3. Persist -------------------------------------------------------
    pred_df = evaluation.to_cv_predictions_df(fold_results)
    pred_df.to_csv(config.CV_PREDICTIONS, index=False)
    print(f"[main] CV predictions -> {config.CV_PREDICTIONS}")
    _write_training_log(fold_results)

    payload = {
        "n_samples": int(len(ds.y)),
        "classes": ds.classes,
        "dataset_audit": _dataset_audit(ds),
        "split_strategy": config.SPLIT_STRATEGY,
        "cv_folds": config.CV_FOLDS,
        "fold_compositions": fold_compositions,
        "model_parameters": n_params,
        "metrics_aggregated": agg,
        "metrics_per_fold": per_fold_metrics,
        "phase2_reference": {
            "logreg_balanced_f1_macro": 0.978,
            "xgb_f1_macro": 0.972,
            "majority_floor_accuracy": 0.9187,
        },
        "config_snapshot": {
            "epochs": config.EPOCHS,
            "batch_size": config.BATCH_SIZE,
            "learning_rate": config.LEARNING_RATE,
            "augmentation_multiplicity": config.AUG_MULTIPLICITY,
            "class_weight_strategy": config.CLASS_WEIGHT_STRATEGY,
        },
    }
    with config.RESULTS_JSON.open("w") as f:
        json.dump(_serialise(payload), f, indent=2)
    print(f"[main] results -> {config.RESULTS_JSON}")

    # ---- 4. Figures -------------------------------------------------------
    print("[main] generating figures ...")
    viz.plot_training_curves(fold_results)
    viz.plot_confusion_matrices(per_fold_metrics)
    viz.plot_metric_summary(agg)

    print("\nPhase 3 complete. Inspect figures + results.json and approve "
          "to start Phase 4 (comparative academic report).")


if __name__ == "__main__":
    main()

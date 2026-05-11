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

import numpy as np

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
    for fold_idx, (train_idx, val_idx) in enumerate(loader.iter_splits(ds)):
        print(f"[main] fold {fold_idx} — train n={len(train_idx)}, val n={len(val_idx)}")
        fr = train_one_fold(fold_idx, ds.X, ds.y, ds.sample_ids, train_idx, val_idx)
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

    payload = {
        "n_samples": int(len(ds.y)),
        "split_strategy": config.SPLIT_STRATEGY,
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

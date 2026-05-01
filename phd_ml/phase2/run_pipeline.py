"""Phase 2 orchestrator.

Run with:
    python -m phd_ml.phase2.run_pipeline

Outputs:
    data/phd_ml/phase2/results.json           — per-fold + aggregated metrics
    data/phd_ml/phase2/cv_predictions.csv     — held-out predictions
    data/phd_ml/phase2/feature_importance.csv — native + permutation importance
    figures/phd_ml/phase2/*.png               — five diagnostic figures
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from . import config, importance, viz
from .evaluation import collect_cv_predictions, cross_validate
from .loader import load_supervised, majority_baseline_accuracy
from .models import build_models


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
    print("Phase 2 — Traditional baselines with imbalance handling")
    print("=" * 72)

    # ---- 1. Load Phase-1 labels ------------------------------------------
    ds = load_supervised()
    floor = majority_baseline_accuracy(ds.y)
    print(f"[main] Majority-class accuracy floor: {floor:.4f} "
          f"(any model below this is uninformative)")

    # ---- 2. Build the model lineup ---------------------------------------
    specs = build_models(ds.y)
    print(f"[main] Models in lineup: {[s.name for s in specs]}")

    # ---- 3. Cross-validate every model -----------------------------------
    cv_results = []
    for spec in specs:
        print(f"[main] Cross-validating {spec.name} ...")
        try:
            r = cross_validate(spec, ds.X, ds.y)
        except Exception as e:
            print(f"[main]   FAILED: {e}")
            continue
        cv_results.append(r)
        agg = r.metrics_aggregated
        print(
            f"        f1_macro    = {agg.get('f1_macro_mean', float('nan')):.3f} "
            f"± {agg.get('f1_macro_std', 0):.3f}"
        )
        print(
            f"        f1_minority = {agg.get('f1_minority_mean', float('nan')):.3f} "
            f"± {agg.get('f1_minority_std', 0):.3f}"
        )
        if agg.get("roc_auc_mean") is not None:
            print(
                f"        roc_auc     = {agg['roc_auc_mean']:.3f} "
                f"± {agg.get('roc_auc_std', 0):.3f}"
            )

    # ---- 4. Persist held-out predictions ---------------------------------
    pred_df = collect_cv_predictions(cv_results)
    pred_df.to_csv(config.CV_PREDICTIONS, index=False)
    print(f"[main] CV predictions -> {config.CV_PREDICTIONS}")

    # ---- 5. Feature importance -------------------------------------------
    print("[main] Computing feature importance (native + permutation) ...")
    fi_df = importance.importance_for_models(
        specs, ds.X, ds.y, ds.feature_names,
    )
    fi_df.to_csv(config.FEATURE_IMPORTANCE, index=False)
    print(f"[main] Feature importance -> {config.FEATURE_IMPORTANCE}")

    # ---- 6. Figures ------------------------------------------------------
    print("[main] Generating figures ...")
    viz.plot_confusion_matrices(cv_results)
    viz.plot_roc_curves(cv_results)
    viz.plot_pr_curves(cv_results)
    viz.plot_metric_comparison(cv_results)
    viz.plot_feature_importance(fi_df)

    # ---- 7. Persist metrics ----------------------------------------------
    payload = {
        "n_samples": int(len(ds.y)),
        "majority_class_accuracy": floor,
        "feature_columns": ds.feature_names,
        "models": [
            {
                "name": r.name, "family": r.family, "strategy": r.strategy,
                "notes": r.notes,
                "metrics_aggregated": r.metrics_aggregated,
                "metrics_per_fold": r.metrics_per_fold,
            }
            for r in cv_results
        ],
    }
    with config.RESULTS_JSON.open("w") as f:
        json.dump(_serialise(payload), f, indent=2)
    print(f"[main] Results -> {config.RESULTS_JSON}")

    print("\nPhase 2 complete. Inspect figures + results.json and approve "
          "to start Phase 3 (1D-CNN).")


if __name__ == "__main__":
    main()

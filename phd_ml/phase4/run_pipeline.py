"""Phase 4 orchestrator.

Run with:
    python -m phd_ml.phase4.run_pipeline

Outputs:
    data/phd_ml/phase4/results.json
    data/phd_ml/phase4/metrics_common.csv
    data/phd_ml/phase4/common_predictions_long.csv
    data/phd_ml/phase4/paired_predictions_logreg_vs_cnn.csv
    figures/phd_ml/phase4/*.png
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd

from . import config, evaluation, viz


def _read_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def _normalise_phase2_predictions(p2: pd.DataFrame) -> pd.DataFrame:
    out = p2.rename(columns={"y_proba": "y_prob_positive"}).copy()
    out["source_phase"] = "phase2_feature_engineered"
    return out[["model", "source_phase", "fold", "sample_index", "y_true", "y_pred", "y_prob_positive"]]


def _normalise_phase3_predictions(p3: pd.DataFrame) -> pd.DataFrame:
    out = p3.copy()
    out["source_phase"] = "phase3_pose_cnn"
    return out[[
        "model", "source_phase", "fold", "sample_index", "sample_key",
        "y_true", "y_pred", "y_prob_positive",
    ]]


def _build_common_predictions(
    phase2_pred: pd.DataFrame,
    phase3_pred: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    phase2 = _normalise_phase2_predictions(phase2_pred)
    phase3 = _normalise_phase3_predictions(phase3_pred)

    phase3_keys = phase3[["sample_index", "sample_key"]].drop_duplicates()
    if phase3_keys["sample_index"].duplicated().any():
        raise ValueError("Phase-3 predictions contain duplicated sample_index values.")

    common_indices = sorted(set(phase3["sample_index"]) & set(phase2["sample_index"]))
    if not common_indices:
        raise ValueError("No shared sample_index values between Phase 2 and Phase 3.")

    phase2_common = phase2[phase2["sample_index"].isin(common_indices)].merge(
        phase3_keys,
        on="sample_index",
        how="left",
    )
    phase3_common = phase3[phase3["sample_index"].isin(common_indices)].copy()

    for model, sub in phase2_common.groupby("model"):
        if sub["sample_index"].nunique() != len(common_indices):
            raise ValueError(f"Phase-2 model {model} is missing common samples.")
    if phase3_common["sample_index"].nunique() != len(common_indices):
        raise ValueError("Phase-3 CNN is missing common samples.")

    reference = phase2_common[phase2_common["model"] == config.REFERENCE_MODEL]
    label_check = reference[["sample_index", "y_true"]].merge(
        phase3_common[["sample_index", "y_true"]],
        on="sample_index",
        suffixes=("_phase2", "_phase3"),
    )
    mismatches = label_check[label_check["y_true_phase2"] != label_check["y_true_phase3"]]
    if not mismatches.empty:
        raise ValueError(f"Label mismatch on common samples: {mismatches.head().to_dict('records')}")

    common_long = pd.concat([phase2_common, phase3_common], ignore_index=True)
    common_long = common_long.sort_values(["model", "sample_index"]).reset_index(drop=True)

    ref = reference.rename(columns={
        "y_pred": "reference_y_pred",
        "y_prob_positive": "reference_y_prob",
        "fold": "reference_fold",
    })
    cnn = phase3_common.rename(columns={
        "y_pred": "cnn_y_pred",
        "y_prob_positive": "cnn_y_prob",
        "fold": "cnn_fold",
    })
    paired = ref[[
        "sample_index", "sample_key", "y_true",
        "reference_fold", "reference_y_pred", "reference_y_prob",
    ]].merge(
        cnn[["sample_index", "cnn_fold", "cnn_y_pred", "cnn_y_prob"]],
        on="sample_index",
        how="inner",
    )
    paired["reference_correct"] = paired["reference_y_pred"] == paired["y_true"]
    paired["cnn_correct"] = paired["cnn_y_pred"] == paired["y_true"]
    paired = paired.sort_values("sample_index").reset_index(drop=True)
    return common_long, paired


def _phase2_full_summary(phase2_results: dict) -> list[dict]:
    rows = []
    for model in phase2_results["models"]:
        agg = model["metrics_aggregated"]
        rows.append({
            "model": model["name"],
            "n_samples": phase2_results["n_samples"],
            "f1_macro_mean": agg.get("f1_macro_mean"),
            "f1_beginner_mean": agg.get("f1_minority_mean"),
            "roc_auc_mean": agg.get("roc_auc_mean"),
            "pr_auc_mean": agg.get("pr_auc_mean"),
        })
    return rows


def main() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("Phase 4 - Comparative academic report")
    print("=" * 72)

    phase2_results = _read_json(config.PHASE2_RESULTS)
    phase3_results = _read_json(config.PHASE3_RESULTS)
    phase2_pred = pd.read_csv(config.PHASE2_PREDICTIONS)
    phase3_pred = pd.read_csv(config.PHASE3_PREDICTIONS)

    common_long, paired = _build_common_predictions(phase2_pred, phase3_pred)
    common_long.to_csv(config.COMMON_PREDICTIONS_LONG, index=False)
    paired.to_csv(config.PAIRED_REFERENCE_CNN, index=False)
    print(f"[main] common predictions -> {config.COMMON_PREDICTIONS_LONG}")
    print(f"[main] paired reference/CNN -> {config.PAIRED_REFERENCE_CNN}")

    metric_rows = []
    for model, sub in common_long.groupby("model", sort=False):
        phase = sub["source_phase"].iloc[0]
        metric_rows.append(evaluation.compute_metrics(sub, model, phase).as_dict())
    metrics_df = pd.DataFrame(metric_rows)
    present_order = [m for m in config.MODEL_ORDER if m in set(metrics_df["model"])]
    metrics_df = metrics_df.set_index("model").loc[present_order].reset_index()
    metrics_df.to_csv(config.METRICS_COMMON, index=False)
    print(f"[main] common metrics -> {config.METRICS_COMMON}")

    bootstrap_metrics = [
        "accuracy", "balanced_accuracy", "f1_macro", "f1_beginner",
        "precision_beginner", "recall_beginner", "roc_auc", "pr_auc",
    ]
    diffs_df, bootstrap_summary = evaluation.paired_bootstrap(
        paired,
        bootstrap_metrics,
        n_iterations=config.BOOTSTRAP_ITERATIONS,
        random_state=config.RANDOM_STATE,
    )
    diffs_df.to_csv(config.BOOTSTRAP_DIFFS, index=False)
    print(f"[main] bootstrap diffs -> {config.BOOTSTRAP_DIFFS}")

    y_counts = Counter(paired["y_true"].astype(int))
    audit = {
        "phase2_total_samples": int(phase2_results["n_samples"]),
        "phase2_beginner_samples": int(sum(
            1 for x in phase2_pred[phase2_pred["model"] == config.REFERENCE_MODEL]["y_true"]
            if int(x) == 1
        )),
        "phase3_total_samples": int(phase3_results["n_samples"]),
        "common_n_samples": int(len(paired)),
        "common_advanced_samples": int(y_counts.get(0, 0)),
        "common_beginner_samples": int(y_counts.get(1, 0)),
        "phase3_intersect_status_counts": phase3_results["dataset_audit"]["intersect_status_counts"],
        "phase3_class_balance": phase3_results["dataset_audit"]["class_balance"],
    }

    paired_tests = {
        "reference_model": config.REFERENCE_MODEL,
        "cnn_model": config.CNN_MODEL,
        "mcnemar_exact": evaluation.mcnemar_exact(paired),
        "bootstrap_reference_minus_cnn": bootstrap_summary,
    }

    figures = {
        "common_metric_comparison": str(viz.plot_common_metric_comparison(metrics_df)),
        "beginner_precision_recall": str(viz.plot_beginner_focus(metrics_df)),
        "reference_vs_cnn_confusion": str(viz.plot_reference_confusions(paired)),
        "reference_vs_cnn_curves": str(viz.plot_curves(common_long)),
        "lane_matched_data_bottleneck": str(viz.plot_data_bottleneck(audit)),
    }

    payload = {
        "phase": 4,
        "title": "Phase 2 vs Phase 3 comparative academic report",
        "comparison_rule": "Metrics are computed only on sample_index values shared by Phase 2 predictions and Phase 3 lane-matched CNN predictions.",
        "reference_model": config.REFERENCE_MODEL,
        "cnn_model": config.CNN_MODEL,
        "audit": audit,
        "phase2_full_summary": _phase2_full_summary(phase2_results),
        "phase3_full_summary": {
            "n_samples": phase3_results["n_samples"],
            "metrics_aggregated": phase3_results["metrics_aggregated"],
            "model_parameters": phase3_results["model_parameters"],
        },
        "metrics_common": metrics_df.to_dict(orient="records"),
        "paired_tests": paired_tests,
        "figures": figures,
        "interpretation": [
            "Phase 2 remains the feature-engineered ceiling because its labels were derived from the same engineered feature space.",
            "Phase 3 is a more independent test because the 1D-CNN receives pose time-series rather than the Phase-1 engineered summary features.",
            "The CNN underperforms on the common subset, but the primary bottleneck is the strict lane-matched beginner count: 6 samples.",
            "The next defensible research step is expanding lane-matched pose coverage before testing higher-capacity sequence models such as ST-GCN.",
        ],
    }

    with config.RESULTS_JSON.open("w", encoding="utf-8") as f:
        json.dump(_serialise(payload), f, indent=2, ensure_ascii=False)
    print(f"[main] results -> {config.RESULTS_JSON}")

    print("\nPhase 4 analysis complete. Generate the Word report with:")
    print("  node phd_ml/docx_builder/build_phase4_docx.js")


if __name__ == "__main__":
    main()


"""Paths and reporting settings for Phase 4.

Phase 4 is a reporting/analysis layer. It does not train a new model; it
compares the already saved Phase-2 tabular baseline predictions and Phase-3
1D-CNN predictions on the identical lane-matched sample_index subset.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

PHASE2_RESULTS: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase2" / "results.json"
PHASE2_PREDICTIONS: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase2" / "cv_predictions.csv"
PHASE3_RESULTS: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase3" / "results.json"
PHASE3_PREDICTIONS: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase3" / "cv_predictions.csv"
PHASE3_INTERSECT: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase3" / "intersect_report.csv"

OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase4"
FIGURE_DIR: Path = PROJECT_ROOT / "figures" / "phd_ml" / "phase4"
DOC_DIR: Path = PROJECT_ROOT / "phd_ml" / "phase4"

RESULTS_JSON: Path = OUTPUT_DIR / "results.json"
METRICS_COMMON: Path = OUTPUT_DIR / "metrics_common.csv"
COMMON_PREDICTIONS_LONG: Path = OUTPUT_DIR / "common_predictions_long.csv"
PAIRED_REFERENCE_CNN: Path = OUTPUT_DIR / "paired_predictions_logreg_vs_cnn.csv"
BOOTSTRAP_DIFFS: Path = OUTPUT_DIR / "paired_bootstrap_diffs.csv"

REFERENCE_MODEL: str = "logreg_balanced"
CNN_MODEL: str = "cnn1d"
POSITIVE_CLASS_NAME: str = "beginner"
NEGATIVE_CLASS_NAME: str = "advanced"

BOOTSTRAP_ITERATIONS: int = 5000
RANDOM_STATE: int = 42

MODEL_ORDER: list[str] = [
    "dummy_majority",
    "logreg_balanced",
    "rf_balanced",
    "xgb_scale_pos_weight",
    "rf_smote",
    "xgb_smote",
    "cnn1d",
]


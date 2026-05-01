"""Paths, hyperparameters, and feature lists for Phase 2.

Phase 2 takes the labeled dataset produced by Phase 1 and trains
class-imbalance-aware supervised baselines (Random Forest, XGBoost) plus
weaker references (Dummy, Logistic Regression) for committee comparison.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

PHASE1_LABELED: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase1" / "labeled_dataset.csv"

OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase2"
FIGURE_DIR: Path = PROJECT_ROOT / "figures" / "phd_ml" / "phase2"

RESULTS_JSON: Path = OUTPUT_DIR / "results.json"
CV_PREDICTIONS: Path = OUTPUT_DIR / "cv_predictions.csv"
FEATURE_IMPORTANCE: Path = OUTPUT_DIR / "feature_importance.csv"

# ---------------------------------------------------------------------------
# Target column from Phase 1
# ---------------------------------------------------------------------------
# Phase 1 selected K-Means k*=2 with strong cross-method agreement
# (ARI 0.85 vs Hierarchical). The ordinal label column produced is
# "cluster_kmeans_label" with values {"beginner", "advanced"}.
TARGET_COLUMN: str = "cluster_kmeans_label"
POSITIVE_CLASS: str = "beginner"  # minority class (n=20) — focus of recall

# ---------------------------------------------------------------------------
# Feature columns (15 camera-independent — same set used by Phase 1)
# ---------------------------------------------------------------------------
POSTURAL_FEATURES: list[str] = [
    "post_avg_knee_angle",
    "post_knee_angle_std",
    "post_avg_elbow_angle",
    "post_elbow_angle_std",
    "post_avg_body_lean",
    "post_body_lean_std",
    "post_hip_width_ratio",
    "post_avg_reach_ratio",
    "post_max_reach_ratio",
]
FREQUENCY_FEATURES: list[str] = [
    "freq_limb_sync_ratio",
    "freq_hand_movement_amplitude",
    "freq_foot_movement_amplitude",
    "freq_foot_frequency_hz",
    "freq_hand_frequency_hz",
    "freq_movement_regularity",
]
FEATURE_COLUMNS: list[str] = POSTURAL_FEATURES + FREQUENCY_FEATURES

# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------
# StratifiedKFold preserves the 226/20 ratio inside each fold.
# 5 folds chosen because 20/5 = 4 minority samples per fold (workable).
CV_FOLDS: int = 5
RANDOM_STATE: int = 42

# ---------------------------------------------------------------------------
# Model hyperparameters (deliberately conservative — tuning belongs to a
# later "model selection" study, not the baseline phase)
# ---------------------------------------------------------------------------
RF_PARAMS: dict = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_leaf": 2,
    "n_jobs": -1,
    "random_state": RANDOM_STATE,
}

XGB_PARAMS: dict = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "eval_metric": "logloss",
    "tree_method": "hist",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}

LR_PARAMS: dict = {
    "max_iter": 2000,
    "solver": "lbfgs",
    "random_state": RANDOM_STATE,
}

# ---------------------------------------------------------------------------
# SMOTE
# ---------------------------------------------------------------------------
# k_neighbors must be < n_minority_per_fold. With 20/5 = 4 per fold,
# we set k_neighbors = 3 (the smallest meaningful value).
SMOTE_PARAMS: dict = {
    "k_neighbors": 3,
    "random_state": RANDOM_STATE,
}

# ---------------------------------------------------------------------------
# Permutation importance
# ---------------------------------------------------------------------------
PERM_REPEATS: int = 30

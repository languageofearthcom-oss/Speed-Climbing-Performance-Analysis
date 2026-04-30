"""Paths, feature lists, and constants for Phase 1.

Centralising configuration keeps the rest of the pipeline reproducible and
easy to audit by the thesis committee.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "data"
INPUT_CSV: Path = DATA_DIR / "ml_dataset" / "all_features.csv"

OUTPUT_DIR: Path = DATA_DIR / "phd_ml" / "phase1"
FIGURE_DIR: Path = PROJECT_ROOT / "figures" / "phd_ml" / "phase1"

LABELED_DATASET: Path = OUTPUT_DIR / "labeled_dataset.csv"
METRICS_JSON: Path = OUTPUT_DIR / "cluster_metrics.json"
SKILL_REPORT: Path = OUTPUT_DIR / "skill_proxy_report.csv"

# ---------------------------------------------------------------------------
# Quality filtering
# ---------------------------------------------------------------------------
# MASTER_CONTEXT.md: 371 raw samples -> 246 high-quality at threshold 0.8
QUALITY_THRESHOLD: float = 0.80

# ---------------------------------------------------------------------------
# Feature lists
# ---------------------------------------------------------------------------
# Camera-independent features (kept by the project per MASTER_CONTEXT).
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

CLUSTERING_FEATURES: list[str] = POSTURAL_FEATURES + FREQUENCY_FEATURES

# Camera-dependent features explicitly excluded (kept here for documentation).
EXCLUDED_FEATURES: list[str] = [
    "eff_acceleration_variance",
    "eff_com_stability_index",
    "eff_lateral_movement_ratio",
    "eff_movement_smoothness",
    "eff_path_straightness",
    "eff_vertical_progress_rate",
]

# ---------------------------------------------------------------------------
# Clustering hyperparameter search
# ---------------------------------------------------------------------------
K_RANGE: tuple[int, int] = (2, 8)
RANDOM_STATE: int = 42
BOOTSTRAP_ITERS: int = 100
BOOTSTRAP_FRAC: float = 0.80
DBSCAN_EPS_GRID: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
DBSCAN_MIN_SAMPLES_GRID: tuple[int, ...] = (3, 5, 8)

"""Paths, hyperparameters, and feature shapes for Phase 3.

Phase 3 trains a 1D-CNN on the BlazePose time-series produced by the
project's pose-extraction pipeline. Inputs are sequences of 33 landmarks
(x, y, z, visibility) per frame; targets are the same Phase-1 K-Means
labels used by Phase 2 so the two baselines are paired by sample_index.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

PHASE1_LABELED: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase1" / "labeled_dataset.csv"
PHASE2_PREDICTIONS: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase2" / "cv_predictions.csv"

# Pose source directories — loader inspects both schemas (see loader.py).
POSE_DIR_SINGLE: Path = PROJECT_ROOT / "data" / "processed" / "poses" / "single_athlete"
POSE_DIR_DUAL_SAMPLES: Path = PROJECT_ROOT / "data" / "processed" / "poses" / "samples"

OUTPUT_DIR: Path = PROJECT_ROOT / "data" / "phd_ml" / "phase3"
FIGURE_DIR: Path = PROJECT_ROOT / "figures" / "phd_ml" / "phase3"

RESULTS_JSON: Path = OUTPUT_DIR / "results.json"
CV_PREDICTIONS: Path = OUTPUT_DIR / "cv_predictions.csv"
INTERSECT_REPORT: Path = OUTPUT_DIR / "intersect_report.csv"
TRAINING_LOG: Path = OUTPUT_DIR / "training_log.csv"

# ---------------------------------------------------------------------------
# Target column from Phase 1 — same as Phase 2 (paired comparison)
# ---------------------------------------------------------------------------
TARGET_COLUMN: str = "cluster_kmeans_label"
POSITIVE_CLASS: str = "beginner"

# ---------------------------------------------------------------------------
# Input shape
# ---------------------------------------------------------------------------
N_LANDMARKS: int = 33                       # MediaPipe BlazePose
CHANNELS_PER_LANDMARK: int = 3              # (x, y, z) — visibility used for masking
TARGET_SEQUENCE_LENGTH: int = 200           # uniform length after resampling

# Visibility threshold for masking unreliable landmarks (per-frame).
VISIBILITY_THRESHOLD: float = 0.3

# ---------------------------------------------------------------------------
# Cross-validation — paired with Phase 2
# ---------------------------------------------------------------------------
# Default StratifiedKFold for parity with Phase 2 (random state pinned to 42
# matches `phd_ml.phase2.config.RANDOM_STATE`). We use three folds by default
# because only 6 beginner examples survive strict lane-matched pose intersect.
# Three folds leaves two beginner examples per validation fold; five folds is
# too brittle for a neural model.
CV_FOLDS: int = int(os.getenv("PHASE3_CV_FOLDS", "3"))
RANDOM_STATE: int = 42

# Set to "subject_aware" to split by athlete (held-out person never seen at
# training), "competition_aware" to split by event, or "stratified" for parity
# with Phase 2. Loader emits a deprecation warning if "stratified" is chosen
# and reminds the reader the Phase-2 caveat applies (labels ⇄ features by
# design, so random fold CV cannot distinguish memorisation from learning).
SPLIT_STRATEGY: str = os.getenv("PHASE3_SPLIT_STRATEGY", "stratified")

# ---------------------------------------------------------------------------
# 1D-CNN architecture (deliberately lean — < 100k parameters)
# ---------------------------------------------------------------------------
CONV_CHANNELS: tuple[int, ...] = (48, 96, 96)
CONV_KERNELS: tuple[int, ...] = (5, 5, 3)
DROPOUT: float = 0.3
DENSE_HIDDEN: int = 48

# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
BATCH_SIZE: int = int(os.getenv("PHASE3_BATCH_SIZE", "32"))
EPOCHS: int = int(os.getenv("PHASE3_EPOCHS", "20"))
LEARNING_RATE: float = 1e-3
WEIGHT_DECAY: float = 1e-4
LR_SCHEDULE: str = "cosine"
EARLY_STOPPING_PATIENCE: int = int(os.getenv("PHASE3_EARLY_STOPPING_PATIENCE", "6"))
GRADIENT_CLIP: float = 1.0

# Class-imbalance handling — Phase-2 logreg results say cost-sensitive is the
# strongest strategy on this label set; we mirror it here so the CNN sees the
# same recipe by default. SMOTE is intentionally NOT used on time-series (the
# synthetic samples are kinematically implausible).
CLASS_WEIGHT_STRATEGY: str = "inverse_frequency"   # "inverse_frequency" | "none"

# ---------------------------------------------------------------------------
# Augmentation parameters (Phase 3.3 in the rationale)
# ---------------------------------------------------------------------------
AUG_GAUSSIAN_NOISE_STD: float = 0.01           # in normalised landmark units
AUG_TIME_WARP_RATIO: float = 0.15              # ±15% temporal scale
AUG_MIRROR_PROBABILITY: float = 0.5            # left/right flip via landmark swap
AUG_MULTIPLICITY: int = int(os.getenv("PHASE3_AUG_MULTIPLICITY", "3"))  # virtual replicas per training sample

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
TORCH_DETERMINISTIC: bool = True

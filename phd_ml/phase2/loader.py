"""Load the Phase-1 labeled dataset and return a tidy supervised problem.

Phase 1 produced data/phd_ml/phase1/labeled_dataset.csv with the kinematic
features and the ordinal pseudo-labels. Phase 2 imports this directly — the
two phases share their feature space by design so the baselines and the
later 1D-CNN are evaluated against the same supervision target.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config


@dataclass
class SupervisedDataset:
    X: np.ndarray
    y: np.ndarray              # binary {0, 1} with 1 = POSITIVE_CLASS (minority)
    feature_names: list[str]
    classes: list[str]         # ordered [majority, minority] -> ["advanced", "beginner"]
    raw: pd.DataFrame
    pos_label: int             # always 1 by construction


def load_supervised() -> SupervisedDataset:
    if not config.PHASE1_LABELED.exists():
        raise FileNotFoundError(
            f"Phase-1 labeled dataset not found at {config.PHASE1_LABELED}. "
            "Run `python -m phd_ml.phase1.run_pipeline` first."
        )

    df = pd.read_csv(config.PHASE1_LABELED)
    if config.TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column '{config.TARGET_COLUMN}' in dataset.")

    missing = [c for c in config.FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    X = df[config.FEATURE_COLUMNS].to_numpy(dtype=float)
    y_raw = df[config.TARGET_COLUMN].to_numpy()

    # Binary encoding with an explicit positive class (the minority).
    classes = sorted(np.unique(y_raw).tolist(), key=lambda c: c == config.POSITIVE_CLASS)
    # `classes` is now ["advanced", "beginner"] -> majority first, minority second.
    label_to_int = {classes[0]: 0, classes[1]: 1}
    y = np.array([label_to_int[v] for v in y_raw], dtype=int)

    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    print(
        f"[loader] {len(df)} samples loaded. "
        f"Class balance: {classes[0]} (0) = {n_neg}, "
        f"{classes[1]} (1) = {n_pos}. "
        f"Positive (minority) class = '{config.POSITIVE_CLASS}'."
    )

    return SupervisedDataset(
        X=X, y=y, feature_names=list(config.FEATURE_COLUMNS),
        classes=classes, raw=df, pos_label=1,
    )


def majority_baseline_accuracy(y: np.ndarray) -> float:
    """The ceiling-of-uselessness: predicting the majority class for everyone."""
    counts = np.bincount(y)
    return float(counts.max() / counts.sum())

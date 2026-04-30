"""Data loading and quality filtering for Phase 1.

The input is the project's main feature CSV produced by the existing pipeline
(`scripts/export_ml_data.py`). This module:
  1. loads the CSV,
  2. applies the documented quality threshold,
  3. selects the camera-independent feature columns,
  4. returns standardised (z-score) features for downstream clustering,
plus the raw subset for later attribution.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from . import config


@dataclass
class LoadedDataset:
    raw: pd.DataFrame
    features_standardised: np.ndarray
    feature_names: list[str]
    scaler: StandardScaler


def load_features() -> LoadedDataset:
    """Load the all-features CSV, filter for quality, return tidy structures."""
    if not config.INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input CSV not found at {config.INPUT_CSV}. "
            "Run the existing feature extraction pipeline first."
        )

    df = pd.read_csv(config.INPUT_CSV)

    missing = [c for c in config.CLUSTERING_FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"Required feature columns missing from CSV: {missing}")

    n_before = len(df)
    df = df.dropna(subset=config.CLUSTERING_FEATURES + ["extraction_quality"])
    df = df[df["extraction_quality"] >= config.QUALITY_THRESHOLD].reset_index(drop=True)
    n_after = len(df)
    print(
        f"[loader] Quality filter ({config.QUALITY_THRESHOLD}): "
        f"{n_before} -> {n_after} samples"
    )

    X = df[config.CLUSTERING_FEATURES].to_numpy(dtype=float)
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    return LoadedDataset(
        raw=df,
        features_standardised=X_std,
        feature_names=list(config.CLUSTERING_FEATURES),
        scaler=scaler,
    )

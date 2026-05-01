"""Model factory — six configurations spanning two strategies.

Why these six?
  Strategy A (cost-sensitive learning): 3 models with class weighting.
  Strategy B (resampling)              : 2 models pre-trained on SMOTE-augmented data.
  Sanity floor                         : DummyClassifier(most_frequent).

Returning fresh instances per call lets the cross-validation loop reset
state cleanly between folds without sharing fitted internals.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import config

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


@dataclass
class ModelSpec:
    name: str
    family: str          # "linear", "tree", "boost", "dummy"
    strategy: str        # "cost_sensitive", "smote", "none"
    needs_smote: bool
    factory: Callable    # () -> sklearn-compatible estimator
    notes: str = ""


def _scale_pos_weight(y: np.ndarray) -> float:
    """XGBoost imbalance knob. Returns n_negative / n_positive."""
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    return float(n_neg / max(n_pos, 1))


def build_models(y_full: np.ndarray) -> list[ModelSpec]:
    """Build the canonical six-model lineup.

    `y_full` is the full label vector — needed only to compute
    XGBoost's `scale_pos_weight` from the global ratio (XGBoost
    documentation recommends the global ratio rather than per-fold).
    """
    spw = _scale_pos_weight(y_full)
    print(f"[models] XGBoost scale_pos_weight = {spw:.2f}")

    specs: list[ModelSpec] = []

    # ---- Sanity floor -----------------------------------------------------
    specs.append(ModelSpec(
        name="dummy_majority",
        family="dummy",
        strategy="none",
        needs_smote=False,
        factory=lambda: DummyClassifier(strategy="most_frequent"),
        notes="Predicts the majority class for every sample.",
    ))

    # ---- Strategy A: cost-sensitive --------------------------------------
    specs.append(ModelSpec(
        name="logreg_balanced",
        family="linear",
        strategy="cost_sensitive",
        needs_smote=False,
        factory=lambda: Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", **config.LR_PARAMS)),
        ]),
        notes="Linear baseline with balanced class weights.",
    ))
    specs.append(ModelSpec(
        name="rf_balanced",
        family="tree",
        strategy="cost_sensitive",
        needs_smote=False,
        factory=lambda: RandomForestClassifier(
            class_weight="balanced", **config.RF_PARAMS,
        ),
        notes="Random Forest with class_weight='balanced'.",
    ))
    if HAS_XGB:
        specs.append(ModelSpec(
            name="xgb_scale_pos_weight",
            family="boost",
            strategy="cost_sensitive",
            needs_smote=False,
            factory=lambda spw=spw: XGBClassifier(
                scale_pos_weight=spw, **config.XGB_PARAMS,
            ),
            notes=f"XGBoost with scale_pos_weight={spw:.2f}.",
        ))

    # ---- Strategy B: SMOTE resampling ------------------------------------
    # SMOTE is applied per-fold on the training split only, before fitting,
    # to avoid information leakage. The factory returns a vanilla model
    # because the resampling happens upstream in the CV harness.
    specs.append(ModelSpec(
        name="rf_smote",
        family="tree",
        strategy="smote",
        needs_smote=True,
        factory=lambda: RandomForestClassifier(**config.RF_PARAMS),
        notes="Random Forest trained on SMOTE-augmented training folds.",
    ))
    if HAS_XGB:
        specs.append(ModelSpec(
            name="xgb_smote",
            family="boost",
            strategy="smote",
            needs_smote=True,
            factory=lambda: XGBClassifier(**config.XGB_PARAMS),
            notes="XGBoost trained on SMOTE-augmented training folds.",
        ))

    return specs

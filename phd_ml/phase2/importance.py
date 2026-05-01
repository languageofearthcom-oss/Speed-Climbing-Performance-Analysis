"""Feature importance — native (tree-based) plus permutation.

Why two methods?
  Native impurity importance is fast but biased toward continuous and
  high-cardinality features. Permutation importance (Strobl et al., 2007;
  Breiman, 2001) is model-agnostic and robust on held-out data, at the
  cost of compute. We report both so the committee can compare.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold

from . import config
from .models import ModelSpec

try:
    from imblearn.over_sampling import SMOTE
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False


def _native_importance(estimator, feature_names: list[str]) -> dict | None:
    if hasattr(estimator, "feature_importances_"):
        imp = np.asarray(estimator.feature_importances_, dtype=float)
        return dict(zip(feature_names, imp.tolist()))
    if hasattr(estimator, "coef_"):
        imp = np.abs(np.asarray(estimator.coef_).ravel())
        return dict(zip(feature_names, imp.tolist()))
    return None


def importance_for_models(
    specs: list[ModelSpec],
    X: np.ndarray, y: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Return a long dataframe: model, method, feature, score, score_std.

    For permutation importance we average across CV folds so we have a
    standard deviation alongside the mean.
    """
    rows: list[dict] = []
    skf = StratifiedKFold(
        n_splits=config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE,
    )

    for spec in specs:
        if spec.family == "dummy":
            continue

        # ---- One full-data fit for native importance ---------------------
        # NOTE: native importance comes from a single full-data fit; permutation
        # importance below comes from 5-fold CV. The two regimes are different
        # by construction — figure captions in viz.py acknowledge this.
        full_model = spec.factory()
        if spec.needs_smote and HAS_IMBLEARN:
            X_tr, y_tr = SMOTE(**config.SMOTE_PARAMS).fit_resample(X, y)
        else:
            X_tr, y_tr = X, y
        full_model.fit(X_tr, y_tr)

        native = _native_importance(full_model, feature_names)
        if native is not None:
            for f, v in native.items():
                rows.append({"model": spec.name, "method": "native",
                             "feature": f, "score": v, "score_std": 0.0})

        # ---- Permutation importance, averaged across CV folds ------------
        # `random_state = base + fold_id` decorrelates the permutations across
        # folds so the per-fold std reflects data variability rather than a
        # repeated permutation pattern.
        per_feature_runs: dict[str, list[float]] = {f: [] for f in feature_names}
        for fold_id, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            model = spec.factory()
            X_tr2, y_tr2 = X[train_idx], y[train_idx]
            if spec.needs_smote and HAS_IMBLEARN:
                X_tr2, y_tr2 = SMOTE(**config.SMOTE_PARAMS).fit_resample(X_tr2, y_tr2)
            model.fit(X_tr2, y_tr2)
            r = permutation_importance(
                model, X[test_idx], y[test_idx],
                n_repeats=config.PERM_REPEATS,
                random_state=config.RANDOM_STATE + fold_id, n_jobs=-1,
                scoring="f1_macro",
            )
            for f, m in zip(feature_names, r.importances_mean):
                per_feature_runs[f].append(float(m))

        for f, vals in per_feature_runs.items():
            rows.append({
                "model": spec.name, "method": "permutation",
                "feature": f, "score": float(np.mean(vals)),
                "score_std": float(np.std(vals)),
            })

    return pd.DataFrame(rows)

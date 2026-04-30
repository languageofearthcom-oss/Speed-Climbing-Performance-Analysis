"""Skill proxy: convert nominal cluster IDs into ordinal pseudo-labels.

The proxy is a literature-grounded composite of camera-independent kinematic
indicators. Higher score is hypothesised to correspond to more advanced
technique. We then **rank clusters by mean proxy score** and assign ordinal
labels (Beginner / Intermediate / Advanced [/ Elite]).

This is *weak supervision*. We never claim the proxy IS skill — we claim it
is a defensible monotonic ordering that converts an unordered partition into
training signal usable by Phase 2 and Phase 3.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


SKILL_COMPONENTS: dict[str, int] = {
    # column                       sign (+1 = higher is better, -1 = lower is better)
    "post_knee_angle_std":         -1,
    "post_elbow_angle_std":        -1,
    "post_body_lean_std":          -1,
    "freq_limb_sync_ratio":        +1,
    "post_avg_reach_ratio":        +1,
    "freq_movement_regularity":    +1,
}

ORDINAL_LABELS_3: list[str] = ["beginner", "intermediate", "advanced"]
ORDINAL_LABELS_4: list[str] = ["beginner", "intermediate", "advanced", "elite"]


def compute_skill_score(df: pd.DataFrame) -> pd.Series:
    """Return a per-row composite z-score with documented direction."""
    parts = []
    for col, sign in SKILL_COMPONENTS.items():
        if col not in df.columns:
            raise ValueError(f"Skill-proxy column missing: {col}")
        z = stats.zscore(df[col].to_numpy(dtype=float), nan_policy="omit")
        parts.append(sign * np.asarray(z))
    score = np.nansum(np.vstack(parts), axis=0) / len(parts)
    return pd.Series(score, index=df.index, name="skill_score")


def assign_ordinal_labels(
    df: pd.DataFrame,
    cluster_col: str,
    score_col: str = "skill_score",
) -> pd.DataFrame:
    """Map cluster IDs to ordinal labels by ascending mean skill score.

    Returns a copy of df with new columns: `<cluster_col>_rank` and
    `<cluster_col>_label`.
    """
    cluster_means = (
        df.groupby(cluster_col)[score_col].mean().sort_values().reset_index()
    )
    n_clusters = len(cluster_means)
    if n_clusters <= 1:
        out = df.copy()
        out[f"{cluster_col}_rank"] = 0
        out[f"{cluster_col}_label"] = "single"
        return out

    label_set = ORDINAL_LABELS_4 if n_clusters >= 4 else ORDINAL_LABELS_3
    if n_clusters == 2:
        label_set = ["beginner", "advanced"]
    if n_clusters > len(label_set):
        # Fall back to ranked numeric labels if k exceeds our ordinal vocabulary.
        label_set = [f"level_{i+1}" for i in range(n_clusters)]

    rank_map = {row[cluster_col]: i for i, row in cluster_means.iterrows()}
    label_map = {cid: label_set[rank_map[cid]] for cid in cluster_means[cluster_col]}

    out = df.copy()
    out[f"{cluster_col}_rank"] = out[cluster_col].map(rank_map)
    out[f"{cluster_col}_label"] = out[cluster_col].map(label_map)
    return out


def cluster_skill_profile(df: pd.DataFrame, cluster_col: str) -> pd.DataFrame:
    """Per-cluster summary used in the thesis report."""
    grouped = df.groupby(cluster_col)
    summary = grouped["skill_score"].agg(["count", "mean", "std", "min", "max"])
    summary = summary.rename(columns={"count": "n_samples"}).reset_index()
    return summary

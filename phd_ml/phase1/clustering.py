"""Unsupervised clustering with methodological triangulation.

Four algorithms are run in parallel on the same standardised feature matrix:
  * K-Means        — spherical clusters, k chosen via elbow + silhouette
  * Gaussian Mixture — elliptical/probabilistic, k chosen via BIC
  * DBSCAN         — density-based, no k assumed
  * Agglomerative  — hierarchical, ward linkage, dendrogram for the thesis

Each algorithm returns a label vector. K-Means receives a bootstrap stability
check (mean Adjusted Rand Index across resamples) so the committee has an
explicit robustness number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture

from . import config


@dataclass
class ClusteringResult:
    name: str
    labels: np.ndarray
    n_clusters: int
    metrics: dict = field(default_factory=dict)
    extras: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _internal_metrics(X: np.ndarray, labels: np.ndarray) -> dict:
    """Compute the three standard internal validity indices.

    Defined only when at least two clusters exist and every sample has a
    label (DBSCAN noise points -1 are filtered out before the call).
    """
    unique = np.unique(labels)
    if len(unique) < 2:
        return {"silhouette": None, "davies_bouldin": None, "calinski_harabasz": None}
    return {
        "silhouette": float(silhouette_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
    }


# ---------------------------------------------------------------------------
# K-Means with elbow + silhouette
# ---------------------------------------------------------------------------

def kmeans_with_model_selection(X: np.ndarray) -> ClusteringResult:
    k_min, k_max = config.K_RANGE
    inertias: dict[int, float] = {}
    silhouettes: dict[int, float] = {}
    fitted: dict[int, KMeans] = {}

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=config.RANDOM_STATE)
        labels = km.fit_predict(X)
        inertias[k] = float(km.inertia_)
        silhouettes[k] = float(silhouette_score(X, labels))
        fitted[k] = km

    best_k = max(silhouettes, key=silhouettes.get)
    best_model = fitted[best_k]
    labels = best_model.labels_

    stability = _bootstrap_stability_kmeans(X, best_k)

    metrics = _internal_metrics(X, labels)
    metrics.update(
        {
            "best_k_by_silhouette": best_k,
            "silhouette_per_k": silhouettes,
            "inertia_per_k": inertias,
            "bootstrap_ari_mean": stability["mean"],
            "bootstrap_ari_std": stability["std"],
        }
    )
    return ClusteringResult(
        name="kmeans",
        labels=labels,
        n_clusters=best_k,
        metrics=metrics,
        extras={"centers": best_model.cluster_centers_.tolist()},
    )


def _bootstrap_stability_kmeans(X: np.ndarray, k: int) -> dict:
    """Mean ARI between the full-data K-Means labels and bootstrap resample labels."""
    rng = np.random.default_rng(config.RANDOM_STATE)
    n = X.shape[0]
    ref = KMeans(n_clusters=k, n_init=10, random_state=config.RANDOM_STATE).fit_predict(X)
    aris = []
    for _ in range(config.BOOTSTRAP_ITERS):
        idx = rng.choice(n, size=int(n * config.BOOTSTRAP_FRAC), replace=False)
        sub_labels = KMeans(
            n_clusters=k, n_init=5, random_state=rng.integers(0, 1_000_000)
        ).fit_predict(X[idx])
        aris.append(adjusted_rand_score(ref[idx], sub_labels))
    return {"mean": float(np.mean(aris)), "std": float(np.std(aris))}


# ---------------------------------------------------------------------------
# GMM with BIC / AIC
# ---------------------------------------------------------------------------

def gmm_with_model_selection(X: np.ndarray) -> ClusteringResult:
    k_min, k_max = config.K_RANGE
    bic: dict[int, float] = {}
    aic: dict[int, float] = {}
    fitted: dict[int, GaussianMixture] = {}

    for k in range(k_min, k_max + 1):
        gmm = GaussianMixture(
            n_components=k,
            covariance_type="full",
            random_state=config.RANDOM_STATE,
            max_iter=300,
        ).fit(X)
        bic[k] = float(gmm.bic(X))
        aic[k] = float(gmm.aic(X))
        fitted[k] = gmm

    best_k = min(bic, key=bic.get)
    best_model = fitted[best_k]
    labels = best_model.predict(X)
    metrics = _internal_metrics(X, labels)
    metrics.update(
        {
            "best_k_by_bic": best_k,
            "bic_per_k": bic,
            "aic_per_k": aic,
            "log_likelihood": float(best_model.score(X) * X.shape[0]),
        }
    )
    return ClusteringResult(
        name="gmm",
        labels=labels,
        n_clusters=best_k,
        metrics=metrics,
        extras={"means": best_model.means_.tolist()},
    )


# ---------------------------------------------------------------------------
# DBSCAN with grid search
# ---------------------------------------------------------------------------

def dbscan_with_grid_search(X: np.ndarray) -> ClusteringResult:
    best: tuple[float, dict, np.ndarray] | None = None
    grid_log: list[dict] = []

    for eps in config.DBSCAN_EPS_GRID:
        for min_samples in config.DBSCAN_MIN_SAMPLES_GRID:
            labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(X)
            mask = labels != -1
            entry = {
                "eps": eps,
                "min_samples": min_samples,
                "n_clusters": int(len(set(labels)) - (1 if -1 in labels else 0)),
                "n_noise": int((labels == -1).sum()),
            }
            if entry["n_clusters"] >= 2 and mask.sum() > 1:
                try:
                    sil = float(silhouette_score(X[mask], labels[mask]))
                    entry["silhouette"] = sil
                    if best is None or sil > best[0]:
                        best = (sil, entry, labels)
                except ValueError:
                    entry["silhouette"] = None
            else:
                entry["silhouette"] = None
            grid_log.append(entry)

    if best is None:
        # Density structure too weak — return a degenerate result honestly.
        labels = np.full(X.shape[0], -1, dtype=int)
        metrics = {"note": "DBSCAN found no valid clusters at any grid point.",
                   "grid": grid_log}
        return ClusteringResult(name="dbscan", labels=labels, n_clusters=0, metrics=metrics)

    _, best_params, labels = best
    mask = labels != -1
    metrics = _internal_metrics(X[mask], labels[mask])
    metrics.update({"best_params": best_params, "grid": grid_log,
                    "noise_fraction": float((~mask).mean())})
    return ClusteringResult(
        name="dbscan",
        labels=labels,
        n_clusters=int(len(set(labels)) - (1 if -1 in labels else 0)),
        metrics=metrics,
    )


# ---------------------------------------------------------------------------
# Hierarchical (Ward) — for the dendrogram in the thesis
# ---------------------------------------------------------------------------

def hierarchical_clustering(X: np.ndarray, n_clusters: int) -> ClusteringResult:
    model = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
    labels = model.fit_predict(X)
    return ClusteringResult(
        name="hierarchical",
        labels=labels,
        n_clusters=n_clusters,
        metrics=_internal_metrics(X, labels),
    )


# ---------------------------------------------------------------------------
# Cross-method agreement
# ---------------------------------------------------------------------------

def pairwise_ari(results: Iterable[ClusteringResult]) -> dict:
    results = [r for r in results if r.n_clusters >= 2 and -1 not in r.labels]
    out = {}
    for i, a in enumerate(results):
        for b in results[i + 1 :]:
            key = f"{a.name}_vs_{b.name}"
            out[key] = float(adjusted_rand_score(a.labels, b.labels))
    return out

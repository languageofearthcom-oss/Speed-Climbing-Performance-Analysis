"""Phase 1 orchestrator.

Run with:
    python -m phd_ml.phase1.run_pipeline

Outputs (paths defined in config.py):
    data/phd_ml/phase1/labeled_dataset.csv
    data/phd_ml/phase1/cluster_metrics.json
    data/phd_ml/phase1/skill_proxy_report.csv
    figures/phd_ml/phase1/*.png
"""
from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np
import pandas as pd

from . import clustering as cl
from . import config, skill_proxy, viz
from .loader import load_features


def _make_serialisable(obj):
    """JSON helper for numpy scalars and tuples."""
    if isinstance(obj, dict):
        return {str(k): _make_serialisable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_serialisable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def main() -> None:
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("Phase 1 — Auto-labeling")
    print("=" * 72)

    # ----- Stage 1: load + filter --------------------------------------------------
    ds = load_features()
    X = ds.features_standardised
    print(f"[main] Feature matrix: {X.shape}, "
          f"{len(ds.feature_names)} camera-independent features.")

    # ----- Stage 2: clustering -----------------------------------------------------
    print("[main] K-Means with model selection ...")
    res_km = cl.kmeans_with_model_selection(X)
    print(f"        best k = {res_km.n_clusters}, "
          f"silhouette = {res_km.metrics['silhouette']:.3f}, "
          f"bootstrap-ARI = {res_km.metrics['bootstrap_ari_mean']:.3f}")

    print("[main] GMM with BIC ...")
    res_gmm = cl.gmm_with_model_selection(X)
    print(f"        best k = {res_gmm.n_clusters}, BIC = "
          f"{res_gmm.metrics['bic_per_k'][res_gmm.n_clusters]:.1f}")

    print("[main] DBSCAN grid search ...")
    res_db = cl.dbscan_with_grid_search(X)
    print(f"        n_clusters = {res_db.n_clusters}, "
          f"noise_fraction = {res_db.metrics.get('noise_fraction', 0):.2f}")

    print("[main] Hierarchical (Ward) — using K-Means k* for comparability ...")
    res_h = cl.hierarchical_clustering(X, n_clusters=res_km.n_clusters)

    pairwise = cl.pairwise_ari([res_km, res_gmm, res_h])
    print(f"[main] Cross-method ARI: {pairwise}")

    # ----- Stage 3: skill proxy + ordinal labels ----------------------------------
    df_full = ds.raw.copy()
    df_full["skill_score"] = skill_proxy.compute_skill_score(df_full).values
    df_full["cluster_kmeans"] = res_km.labels
    df_full["cluster_gmm"] = res_gmm.labels
    df_full["cluster_dbscan"] = res_db.labels
    df_full["cluster_hierarchical"] = res_h.labels

    df_full = skill_proxy.assign_ordinal_labels(df_full, "cluster_kmeans")
    df_full = skill_proxy.assign_ordinal_labels(df_full, "cluster_gmm")
    df_full = skill_proxy.assign_ordinal_labels(df_full, "cluster_hierarchical")

    skill_report = skill_proxy.cluster_skill_profile(df_full, "cluster_kmeans")
    skill_report.to_csv(config.SKILL_REPORT, index=False)
    print(f"[main] Skill profile per K-Means cluster:\n{skill_report}")

    # ----- Stage 4: figures --------------------------------------------------------
    print("[main] Generating figures ...")
    viz.plot_elbow_kmeans(
        res_km.metrics["silhouette_per_k"], res_km.metrics["inertia_per_k"]
    )
    viz.plot_bic_gmm(res_gmm.metrics["bic_per_k"], res_gmm.metrics["aic_per_k"])
    viz.plot_dendrogram(X)
    viz.plot_embeddings(X, res_km.labels)
    viz.plot_skill_distribution(df_full, "cluster_kmeans")
    viz.plot_method_agreement(pairwise)

    # ----- Stage 5: persist outputs -----------------------------------------------
    df_full.to_csv(config.LABELED_DATASET, index=False)
    print(f"[main] Wrote labeled dataset -> {config.LABELED_DATASET}")

    metrics_dump = {
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "feature_names": ds.feature_names,
        "kmeans": _make_serialisable(asdict(res_km) | {"labels": None}),
        "gmm": _make_serialisable(asdict(res_gmm) | {"labels": None}),
        "dbscan": _make_serialisable(asdict(res_db) | {"labels": None}),
        "hierarchical": _make_serialisable(asdict(res_h) | {"labels": None}),
        "pairwise_ari": pairwise,
        "label_distribution_kmeans": (
            df_full["cluster_kmeans_label"].value_counts().to_dict()
        ),
    }
    with config.METRICS_JSON.open("w") as f:
        json.dump(metrics_dump, f, indent=2)
    print(f"[main] Wrote cluster metrics -> {config.METRICS_JSON}")

    print("\nPhase 1 complete. Inspect outputs and approve to start Phase 2.")


if __name__ == "__main__":
    main()

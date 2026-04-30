"""Diagnostic plots for Phase 1 (saved to figures/phd_ml/phase1/).

Plots produced
--------------
  1. elbow_kmeans.png             — inertia and silhouette vs k
  2. bic_gmm.png                  — BIC and AIC vs k
  3. dendrogram_ward.png          — hierarchical clustering tree
  4. embedding_pca.png            — 2D PCA scatter coloured by chosen label
  5. embedding_umap.png           — 2D UMAP scatter (if umap-learn installed)
  6. embedding_tsne.png           — 2D t-SNE scatter
  7. skill_score_distribution.png — boxplot of skill score per cluster
  8. method_agreement.png         — pairwise ARI between K-Means / GMM / Hier.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from . import config

try:
    import umap

    HAS_UMAP = True
except ImportError:  # pragma: no cover
    HAS_UMAP = False


def _ensure_dir() -> Path:
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    return config.FIGURE_DIR


def plot_elbow_kmeans(silhouettes: dict[int, float], inertias: dict[int, float]) -> Path:
    out = _ensure_dir() / "elbow_kmeans.png"
    ks = sorted(silhouettes)
    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.plot(ks, [inertias[k] for k in ks], "o-", color="C0", label="Inertia")
    ax1.set_xlabel("k")
    ax1.set_ylabel("Inertia (sum of squared distances)", color="C0")
    ax2 = ax1.twinx()
    ax2.plot(ks, [silhouettes[k] for k in ks], "s--", color="C3", label="Silhouette")
    ax2.set_ylabel("Silhouette score", color="C3")
    plt.title("K-Means: Elbow + Silhouette")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_bic_gmm(bic: dict[int, float], aic: dict[int, float]) -> Path:
    out = _ensure_dir() / "bic_gmm.png"
    ks = sorted(bic)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(ks, [bic[k] for k in ks], "o-", label="BIC")
    ax.plot(ks, [aic[k] for k in ks], "s--", label="AIC")
    ax.set_xlabel("k (number of components)")
    ax.set_ylabel("Information criterion (lower = better)")
    ax.legend()
    plt.title("Gaussian Mixture: BIC vs AIC")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_dendrogram(X: np.ndarray) -> Path:
    out = _ensure_dir() / "dendrogram_ward.png"
    Z = linkage(X, method="ward")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    dendrogram(Z, no_labels=True, color_threshold=None, ax=ax)
    ax.set_title("Hierarchical clustering (Ward) — full dendrogram")
    ax.set_xlabel("Samples")
    ax.set_ylabel("Distance")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def _scatter(emb: np.ndarray, labels: np.ndarray, title: str, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    palette = plt.colormaps["tab10"]
    for i, c in enumerate(sorted(set(labels))):
        mask = labels == c
        ax.scatter(emb[mask, 0], emb[mask, 1], s=22, alpha=0.8,
                   color=palette(i % 10), label=f"cluster {c}")
    ax.set_title(title)
    ax.set_xlabel("dim 1")
    ax.set_ylabel("dim 2")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_embeddings(X: np.ndarray, labels: np.ndarray) -> dict[str, Path]:
    out_dir = _ensure_dir()
    paths = {}
    pca = PCA(n_components=2, random_state=config.RANDOM_STATE).fit_transform(X)
    paths["pca"] = _scatter(pca, labels, "PCA (2D)", out_dir / "embedding_pca.png")

    perplexity = max(5, min(30, X.shape[0] // 5))
    tsne = TSNE(
        n_components=2, random_state=config.RANDOM_STATE, perplexity=perplexity, init="pca",
    ).fit_transform(X)
    paths["tsne"] = _scatter(tsne, labels, f"t-SNE (perplexity={perplexity})",
                             out_dir / "embedding_tsne.png")

    if HAS_UMAP:
        ump = umap.UMAP(n_components=2, random_state=config.RANDOM_STATE).fit_transform(X)
        paths["umap"] = _scatter(ump, labels, "UMAP (2D)",
                                 out_dir / "embedding_umap.png")
    else:
        print("[viz] umap-learn not installed — skipping UMAP plot.")
    return paths


def plot_skill_distribution(df: pd.DataFrame, cluster_col: str) -> Path:
    out = _ensure_dir() / "skill_score_distribution.png"
    fig, ax = plt.subplots(figsize=(7, 4.5))
    groups = [g["skill_score"].to_numpy() for _, g in df.groupby(cluster_col)]
    labels = list(df.groupby(cluster_col).groups.keys())
    ax.boxplot(groups, labels=[str(l) for l in labels], showmeans=True)
    ax.set_xlabel(cluster_col)
    ax.set_ylabel("Skill proxy score (z)")
    ax.set_title("Skill proxy distribution per cluster")
    ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_method_agreement(pairwise: dict[str, float]) -> Path | None:
    if not pairwise:
        return None
    out = _ensure_dir() / "method_agreement.png"
    fig, ax = plt.subplots(figsize=(6, 3.5))
    keys = list(pairwise.keys())
    vals = [pairwise[k] for k in keys]
    ax.barh(keys, vals)
    ax.set_xlim(-0.05, 1.05)
    ax.set_xlabel("Adjusted Rand Index")
    ax.set_title("Cross-method agreement (higher = more stable structure)")
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out

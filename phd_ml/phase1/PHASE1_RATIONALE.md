# Phase 1 — Methodological Rationale

> **Audience**: thesis advisor & dissertation committee.
> **Intent**: justify every methodological choice in terms a committee can challenge and a defender can answer.

---

## 1. Problem Statement

We hold 246 high-quality kinematic feature vectors extracted from IFSC speed-climbing performances using BlazePose + the project's existing pipeline. These vectors are **unlabeled**. Human labeling is excluded by project constraint. The Phase-1 question is:

> *Can a defensible ordinal label set be generated automatically from the data, so that supervised models in Phase 2 (Random Forest / XGBoost) and Phase 3 (1D-CNN) have a target variable?*

## 2. Why Unsupervised Discovery Is Defensible Here

Sport-biomechanics literature on movement-pattern discovery (Hofmann et al., 2017; Rein & Memmert, 2016; Federolf et al., 2014) treats the appearance of natural clusters in standardised kinematic feature space as **prima facie evidence of distinct technique modes**. We do not claim cluster membership = skill class; we claim cluster membership = a coherent technique mode that we then *order* using domain heuristics.

This is a textbook **weak supervision** workflow (Ratner et al., 2017):

```
unlabeled data  →  unsupervised structure discovery  →  domain-informed ranking  →  pseudo-labels
```

The thesis must (and will, in Phase 4) explicitly bound the validity of these labels — they are a *generating model* for downstream learning, not a measurement of true skill.

## 3. Methodological Triangulation

Rather than commit to a single algorithm, we run **four** in parallel and report agreement:

| Algorithm | Geometric assumption | k chosen by | Strength |
|-----------|---------------------|-------------|----------|
| K-Means | spherical, equal variance | Elbow + Silhouette | Standard reference |
| Gaussian Mixture | elliptical, full covariance | BIC (AIC reported) | Probabilistic; allows soft assignment |
| DBSCAN | density-based | Grid over (eps, min_samples) | No k assumption; finds noise |
| Agglomerative Ward | hierarchical | k* from K-Means | Dendrogram for thesis figure |

Convergence among these (high pairwise Adjusted Rand Index) is treated as evidence that the partition reflects real structure rather than algorithmic bias. Divergence is reported honestly.

## 4. Cluster Validity

Three internal validity indices are computed for every algorithm:

* **Silhouette Score** — separation/cohesion balance, higher is better.
* **Davies-Bouldin Index** — average cluster similarity, lower is better.
* **Calinski-Harabasz Score** — between/within variance ratio, higher is better.

A **bootstrap stability check** is run for K-Means: 100 iterations of 80% subsampling, computing ARI between subsample labels and full-data labels. The mean and standard deviation of the ARI are reported. We treat ARI ≥ 0.70 as "stable", 0.50–0.70 as "weakly stable", < 0.50 as "unstable" (Hennig, 2007).

## 5. Feature Selection — Camera-Independent Only

The project has already documented in `MASTER_CONTEXT.md` that six efficiency features are camera-motion artefacts and must not be used. We honour that constraint. The 15 retained features are:

* **Postural** (9): joint angles, joint-angle variability, body-lean, hip-width ratio, reach ratios.
* **Frequency** (6): limb-sync ratio, hand/foot amplitudes & frequencies, movement regularity.

Standardisation is z-score (`StandardScaler`). No feature engineering occurs at this stage; that is Phase 3's job for the temporal CNN.

## 6. Skill Proxy Score (Ordinal Conversion)

Cluster IDs are nominal. To produce an ordered label set we compute, per sample, a composite z-score:

```
SkillScore_i = mean over j ( sign_j * z(feature_j[i]) )
```

with components and signs:

| Feature | Direction | Biomechanical justification |
|---|---|---|
| `post_knee_angle_std` | − | Stable knee alignment is a marker of trained motor control. |
| `post_elbow_angle_std` | − | Stable upper-limb angles correlate with controlled pulls. |
| `post_body_lean_std` | − | Reduced trunk wobble is associated with elite climbers. |
| `freq_limb_sync_ratio` | + | Higher hand-foot synchronisation = better coordination. |
| `post_avg_reach_ratio` | + | Greater effective reach per cycle = larger move efficiency. |
| `freq_movement_regularity` | + | Periodic, non-erratic motion tracks skill. |

Per-cluster mean SkillScore induces a total order; clusters are then mapped onto ordinal labels (`beginner < intermediate < advanced` for k = 3, with a 4-class extension `… < elite` if the model selects k = 4). For k = 2 we use `beginner < advanced`.

We report the dispersion of skill score *within* each cluster as part of cluster validity.

## 7. Limitations and How They Will Be Defended

| Limitation | Mitigation | Where addressed |
|---|---|---|
| The proxy is a heuristic, not a measurement of truth. | Phase 4 explicitly bounds claims to "consistency with the proxy" — never "ability to predict skill". | `phd_ml/phase4_*` |
| n = 246 is small for clustering in 15 dimensions. | (a) z-score standardisation; (b) bootstrap stability; (c) cross-method agreement; (d) PCA/UMAP visualisation for human inspection. | This document. |
| Clusters may be confounded by competition style (Chamonix vs Seoul, etc.). | Phase 1 reports per-competition cluster distribution as a confound check. | `cluster_metrics.json` |
| Pseudo-labels propagate noise into Phase 2 / 3 training. | Phase 4 reports a "label-noise sensitivity" experiment (label-flip 10%) so the committee sees robustness. | Phase 4 plan. |

## 8. Outputs Delivered by This Phase

```
data/phd_ml/phase1/labeled_dataset.csv     # features + 4 cluster columns + ordinal labels
data/phd_ml/phase1/cluster_metrics.json    # validity indices, BIC/AIC, ARI, label distribution
data/phd_ml/phase1/skill_proxy_report.csv  # per-cluster skill statistics

figures/phd_ml/phase1/elbow_kmeans.png
figures/phd_ml/phase1/bic_gmm.png
figures/phd_ml/phase1/dendrogram_ward.png
figures/phd_ml/phase1/embedding_pca.png
figures/phd_ml/phase1/embedding_tsne.png
figures/phd_ml/phase1/embedding_umap.png      # if umap-learn installed
figures/phd_ml/phase1/skill_score_distribution.png
figures/phd_ml/phase1/method_agreement.png
```

## 9. References

* Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data Analysis*, 52(1), 258-271.
* Hofmann, M., et al. (2017). Movement primitives in sport biomechanics. *Frontiers in Sports and Active Living*.
* Rein, R., & Memmert, D. (2016). Big data and tactical analysis in elite soccer. *SpringerPlus*, 5, 1410.
* Ratner, A., et al. (2017). Snorkel: rapid training data creation with weak supervision. *VLDB*.
* Federolf, P., Reid, R., Gilgien, M., Haugen, P., & Smith, G. (2014). The application of principal component analysis to quantify technique in sports. *Scandinavian Journal of Medicine & Science in Sports*, 24(3), 491-499.

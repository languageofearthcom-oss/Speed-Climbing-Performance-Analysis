# PhD ML Track — Progress Log

این فایل پیشرفت چهار فاز یادگیری ماشین پایان‌نامه را ردیابی می‌کند. هر فاز پس از تأیید نگارنده بسته می‌شود و فاز بعدی شروع می‌شود.

---

## Constraints Agreed (الزامی)

| # | Rule | Status |
|---|------|--------|
| 1 | بدون CNN دوبعدی روی فریم خام — فقط time-series keypoint | Locked |
| 2 | بدون برچسب‌گذاری انسانی — Unsupervised + Pseudo-labels | Locked |
| 3 | تحویل فاز‌به‌فاز با approval gate + کامیت/پوش | Locked |
| 4 | پذیرش علمی نتیجه منفی (CNN ≤ baseline قابل قبول است) | Locked |

---

## Phase Tracker

| Phase | Title | Branch | Status | Approved |
|-------|-------|--------|--------|----------|
| 1 | Auto-labeling (Unsupervised + Skill Proxy) | `phd-ml/phase1-auto-labeling` | Pipeline executed, results documented, awaiting sign-off | ⏳ |
| 2 | Traditional Baseline (Random Forest / XGBoost) | `phd-ml/phase2-baseline` | Code committed, awaiting user execution | ⏳ |
| 3 | 1D-CNN on Pose Time-Series + Augmentation | `phd-ml/phase3-cnn` | Pending — 114 / 188 pose JSONs available (61% coverage) | — |
| 4 | Comparative Academic Report (ROC, Accuracy, Discussion) | `phd-ml/phase4-report` | Pending | — |

---

## Phase 1 Empirical Results (commit `140fbd4`)

**K-Means k\*=2 chosen by silhouette** (0.423 at k=2 vs 0.252 at k=3 vs 0.139–0.152 at k≥4).

| Metric | Value |
|---|---|
| Silhouette | 0.423 (below 0.5 target — typical for 15-D kinematic data) |
| Davies-Bouldin | 1.617 |
| Calinski-Harabasz | 36.0 |
| Bootstrap-ARI | **0.634 ± 0.252** (weakly stable per Hennig 2007) |
| K-Means × Hierarchical (Ward) ARI | **0.851** (strong agreement, geometric structure is real) |
| K-Means × GMM ARI | 0.327 (GMM at k=5 disagrees) |
| DBSCAN | 2 clusters but 34.5% noise (density structure weak) |

**Pseudo-label distribution**: 226 advanced / 20 beginner ≈ 92% / 8% — **class-imbalanced**.
Skill-proxy separation: Welch p = 0.0022, Mann-Whitney p = 1.6e-5, Cohen's d = -0.92 (large effect).

### Implications for Phase 2
- Use `class_weight='balanced'` in Random Forest / XGBoost (or SMOTE).
- Report stratified F1 + per-class precision/recall — never raw accuracy.
- Baseline majority-class accuracy is 91.9% — anything ≤ that is uninformative.

### Implications for Phase 3
- 114 single-athlete pose JSONs at `data/processed/poses/single_athlete/` (committed in `c600dea`).
- 61% race coverage. **Schema differs** from existing 10 dual-lane samples — phase-3 loader must handle both.
- Realised supervised-training set size = labeled CSV rows ∩ available pose JSONs (computed in Phase 3).

---

## Phase 2 Deliverables

**Goal**: Train class-imbalance-aware supervised baselines (RF, XGBoost, LR, Dummy) on the Phase-1 labels and produce a defensible reference for Phase 3's 1D-CNN.

### Pipeline Stages
1. Load Phase-1 labels (`labeled_dataset.csv`) — binary target `cluster_kmeans_label`.
2. Build six-model lineup: Dummy (floor), LR-balanced, RF-balanced, XGB-spw, RF-SMOTE, XGB-SMOTE.
3. Stratified-5-Fold CV — SMOTE applied INSIDE training fold only (no leakage).
4. Compute per-fold and aggregated metrics — Macro-F1, F1-minority, ROC-AUC, PR-AUC, per-class P/R, confusion matrix. **Accuracy reported only to surface the 91.9% trivial floor.**
5. Native + permutation feature importance per non-trivial model.
6. Five diagnostic figures saved to `figures/phd_ml/phase2/`.

### Files Added
```
phd_ml/phase2/
├── PHASE2_RATIONALE.md          # Markdown twin
├── PHASE2_METHODOLOGY.docx      # Bilingual Word doc (built via docx skill)
├── __init__.py
├── config.py
├── loader.py
├── models.py
├── evaluation.py
├── importance.py
├── viz.py
└── run_pipeline.py
phd_ml/docx_builder/build_phase2_docx.js
```

### How to Run
```bash
git fetch origin && git checkout phd-ml/phase2-baseline
pip install -r requirements.txt -r phd_ml/requirements.txt
python -m phd_ml.phase2.run_pipeline
```

### Phase 2 Sign-off Checklist
- [ ] Methodology document reviewed (`PHASE2_METHODOLOGY.docx` or `PHASE2_RATIONALE.md`)
- [ ] Six-model lineup approved
- [ ] Imbalance strategies (cost-sensitive + SMOTE) approved
- [ ] Metric set (Macro-F1, F1-minority, ROC-AUC, PR-AUC) approved
- [ ] Outcome bands acknowledged (≥0.80 strong / 0.65–0.80 reasonable / 0.50–0.65 weak / <0.50 failure)
- [ ] Pipeline executed and `data/phd_ml/phase2/results.json` reviewed
- [ ] Approval given to start Phase 3 (1D-CNN)

---

## Phase 1 Deliverables

**Goal**: Convert 246 unlabeled samples into a labeled dataset usable by supervised models in Phase 2 & 3.

### Inputs
- `data/ml_dataset/all_features.csv` (371 rows × 25 cols, with `extraction_quality`)
- Quality filter: `extraction_quality >= 0.8` → ~246 rows

### Pipeline Stages
1. **Load & filter** camera-independent features (15 cols)
2. **Standardize** (z-score)
3. **Reduce** for visualization: PCA-2D, t-SNE-2D, UMAP-2D
4. **Cluster** with three algorithms in parallel:
   - K-Means (k chosen via Elbow + Silhouette)
   - GMM (k chosen via BIC/AIC)
   - DBSCAN (density-based, no k)
   - Hierarchical (dendrogram for thesis figure)
5. **Validate**: Silhouette, Davies-Bouldin, Calinski-Harabasz, bootstrap-ARI stability
6. **Skill proxy** → ordinal labels (Beginner / Intermediate / Advanced)
7. **Export** labeled CSV + metrics JSON + figures

### Outputs
- `data/phd_ml/phase1/labeled_dataset.csv`
- `data/phd_ml/phase1/cluster_metrics.json`
- `figures/phd_ml/phase1/*.png`

### Academic Justification
See `phd_ml/phase1/PHASE1_RATIONALE.md`.

### Files Added
```
phd_ml/
├── requirements.txt              # umap-learn, xgboost (extras)
└── phase1/
    ├── PHASE1_RATIONALE.md       # Academic methodology document
    ├── __init__.py
    ├── config.py                 # Paths, constants, feature lists
    ├── loader.py                 # Load CSV + quality filter
    ├── clustering.py             # K-Means, GMM, DBSCAN, Hierarchical
    ├── skill_proxy.py            # Ordinal pseudo-labels via skill score
    ├── viz.py                    # PCA/UMAP/t-SNE + diagnostic plots
    └── run_pipeline.py           # Orchestrator
```

### How to Run (Phase 1)
```bash
pip install -r phd_ml/requirements.txt
python -m phd_ml.phase1.run_pipeline
```

### Phase 1 Sign-off Checklist (for advisor)
- [ ] Methodology document reviewed (`PHASE1_RATIONALE.md`)
- [ ] Cluster metrics inspected (silhouette, BIC, stability)
- [ ] Visualization plots reviewed (PCA, UMAP, dendrogram)
- [ ] Skill proxy formula approved
- [ ] Number of classes (k*) confirmed
- [ ] Approval given to start Phase 2

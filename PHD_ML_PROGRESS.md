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
| 1 | Auto-labeling (Unsupervised + Skill Proxy) | `phd-ml/phase1-auto-labeling` | In Review | ⏳ |
| 2 | Traditional Baseline (Random Forest / XGBoost) | `phd-ml/phase2-baseline` | Pending | — |
| 3 | 1D-CNN on Pose Time-Series + Augmentation | `phd-ml/phase3-cnn` | Pending | — |
| 4 | Comparative Academic Report (ROC, Accuracy, Discussion) | `phd-ml/phase4-report` | Pending | — |

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

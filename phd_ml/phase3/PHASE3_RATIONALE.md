# Phase 3 — 1D-CNN on Pose Time-Series

**Branch**: `phd-ml/phase3-cnn`
**Status**: Pipeline executed on the lane-matched pose subset.
**Predecessors**: `phd-ml/phase1-auto-labeling` (labels) and `phd-ml/phase2-baseline` (reference baselines).

---

## 1. Problem statement

Phase 1 produced 246 binary labels (226 advanced / 20 beginner) derived from K-Means over 15 engineered kinematic features. Phase 2 demonstrated that any model with sufficient capacity recovers these labels nearly perfectly when it sees the same 15 features as input — the headline result (Macro-F1 = 0.978 for `logreg_balanced`, ROC-AUC = 1.000) is a tautology, not an achievement.

**Phase 3 asks the substantive question**: can a model trained on **raw pose time-series** — never given the engineered summary features — recover the same partition? The 1D-CNN sees only the 33 BlazePose landmarks per frame, not the features Phase 1's K-Means used. If it succeeds, the engineered features are redundant and a learned representation suffices. If it fails (or underperforms the 0.97 ceiling), the engineered features carry information that local temporal convolutions over keypoint trajectories cannot recover at this dataset size — a publishable negative result per the project's Constraint 4 (научное приемлемо отрицательного результата / scientific acceptance of a negative result).

## 2. Architecture choice

We deliberately do **not** train a 2D CNN on raw video frames:

1. **Re-doing MediaPipe's job.** Pose extraction is solved upstream by MediaPipe BlazePose; a 2D CNN would have to relearn it from 246 examples.
2. **Capacity vs. data.** 2D CNNs are designed for the ImageNet regime (millions of images). With 246 samples (≤ ~100 after pose intersect for the minority class), 2D CNNs overfit in epochs.
3. **Camera-invariance constraint.** Phase 1 explicitly excluded six camera-dependent features (`eff_*`). Training a 2D CNN on raw frames reintroduces every camera-perspective confound the project has fought to remove.

The 1D-CNN over pose keypoint time-series:

- consumes the upstream pose extractor's output directly,
- operates on a much smaller input volume (T frames × 99 channels rather than T × H × W × 3),
- is parameter-budget compatible with 246 samples (target: < 100k trainable parameters),
- and preserves the camera-independence already engineered into the pipeline (BlazePose coordinates are normalised to image dimensions).

A future study with substantially more pose data should use **ST-GCN** (Spatial-Temporal Graph Convolutional Networks, Yan et al., 2018) — these explicitly model the skeleton topology and are state-of-the-art on action recognition. ST-GCN is documented here as the next-step research direction rather than implemented now, because at 246 samples a graph CNN overparameterises even more aggressively than a flat 1D-CNN.

## 3. Pose data — what we have and what is missing

| Source | Files | Schema | Lane | Quality |
|---|---|---|---|---|
| `data/processed/poses/single_athlete/` (commit `c600dea`) | 114 | flat `frames[].landmarks` (33 × {x,y,z,visibility}) | single climber inferred per file (64 LEFT / 39 RIGHT / 11 CENTER) | mean success_rate 97.0% |
| `data/processed/poses/samples/` | 10 | dual-lane `frames[].{left_climber, right_climber}` | both lanes carried in one file | 100% detection rate |
| **Missing for Phase 3** | 74 races + the second climber of every dual race | re-running `scripts/batch/extract_poses.py` with `dual_lane_detector.py` | both lanes | — |

The Phase-3 loader detects both schemas and emits a uniform `(T, 33, 3)` tensor. Because Phase 1 labels are lane-level rows, the loader is deliberately **lane-aware**:

- dual-lane files emit the requested lane (`left_climber` or `right_climber`),
- single-athlete files are used only when `MANIFEST.csv:athlete_lane_inferred` matches the label row's `lane`,
- single-athlete `center` and lane-mismatch cases are dropped rather than duplicated with potentially wrong labels.

After intersecting with the labeled CSV, the realised training set is:

```
n_total       = 107 lane-matched samples
n_minority    = 6 beginners — the binding constraint for any imbalance strategy
```

`build_dataset()` writes `data/phd_ml/phase3/intersect_report.csv` showing which labelled rows were dropped (`missing_pose`, `single_lane_mismatch:*`, `single_lane_uncertain:center`, `load_error`, `too_few_frames`). The very first sanity check is to confirm `n_minority ≥ CV_FOLDS` so each fold gets at least one positive example. With 3-fold CV, each validation fold has only two beginner examples.

## 4. Pre-processing pipeline

1. **Per-file load**: detect schema → extract `(T_raw, 33, 3)` of (x, y, z) for the chosen climber.
2. **Visibility masking**: landmarks with `visibility < 0.3` are zeroed (rather than discarded) so the convolutional channels see "this joint was occluded this frame" as a learnable signal.
3. **Temporal resampling** (`resample_to_length`): linear interpolation to a uniform `TARGET_SEQUENCE_LENGTH = 200` frames. Speed climbs vary in duration (mean ~6.5s, ranging ~4.5–9s on the 15m wall); a fixed receptive field is what the convolutional architecture needs. Linear interpolation is the conservative choice; for the final reported result consider DTW-based temporal alignment.
4. **Channel flattening**: `(T, 33, 3) → (T, 99)` so `nn.Conv1d` sees a flat channel dimension. The spatial structure of the 33 landmarks is recovered implicitly by the first conv kernel — if this becomes a limitation, swap in ST-GCN.

## 5. Augmentation — how 246 samples get to "enough"

CNNs need many samples; 246 (real) samples do not span the kinematic manifold. We use three augmentations applied per training-fold sample (SMOTE-style synthetic minority interpolation is **deliberately not** used — interpolating two unrelated climbs in pose space produces kinematically implausible sequences):

| Augmentation | Parameter | What it simulates |
|---|---|---|
| Gaussian noise | std = 0.01 in normalised landmark units | BlazePose detector jitter and minor occlusions |
| Time warp | ±15% linear temporal scale | Climbers of different rhythm; resampled back to fixed length |
| Anatomical mirror | 50% probability, swap left/right landmark indices + flip x | Right-handed → left-handed; ~doubles the effective dataset |

`AUG_MULTIPLICITY = 3` virtual replicas per real sample by default. This keeps the CPU run practical while still exposing the network to detector jitter, rhythm changes, and left/right reflection. Augmentation runs **inside the training fold only** — never on the validation fold (the same leakage rule that governed SMOTE in Phase 2).

## 6. Class imbalance

Phase 2 found that `class_weight='balanced'` (cost-sensitive learning) outperformed SMOTE on this label set. We mirror that here:

- `CLASS_WEIGHT_STRATEGY = "inverse_frequency"` is the default; the CrossEntropyLoss weights are `inv_freq / mean(inv_freq)`.
- SMOTE is **not** used. Synthetic minority interpolation on time-series fabricates physiologically unrealistic motions.

## 7. Cross-validation — two splits, only one reportable

| Strategy | Where it lives | What it tells us | Reportable? |
|---|---|---|---|
| **Stratified-3-Fold** (random) | `SPLIT_STRATEGY = "stratified"` | Keeps roughly 4-5 beginner examples per validation fold and pairs with Phase 2 by `sample_index` for Phase 4 | Primary executable run in the current repository |
| **Competition-aware GroupKFold** | `SPLIT_STRATEGY = "competition_aware"` | Holds out an event at a time; useful as a generalisation stress test | Diagnostic only |
| **Subject-aware GroupKFold** | `SPLIT_STRATEGY = "subject_aware"` | Held-out athlete never seen at training; requires real athlete identifiers | Future headline result when metadata exists |

The stratified split is included because it lets Phase 4 perform McNemar / paired-bootstrap comparison with the Phase-2 baselines. A true subject-aware split remains the scientifically strongest design, but the current `*_results.json` files do not carry athlete names or IDs. Therefore any subject-aware claim must wait for metadata; the current repository reports stratified 3-fold as the executable Phase-3 run and competition-aware split only as a diagnostic stress test.

> The current `_athlete_from_race_id` is a placeholder that groups by competition, not by individual climber — the project does not yet have athlete metadata joined to `race_id`. **Before reporting a subject-aware result, replace this function** with a proper join against `data/race_segments/<competition>/<race>_results.json` (each race file lists the two athletes and lanes).

## 8. Architecture details

`PoseCNN` (see `models.py`):

```
Conv1d(99 → 48, k=5) → BN → ReLU → Dropout(0.3)
Conv1d(48 → 96, k=5) → BN → ReLU → Dropout(0.3)
Conv1d(96 → 96, k=3) → BN → ReLU → Dropout(0.3)
GlobalAveragePool(time)
Linear(96 → 48) → ReLU → Dropout(0.3)
Linear(48 → 2)
```

Total trainable parameters: ~ 80k (confirmed via `models.count_parameters()` at run time). Optimiser is AdamW(lr=1e-3, weight_decay=1e-4) with cosine LR schedule and gradient clipping at 1.0. Early stopping uses patience=6 on validation loss.

## 9. Honest outcome bands

Before running the experiment we commit to these interpretations (mirror of Phase 2's bands, with the Phase 2 results substituted):

| Macro-F1 (subject-aware split) | Verdict for the thesis |
|---|---|
| ≥ 0.97 | CNN matches the Phase-2 ceiling — engineered features and learned features carry equivalent information at this dataset size. |
| 0.80 – 0.97 | CNN is competitive but below the engineered-feature ceiling — useful baseline, ST-GCN suggested as future work. |
| 0.65 – 0.80 | Honest negative result: engineered features outperform raw-pose representation learning at n=246. Publishable as evidence that hand-crafted kinematics retain advantage on small datasets. |
| 0.50 – 0.65 | Pseudo-labels are likely poorly aligned with raw-pose evidence; revisit Phase 1 label quality before drawing conclusions. |
| < 0.50 | Method failure — investigate augmentation, fold composition, and label intersect before reporting. |

We do **not** retroactively tune hyperparameters to escape the band we land in. The result is the result.

## 10. Outputs

```
data/phd_ml/phase3/
  ├── results.json           # per-fold + aggregated metrics, model parameter count, split strategy
  ├── cv_predictions.csv     # long-format predictions: sample_index, fold, y_true, y_pred, y_prob_positive
  ├── intersect_report.csv   # which labeled rows survived the pose intersect, why
  └── training_log.csv       # (optional) per-fold per-epoch train/val loss

figures/phd_ml/phase3/
  ├── training_curves.png
  ├── confusion_matrix.png
  └── metric_summary.png     # CNN bars with Phase-2 reference overlay
```

## 10.1 Executed results (lane-matched subset)

Executed with `SPLIT_STRATEGY=stratified`, `CV_FOLDS=3`, `AUG_MULTIPLICITY=3`, CPU-only PyTorch 2.1.2, and the 79,922-parameter 1D-CNN.

| Metric | Mean ± std |
|---|---|
| Macro-F1 | 0.525 ± 0.079 |
| F1 beginner | 0.111 ± 0.157 |
| ROC-AUC | 0.557 ± 0.255 |
| PR-AUC | 0.124 ± 0.065 |
| Beginner recall | 0.167 ± 0.236 |

Pooled over folds, the model catches only 1 of 6 beginner samples. This is an honest negative result: after enforcing lane correctness, the supervised pose-time-series set is too small and too imbalanced for a 1D-CNN to recover the Phase-1 pseudo-label partition. The result should be reported as evidence for a data bottleneck, not as a failed implementation.

The key methodological correction in this run is the lane-aware loader. Earlier scaffold logic joined by race_id only, which could duplicate one single-athlete pose tensor for both left and right lane labels. That was fixed before reporting any Phase-3 result.

## 11. Reproduction

```bash
git fetch origin
git checkout phd-ml/phase3-cnn
pip install -r requirements.txt
pip install -r phd_ml/requirements.txt
python -m phd_ml.phase3.run_pipeline
```

Requires a working PyTorch install. The pipeline runs on CPU; expect ~10–20 minutes per fold without a GPU, ~1–2 minutes with one. Pin `torch>=2.1` to match `pyproject` if added.

## 12. References

- Yan, S., Xiong, Y., & Lin, D. (2018). Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition. AAAI.
- Wang, F., Wang, Z., & Oates, T. (2017). Time Series Classification from Scratch with Deep Neural Networks. IJCNN.
- Iwana, B. K., & Uchida, S. (2021). An empirical survey of data augmentation for time series classification with neural networks. PLOS ONE 16(7).
- Chawla, N. V. et al. (2002). SMOTE — referenced here only to justify its **non-use** on time-series.

## 13. Phase 3 sign-off checklist

- [ ] Pose intersect inspected (`intersect_report.csv`); minority-class survival ≥ CV_FOLDS confirmed
- [ ] Stratified-split run completed and `cv_predictions.csv` joinable with Phase-2 predictions
- [ ] Subject-aware split helper updated to use real athlete identifiers from `data/race_segments/*_results.json`
- [ ] Subject-aware split run completed and metrics interpreted against bands above
- [ ] Methodology document reviewed (this file)
- [ ] Approval given to start Phase 4 (comparative report)

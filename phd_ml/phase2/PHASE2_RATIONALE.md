# Phase 2 — Methodological Rationale

> **Audience**: thesis advisor & dissertation committee.
> **Intent**: justify every methodological choice on a class-imbalanced (92% / 8%), small-n (246) tabular problem.

---

## 1. Problem Statement

Phase 1 produced 246 labeled samples in two ordinal classes:

| Class | n | Share |
|-------|---|-------|
| advanced (majority) | 226 | 91.9% |
| beginner (minority) | 20 | 8.1% |

Phase 2 trains traditional supervised models on this dataset. The deliverable is a **defensible baseline** for the 1D-CNN of Phase 3 to beat (or, by Phase 4's "honesty" rule, for the CNN to fail to beat — also an acceptable outcome).

The dominant constraint is the class imbalance. **Predicting "advanced" for every sample yields 91.9% accuracy.** Therefore *raw accuracy is uninformative* and any reported improvement must be expressed through metrics that reward minority-class recall.

## 2. Why Random Forest and XGBoost?

| Family | Algorithm | Justification |
|---|---|---|
| Bagging | Random Forest (Breiman, 2001) | Standard reference for tabular features; native impurity importance; native `class_weight='balanced'`. |
| Boosting | XGBoost (Chen & Guestrin, 2016) | Best-in-class for small tabular datasets; native `scale_pos_weight`; explicit regularisation against the n=246 size. |
| Linear | Logistic Regression (with StandardScaler) | Reference for whether the structure is captured by a linear decision boundary. |
| Trivial | DummyClassifier (most_frequent) | Sanity floor — anything below is uninformative. |

Running both bagging and boosting families in parallel is methodological triangulation in the same spirit as Phase 1's K-Means / GMM / Hierarchical lineup. Disagreement between RF and XGBoost is informative; agreement is corroboration.

## 3. Imbalance Handling — Two Strategies

We deliberately implement **two orthogonal strategies** so the committee can compare like-for-like:

### Strategy A: Cost-sensitive learning
* `class_weight='balanced'` for Random Forest and Logistic Regression
* `scale_pos_weight = n_majority / n_minority ≈ 11.3` for XGBoost

The training data is unchanged; the model's loss is reweighted to penalise minority-class errors more heavily.

### Strategy B: SMOTE resampling (Chawla et al., 2002)
* Synthetic minority oversampling **inside each CV training fold**
* `k_neighbors = 3` (smallest meaningful, given 4 minority samples per fold)

Crucially, SMOTE is applied **only to training folds**, never to the test fold. Applying SMOTE before splitting is a common but invalidating mistake (Saito & Rehmsmeier, 2015) that leaks synthetic minority samples into evaluation.

We do **not** combine cost-sensitive + SMOTE in one model: the goal is to compare the two strategies, not to stack them.

## 4. Cross-Validation Protocol

* **StratifiedKFold(n_splits=5)** — preserves the 226/20 ratio in each fold.
* 20 minority samples / 5 folds = 4 per test fold — small but acceptable; results are reported as mean ± std across folds for a defensible measure of dispersion.
* `random_state` is pinned for reproducibility.

## 5. Metrics — Imbalance-Appropriate Only

We report only metrics that are meaningful at this class ratio:

| Metric | Why it is included |
|---|---|
| **Macro-F1** | Mean F1 across both classes; invariant to class size. Primary headline metric. |
| **F1 (minority)** | Direct measure of how well we detect the rare class. |
| **Per-class precision / recall** | Whether errors are FPs or FNs on the minority side. |
| **ROC-AUC** | Threshold-independent ranking quality. |
| **PR-AUC (Average Precision)** | Strictly more informative than ROC-AUC at this imbalance (Saito & Rehmsmeier, 2015). |
| **Confusion matrix** | The actual counts. |
| **Accuracy** | Reported only to surface the trivial 91.9% floor. We do not optimise for it. |

## 6. Feature Importance — Two Methods

| Method | Strength | Weakness | Reported |
|---|---|---|---|
| Native (impurity / |coef|) | Fast, no extra fits | Biased toward continuous, high-cardinality features (Strobl et al., 2007) | Yes |
| Permutation (Breiman, 2001) | Model-agnostic; uses held-out data | Compute-heavy | Yes — averaged across CV folds with std |

We do **not** use SHAP in Phase 2 to keep the baseline lean. SHAP belongs in Phase 4's interpretability deep-dive if needed.

## 7. Honest Outcome Bands

| Macro-F1 | Verdict for the committee |
|---|---|
| ≥ 0.80 | Strong baseline; CNN must clear this convincingly. |
| 0.65 – 0.80 | Reasonable baseline; CNN expected to match or beat. |
| 0.50 – 0.65 | Weak baseline; pseudo-labels may be noisy, evidence accordingly. |
| < 0.50 | Failure — the proxy labels are not learnable from these 15 features. Phase 4 will frame this as evidence about the proxy, not the model. |

We commit to reporting whichever band we land in **without retroactively tweaking hyperparameters to escape it**. The thesis values an honest negative result over an inflated positive one.

## 8. Outputs Delivered by This Phase

```
data/phd_ml/phase2/results.json            — per-fold + aggregated metrics for every model
data/phd_ml/phase2/cv_predictions.csv      — long-format held-out predictions
data/phd_ml/phase2/feature_importance.csv  — native + permutation, per model

figures/phd_ml/phase2/confusion_matrices.png
figures/phd_ml/phase2/roc_curves.png
figures/phd_ml/phase2/pr_curves.png
figures/phd_ml/phase2/metric_comparison.png
figures/phd_ml/phase2/feature_importance.png
```

## 9. References

* Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32.
* Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: synthetic minority over-sampling technique. *JAIR*, 16, 321–357.
* Chen, T., & Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD '16*, 785–794.
* Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLoS ONE*, 10(3), e0118432.
* Strobl, C., Boulesteix, A. L., Zeileis, A., & Hothorn, T. (2007). Bias in random forest variable importance measures. *BMC Bioinformatics*, 8(25).

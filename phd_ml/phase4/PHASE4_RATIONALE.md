# Phase 4 — Comparative Academic Report

**Branch**: `phd-ml/phase4-report`  
**Status**: Phase-2 vs Phase-3 comparison executed on the shared `sample_index` subset.  
**Inputs**:

- `data/phd_ml/phase2/cv_predictions.csv`
- `data/phd_ml/phase2/results.json`
- `data/phd_ml/phase3/cv_predictions.csv`
- `data/phd_ml/phase3/results.json`
- `data/phd_ml/phase3/intersect_report.csv`

## 1. هدف فاز چهارم

هدف فاز چهارم ساخت یک گزارش مقایسه‌ای آکادمیک بین فاز ۲ و فاز ۳ است. این فاز مدل جدیدی آموزش نمی‌دهد. فقط خروجی‌های held-out موجود را روی نمونه‌های مشترک مقایسه می‌کند تا مقایسه عادلانه باشد.

قانون مقایسه:

> فقط نمونه‌هایی وارد مقایسه می‌شوند که هم در خروجی cross-validation فاز ۲ و هم در خروجی lane-matched فاز ۳ `sample_index` معتبر داشته باشند.

در نتیجه، مقایسه اصلی روی ۱۰۷ نمونه مشترک انجام شد:

| کلاس | تعداد |
|---|---:|
| advanced | 101 |
| beginner | 6 |
| کل | 107 |

## 2. چرا این مقایسه عادلانه‌تر است؟

فاز ۲ روی کل دیتاست برچسب‌خورده فاز ۱ اجرا شد: ۲۴۶ نمونه، شامل ۲۰ beginner. اما فاز ۳ پس از اصلاح lane-aware loader فقط ۱۰۷ نمونه معتبر دارد، شامل ۶ beginner. بنابراین مقایسه مستقیم Macro-F1 فاز ۲ روی ۲۴۶ نمونه با Macro-F1 فاز ۳ روی ۱۰۷ نمونه از نظر آماری و روش‌شناختی ناقص است.

در فاز ۴، همه مدل‌های فاز ۲ روی همان ۱۰۷ نمونه‌ای ارزیابی شدند که CNN فاز ۳ دیده است. این کار دو مزیت دارد:

1. تعداد نمونه‌ها و توزیع کلاس برای همه مدل‌ها یکسان است.
2. paired comparison ممکن می‌شود، چون هر مدل برای همان `sample_index`ها پیش‌بینی دارد.

## 3. Caveat اصلی فاز ۲

فاز ۲ از ۱۵ فیچر مهندسی‌شده استفاده می‌کند. همین فیچرها در فاز ۱ برای ساخت pseudo-labelها با K-Means استفاده شده‌اند. بنابراین عملکرد بسیار بالا در فاز ۲ باید به عنوان سقف feature-engineered و تا حدی تاتولوژیک خوانده شود، نه به عنوان اثبات قطعی generalization.

مدل `logreg_balanced` در فاز ۲ روی کل ۲۴۶ نمونه به Macro-F1 برابر ۰٫۹۷۸ رسید. روی subset مشترک ۱۰۷ نمونه نیز همه نمونه‌ها را درست پیش‌بینی کرد. این نتیجه از نظر مهندسی عالی است، اما از نظر پایان‌نامه باید با caveat بالا گزارش شود.

## 4. فاز ۳ چه چیزی را مستقل‌تر آزمون می‌کند؟

فاز ۳ از فیچرهای مهندسی‌شده فاز ۱ استفاده نمی‌کند. ورودی مدل فقط سری زمانی pose است:

- ۲۰۰ فریم برای هر نمونه
- ۳۳ landmark در هر فریم
- ۳ مختصات برای هر landmark
- ورودی نهایی: `T=200, C=99`

بنابراین 1D-CNN فاز ۳ آزمون مستقل‌تری است: آیا از raw pose time-series می‌توان همان partition فاز ۱ را بدون دیدن summary featureهای فاز ۱ بازیابی کرد؟

## 5. نتایج روی ۱۰۷ نمونه مشترک

| مدل | منبع | Macro-F1 | F1 beginner | Recall beginner | ROC-AUC | PR-AUC | Confusion `[[TN, FP], [FN, TP]]` |
|---|---|---:|---:|---:|---:|---:|---|
| dummy_majority | Phase 2 | 0.486 | 0.000 | 0.000 | 0.500 | 0.056 | `[[101, 0], [6, 0]]` |
| logreg_balanced | Phase 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | `[[101, 0], [0, 6]]` |
| rf_balanced | Phase 2 | 0.952 | 0.909 | 0.833 | 1.000 | 1.000 | `[[101, 0], [1, 5]]` |
| xgb_scale_pos_weight | Phase 2 | 0.952 | 0.909 | 0.833 | 0.998 | 0.976 | `[[101, 0], [1, 5]]` |
| rf_smote | Phase 2 | 0.952 | 0.909 | 0.833 | 1.000 | 1.000 | `[[101, 0], [1, 5]]` |
| xgb_smote | Phase 2 | 0.952 | 0.909 | 0.833 | 1.000 | 1.000 | `[[101, 0], [1, 5]]` |
| cnn1d | Phase 3 | 0.541 | 0.143 | 0.167 | 0.528 | 0.086 | `[[94, 7], [5, 1]]` |

## 6. Paired comparison

مقایسه جفتی اصلی بین `logreg_balanced` و `cnn1d` انجام شد.

| شاخص | مقدار |
|---|---:|
| هر دو درست | 95 |
| فقط logreg درست | 12 |
| فقط CNN درست | 0 |
| هر دو غلط | 0 |
| McNemar exact p-value | 0.000488 |

Bootstrap جفتی روی ۵۰۰۰ resample انجام شد. جهت اختلاف در خروجی‌ها `logreg_balanced - cnn1d` است. بنابراین مقدار مثبت یعنی برتری فاز ۲.

| Metric | Mean difference | 95% CI |
|---|---:|---:|
| accuracy | 0.112 | [0.056, 0.168] |
| balanced_accuracy | 0.451 | [0.265, 0.554] |
| f1_macro | 0.463 | [0.315, 0.543] |
| f1_beginner | 0.866 | [0.579, 1.000] |
| precision_beginner | 0.873 | [0.571, 1.000] |
| recall_beginner | 0.833 | [0.500, 1.000] |
| roc_auc | 0.470 | [0.166, 0.796] |
| pr_auc | 0.902 | [0.777, 0.975] |

## 7. تفسیر نهایی

نتیجه CNN ضعیف‌تر از baselineهای فاز ۲ است. اما این نتیجه نباید به عنوان شکست ساده مدل خوانده شود. نکته علمی اصلی این است:

> پس از enforce کردن lane correctness، فقط ۶ نمونه beginner معتبر باقی مانده است. در چنین شرایطی، یک 1D-CNN سبک با ۷۹٬۹۲۲ پارامتر نمی‌تواند partition فاز ۱ را از raw pose time-series بازیابی کند.

عبارت مناسب برای پایان‌نامه:

> نتایج فاز چهارم نشان داد که baselineهای مبتنی بر فیچرهای مهندسی‌شده، به‌ویژه `logreg_balanced`، روی subset مشترک عملکرد بسیار بالایی دارند. با این حال، این عملکرد باید در پرتو تاتولوژی روش‌شناختی فاز ۲ تفسیر شود، زیرا pseudo-labelهای فاز ۱ از همان فضای فیچر ساخته شده‌اند. در مقابل، 1D-CNN فاز ۳ آزمون مستقل‌تری روی سری زمانی pose فراهم می‌کند، اما با فقط ۶ نمونه beginner lane-matched قادر به بازتولید عملکرد baseline نیست. نتیجه منفی CNN از نظر پایان‌نامه قابل دفاع است و نشان می‌دهد گام بعدی باید افزایش پوشش pose lane-matched باشد، نه صرفاً tuning معماری.

## 8. خروجی‌ها

```
data/phd_ml/phase4/
  results.json
  metrics_common.csv
  common_predictions_long.csv
  paired_predictions_logreg_vs_cnn.csv
  paired_bootstrap_diffs.csv

figures/phd_ml/phase4/
  common_metric_comparison.png
  beginner_precision_recall.png
  reference_vs_cnn_confusion.png
  reference_vs_cnn_curves.png
  lane_matched_data_bottleneck.png

phd_ml/phase4/
  PHASE4_RATIONALE.md
  PHASE4_COMPARATIVE_REPORT.docx
```

## 9. بازتولید

```bash
uv run python -m phd_ml.phase4.run_pipeline
node phd_ml/docx_builder/build_phase4_docx.js
```


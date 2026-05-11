/**
 * Phase 2 Methodology Document — DOCX builder.
 *
 * Generates a bilingual (English + Persian) thesis-grade Word document for the
 * Random Forest + XGBoost baseline phase, with deliberate emphasis on the
 * class-imbalance handling and the imbalance-appropriate evaluation metrics.
 *
 * Run:  node build_phase2_docx.js
 * Out:  ../phase2/PHASE2_METHODOLOGY.docx
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, TableOfContents,
} = require("docx");

const FONT_LATIN = "Arial";
const FONT_PERSIAN = "Tahoma";

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const headerShade = { fill: "1F4E79", type: ShadingType.CLEAR, color: "auto" };

const txt = (t, o = {}) => new TextRun({ text: t, font: FONT_LATIN, size: 22, ...o });
const txtFa = (t, o = {}) => new TextRun({ text: t, font: FONT_PERSIAN, size: 22, rtl: true, ...o });
const p = (t, o = {}) => {
  const { fa = false } = o;
  return new Paragraph({
    bidirectional: fa,
    alignment: fa ? AlignmentType.RIGHT : AlignmentType.JUSTIFIED,
    spacing: { after: 120 },
    children: [fa ? txtFa(t) : txt(t)],
  });
};
const h1 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 240, after: 160 },
  children: [new TextRun({ text: t, font: FONT_LATIN, size: 32, bold: true, color: "1F4E79" })],
});
const h2 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 200, after: 120 },
  children: [new TextRun({ text: t, font: FONT_LATIN, size: 26, bold: true, color: "2E74B5" })],
});
const h3 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 160, after: 100 },
  children: [new TextRun({ text: t, font: FONT_LATIN, size: 23, bold: true, color: "404040" })],
});
const code = (lines) => lines.map((line) => new Paragraph({
  spacing: { before: 0, after: 0, line: 240 },
  shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
  children: [new TextRun({ text: line || " ", font: "Consolas", size: 18 })],
}));
const bullet = (t, fa = false) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  bidirectional: fa,
  alignment: fa ? AlignmentType.RIGHT : AlignmentType.LEFT,
  spacing: { after: 60 },
  children: [fa ? txtFa(t) : txt(t)],
});
const spacer = () => new Paragraph({ children: [new TextRun(" ")] });
const pagebreak = () => new Paragraph({ children: [new PageBreak()] });

const makeCell = (content, opts = {}) => {
  const { width = 3000, header = false, fa = false } = opts;
  const lines = Array.isArray(content) ? content : [content];
  const runs = lines.map((line) => {
    const baseProps = header
      ? { bold: true, color: "FFFFFF", size: 22 }
      : { size: 21 };
    if (fa) {
      return new Paragraph({
        bidirectional: true, alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: line, font: FONT_PERSIAN, rtl: true, ...baseProps })],
      });
    }
    return new Paragraph({
      children: [new TextRun({ text: line, font: FONT_LATIN, ...baseProps })],
    });
  });
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: header ? headerShade : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: runs,
  });
};
const table = (rows, columnWidths) => {
  const total = columnWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((cellContent, j) => makeCell(cellContent, {
        width: columnWidths[j],
        header: i === 0,
        fa: typeof cellContent === "string" && /[؀-ۿ]/.test(cellContent),
      })),
    })),
  });
};

// ---------- content ---------------------------------------------------------

const COVER = [
  new Paragraph({
    spacing: { before: 2400, after: 240 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Speed Climbing Performance Analysis",
      font: FONT_LATIN, size: 44, bold: true, color: "1F4E79" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "PhD ML Track — Phase 2",
      font: FONT_LATIN, size: 32, bold: true, color: "2E74B5" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true, spacing: { after: 600 },
    children: [new TextRun({ text: "تحلیل عملکرد سنگ‌نوردی سرعت — مسیر یادگیری ماشین پایان‌نامه — فاز دوم",
      font: FONT_PERSIAN, size: 26, rtl: true, color: "404040" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Methodology Document",
      font: FONT_LATIN, size: 28, italics: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 720 },
    children: [new TextRun({ text: "Random Forest + XGBoost Baselines with Class-Imbalance Handling",
      font: FONT_LATIN, size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Author: airano   |   Date: 2026-04-30   |   Version: 1.0",
      font: FONT_LATIN, size: 22, color: "595959" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "Branch: phd-ml/phase2-baseline",
      font: "Consolas", size: 20, color: "595959" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 1200 },
    children: [new TextRun({
      text: "Repository: github.com/languageofearthcom-oss/Speed-Climbing-Performance-Analysis",
      font: "Consolas", size: 18, color: "808080",
    })],
  }),
  pagebreak(),
];

const EXEC_EN = [
  h1("Executive Summary"),
  p("Phase 2 trains supervised baselines on the labeled dataset produced by Phase 1 (246 samples, 226 advanced / 20 beginner — class imbalance 92% / 8%). Six models are evaluated under a single Stratified-5-Fold cross-validation harness: a sanity-floor DummyClassifier; a Logistic Regression with balanced class weights; Random Forest and XGBoost under two distinct imbalance-handling strategies (cost-sensitive learning and SMOTE resampling)."),
  p("Because the trivial majority-class baseline already achieves 91.9% accuracy, raw accuracy is suppressed throughout the analysis. Headline metrics are Macro-F1, F1 on the minority (beginner) class, ROC-AUC, and PR-AUC (Average Precision), with full confusion matrices and per-class precision/recall reported per-fold and as mean ± std across folds."),
  p("Feature importance is computed via two methods — native (impurity / |coef|) and permutation importance averaged across CV folds — to mitigate the well-known impurity bias toward high-cardinality features (Strobl et al., 2007). The phase outputs results.json, cv_predictions.csv, feature_importance.csv, and five diagnostic figures, all committed to branch phd-ml/phase2-baseline."),
  p("The deliverable is a defensible baseline against which Phase 3's 1D-CNN will be compared. Per the project's honesty rule, whatever score band these baselines occupy is reported without retroactive hyperparameter tweaking to escape it."),
  p("EMPIRICAL RESULT (executed 2026-05-11, commit 4710bb5): all five non-trivial models land in the strong-baseline band — Logistic Regression with class_weight='balanced' tops the lineup at Macro-F1 0.978 ± 0.045 (F1-minority 0.960 ± 0.080, ROC-AUC 1.000, PR-AUC 1.000), with XGBoost variants close behind at 0.972. Section 8 reports the full table, the pooled confusion counts, the top predictive features (post_body_lean_std dominates), and the critical methodological caveat that this near-perfect ceiling is tautological: Phase-1 labels were derived from the same 15 features now used as inputs. The genuine Phase-3 test is whether a 1D-CNN over raw pose time-series can recover the same partition without seeing the engineered summary features."),
];

const EXEC_FA = [
  h1("خلاصه اجرایی (فارسی)"),
  p("فاز دوم مدل‌های نظارت‌شده پایه را روی دیتاست برچسب‌خورده فاز اول (۲۴۶ نمونه، ۲۲۶ پیشرفته / ۲۰ مبتدی — عدم‌توازن ۹۲٪ / ۸٪) آموزش می‌دهد. شش مدل تحت یک پروتکل Stratified-5-Fold مشترک ارزیابی می‌شوند: کف منطقی DummyClassifier، رگرسیون لجستیک با وزن‌های متعادل، Random Forest و XGBoost تحت دو استراتژی متفاوت مدیریت عدم‌توازن (یادگیری cost-sensitive و resampling با SMOTE).", { fa: true }),
  p("از آنجا که خط‌پایه trivial کلاس اکثریت در همان ابتدا به دقت ۹۱٫۹٪ می‌رسد، در سراسر تحلیل از گزارش accuracy خام پرهیز می‌شود. متریک‌های اصلی Macro-F1، F1 کلاس اقلیت (beginner)، ROC-AUC و PR-AUC (Average Precision) هستند، به‌همراه ماتریس‌های درهم‌ریختگی کامل و precision/recall هر کلاس در هر fold و میانگین ± انحراف معیار.", { fa: true }),
  p("اهمیت ویژگی با دو روش مکمل محاسبه می‌شود — native (impurity / |coef|) و permutation importance میانگین‌گیری‌شده روی foldهای CV — برای کنترل بایاس شناخته‌شده‌ی impurity به سمت ویژگی‌های با cardinality بالا (Strobl و همکاران، ۲۰۰۷). خروجی فاز شامل results.json، cv_predictions.csv، feature_importance.csv و پنج نمودار تشخیصی است که همگی روی شاخه phd-ml/phase2-baseline کامیت می‌شوند.", { fa: true }),
  p("تحویلی این فاز یک خط‌پایه قابل دفاع است که 1D-CNN فاز سوم با آن مقایسه می‌شود. مطابق قانون صداقت پروژه، هر بازه‌ی نمره‌ای که این خطوط پایه به آن می‌رسند به‌صراحت گزارش می‌شود — بدون بازنویسی hyperparameter برای فرار از نتیجه‌ی صادقانه.", { fa: true }),
  p("نتایج تجربی (اجرا: ۲۰۲۶-۰۵-۱۱، کامیت 4710bb5): هر پنج مدل غیرتُرویال در بازه قوی (≥۰٫۸۰) قرار گرفتند — رگرسیون لجستیک با class_weight='balanced' در صدر با Macro-F1 برابر ۰٫۹۷۸ ± ۰٫۰۴۵ (F1 اقلیت ۰٫۹۶۰ ± ۰٫۰۸۰، ROC-AUC ۱٫۰۰۰، PR-AUC ۱٫۰۰۰) و XGBoost با ۰٫۹۷۲. بخش هشتم جدول کامل، شمارش‌های pooled confusion، ویژگی‌های برتر (post_body_lean_std غالب) و هشدار روش‌شناختی حیاتی را گزارش می‌کند: این سقف نزدیک به کمال یک ساختار tautological است، زیرا برچسب‌های فاز اول از همان ۱۵ ویژگی استخراج شده‌اند که اکنون ورودی فاز دوم‌اند. آزمون واقعی فاز سوم این است که آیا یک 1D-CNN روی سری زمانی پوز خام می‌تواند بدون دیدن ویژگی‌های summary مهندسی‌شده، همان partition را بازیابی کند.", { fa: true }),
];

const SECTIONS = [
  h1("1. Problem Statement"),
  p("Phase 1 produced 246 labeled samples in two ordinal classes:"),
  spacer(),
  table(
    [["Class", "n", "Share", "Note"],
     ["advanced (majority)", "226", "91.9%", "Cluster 1 of K-Means k* = 2"],
     ["beginner (minority)", "20", "8.1%", "Cluster 0; well-isolated in UMAP, blurred in PCA"]],
    [3000, 1100, 1500, 3760],
  ),
  spacer(),
  p("The class imbalance is the dominant constraint. Predicting \"advanced\" for every sample yields 91.9% accuracy — therefore raw accuracy is uninformative and any reported gain must come from minority-class metrics."),

  h1("2. Why Random Forest and XGBoost"),
  table(
    [["Family", "Algorithm", "Justification"],
     ["Bagging", "Random Forest (Breiman, 2001)", "Tabular reference; native impurity importance; native class_weight='balanced'."],
     ["Boosting", "XGBoost (Chen & Guestrin, 2016)", "Best-in-class on small tabular data; explicit L2 regularisation; native scale_pos_weight."],
     ["Linear", "Logistic Regression", "Reference for whether structure is linearly separable."],
     ["Trivial", "DummyClassifier(most_frequent)", "Sanity floor — anything below this is uninformative."]],
    [1300, 3000, 5060],
  ),
  spacer(),
  p("Running both bagging and boosting families is methodological triangulation in the same spirit as Phase 1's K-Means / GMM / Hierarchical lineup."),

  h1("3. Imbalance Handling — Two Strategies"),
  h3("Strategy A — Cost-sensitive learning"),
  ...["class_weight='balanced' for Random Forest and Logistic Regression",
      "scale_pos_weight = n_majority / n_minority ≈ 11.3 for XGBoost"].map((x) => bullet(x)),
  p("Training data is unchanged; the loss is reweighted so minority-class errors cost more."),
  h3("Strategy B — SMOTE resampling (Chawla et al., 2002)"),
  ...["Synthetic minority oversampling INSIDE each CV training fold only",
      "k_neighbors = 3 (smallest meaningful given 4 minority samples per fold)",
      "NEVER applied before splitting — that leaks synthetic minority samples into evaluation (Saito & Rehmsmeier, 2015)"].map((x) => bullet(x)),
  p("We do not stack Strategy A + Strategy B in one model. The goal is comparison of the two strategies, not maximisation of a single number."),

  h1("4. Cross-Validation Protocol"),
  table(
    [["Setting", "Value", "Reason"],
     ["Splitter", "StratifiedKFold(5, shuffle=True)", "Preserves 226/20 ratio per fold"],
     ["Folds", "5", "20/5 = 4 minority per test fold — minimal but workable"],
     ["random_state", "42", "Pinned for reproducibility"],
     ["SMOTE timing", "Inside training split only", "Prevents leakage to test fold"]],
    [2200, 3300, 3860],
  ),

  h1("5. Metrics — Imbalance-Appropriate Only"),
  table(
    [["Metric", "Why it is reported"],
     ["Macro-F1", "Mean F1 across both classes; primary headline."],
     ["F1 (minority)", "How well we detect the rare class."],
     ["Per-class precision / recall", "Whether errors are FP or FN on the minority side."],
     ["ROC-AUC", "Threshold-independent ranking quality."],
     ["PR-AUC (Average Precision)", "Strictly more informative than ROC at this imbalance."],
     ["Confusion matrix", "Actual counts."],
     ["Accuracy", "Reported only to surface the trivial 91.9% floor."]],
    [3000, 6360],
  ),

  h1("6. Feature Importance"),
  table(
    [["Method", "Strength", "Weakness", "Reported"],
     ["Native (impurity / |coef|)", "Fast, no extra fits", "Biased toward continuous, high-cardinality features (Strobl 2007)", "Yes"],
     ["Permutation (Breiman 2001)", "Model-agnostic; held-out data", "Compute-heavy", "Yes — averaged across folds with std"]],
    [2200, 2400, 3300, 1460],
  ),
  spacer(),
  p("SHAP is intentionally deferred to Phase 4 to keep this baseline lean."),

  h1("7. Honest Outcome Bands"),
  p("Before running the experiment we commit to interpreting whichever band we land in, without retroactive tuning:"),
  spacer(),
  table(
    [["Macro-F1", "Verdict for the committee"],
     ["≥ 0.80", "Strong baseline; CNN must clear this convincingly."],
     ["0.65 – 0.80", "Reasonable baseline; CNN expected to match or beat."],
     ["0.50 – 0.65", "Weak baseline; pseudo-labels may be noisy, evidence accordingly."],
     ["< 0.50", "Failure — proxy labels not learnable from these 15 features. Phase 4 will frame as evidence about the proxy, not the model."]],
    [1700, 7660],
  ),

  h1("8. Empirical Results"),
  p("Pipeline executed on 2026-05-11 against commit 4710bb5. All six models trained successfully (imbalanced-learn 0.14.1, xgboost 3.2.0 installed). Stratified-5-Fold CV results, mean ± std across folds:"),
  spacer(),
  table(
    [["Model", "F1-macro", "F1-minority", "ROC-AUC", "PR-AUC"],
     ["dummy_majority (floor)", "0.479 ± 0.000", "0.000 ± 0.000", "0.500", "0.081"],
     ["logreg_balanced", "0.978 ± 0.045", "0.960 ± 0.080", "1.000", "1.000"],
     ["rf_balanced", "0.949 ± 0.070", "0.905 ± 0.131", "1.000", "0.990"],
     ["xgb_scale_pos_weight", "0.972 ± 0.034", "0.949 ± 0.063", "1.000", "1.000"],
     ["rf_smote", "0.969 ± 0.038", "0.943 ± 0.070", "0.999", "0.990"],
     ["xgb_smote", "0.972 ± 0.034", "0.949 ± 0.063", "1.000", "1.000"]],
    [2400, 1740, 1740, 1740, 1740],
  ),
  spacer(),
  h3("Pooled confusion (over all CV folds; 226 advanced + 20 beginner = 246)"),
  table(
    [["Model", "TP (beginner caught)", "FN (beginner missed)", "FP (advanced misclassified)"],
     ["dummy_majority", "0 / 20", "20", "0"],
     ["logreg_balanced", "20 / 20", "0", "2"],
     ["xgb_scale_pos_weight", "19 / 20", "1", "1"],
     ["xgb_smote", "19 / 20", "1", "1"],
     ["rf_smote", "18 / 20", "2", "0"],
     ["rf_balanced", "17 / 20", "3", "0"]],
    [2800, 2300, 2200, 2060],
  ),
  spacer(),
  h3("Top predictive features (consistent across permutation + native methods)"),
  ...["post_body_lean_std — permutation 0.24 (LR), native 0.25 (RF). Dominant single feature.",
      "post_avg_body_lean — native 0.23 (RF), permutation 0.03 (LR).",
      "freq_foot_movement_amplitude — native ≈ 0.06 (RF/XGB).",
      "post_max_reach_ratio — permutation 0.03 (LR).",
      "post_elbow_angle_std — permutation 0.02 (LR)."].map((x) => bullet(x)),
  spacer(),
  h2("Critical caveat — read before reporting these numbers"),
  p("ROC-AUC = 1.000 is a tautological ceiling, not a triumph. The Phase-1 K-Means labels were derived from the SAME 15 features now used as Phase-2 inputs. These models are recovering a deterministic partition of the feature space, not predicting from independent evidence. Any model with sufficient capacity will saturate at this ceiling, and the perfect score is by design rather than achievement."),
  p("The real Phase-3 test is whether a 1D-CNN trained on RAW pose time-series (33 BlazePose landmarks × T frames) can recover the same partition. Below ~0.65 macro-F1 from raw pose CNN should be framed as scientific evidence that summary kinematic features carry the entire signal — a publishable negative result per project Constraint 4 — not a model failure."),
  p("The fold IDs in cv_predictions.csv are the reference partition. Any subject-aware or competition-aware split adopted in Phase 3 must report alignment with these IDs to enable fair comparison."),
  spacer(),
  h3("Verdict against the outcome bands"),
  p("All five non-trivial models land in the ≥ 0.80 strong-baseline band. The bands now serve as targets for Phase 3, not as final verdicts on Phase 2."),

  h1("9. Code Architecture"),
  ...code([
    "phd_ml/phase2/",
    "├── __init__.py",
    "├── PHASE2_RATIONALE.md          # Markdown twin of this Word document",
    "├── config.py                    # Paths, hyperparameters, target column",
    "├── loader.py                    # Phase-1 labels → supervised problem",
    "├── models.py                    # Six-model factory (RF, XGB, LR, Dummy)",
    "├── evaluation.py                # Stratified CV harness + metric aggregator",
    "├── importance.py                # Native + permutation feature importance",
    "├── viz.py                       # Five diagnostic figures",
    "└── run_pipeline.py              # Orchestrator",
  ]),

  h1("10. Outputs"),
  ...["data/phd_ml/phase2/results.json — per-fold + aggregated metrics for every model",
      "data/phd_ml/phase2/cv_predictions.csv — long-format held-out predictions",
      "data/phd_ml/phase2/feature_importance.csv — native + permutation per model",
      "figures/phd_ml/phase2/confusion_matrices.png",
      "figures/phd_ml/phase2/roc_curves.png",
      "figures/phd_ml/phase2/pr_curves.png",
      "figures/phd_ml/phase2/metric_comparison.png",
      "figures/phd_ml/phase2/feature_importance.png"].map((x) => bullet(x)),

  h1("11. Reproduction"),
  ...code([
    "git fetch origin",
    "git checkout phd-ml/phase2-baseline",
    "pip install -r requirements.txt",
    "pip install -r phd_ml/requirements.txt   # adds imbalanced-learn",
    "python -m phd_ml.phase2.run_pipeline",
  ]),

  h1("12. References"),
  ...["Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.",
      "Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: synthetic minority over-sampling technique. JAIR, 16, 321–357.",
      "Chen, T., & Guestrin, C. (2016). XGBoost: a scalable tree boosting system. KDD, 785–794.",
      "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLoS ONE, 10(3), e0118432.",
      "Strobl, C., Boulesteix, A. L., Zeileis, A., & Hothorn, T. (2007). Bias in random forest variable importance measures. BMC Bioinformatics, 8(25)."].map((x) => bullet(x)),

  h1("13. Sign-off Checklist"),
  ...["Methodology document reviewed (this file)",
      "Six-model lineup approved",
      "Imbalance strategies (cost-sensitive + SMOTE) approved",
      "Stratified-5-Fold CV protocol approved",
      "Metric set (Macro-F1, F1-minority, ROC-AUC, PR-AUC) approved",
      "Outcome bands acknowledged",
      "Approval given to start Phase 3 (1D-CNN on pose time-series)"
  ].map((t) => new Paragraph({
    numbering: { reference: "checks", level: 0 },
    spacing: { after: 80 },
    children: [txt(t)],
  })),
  spacer(),
  h3("تأیید فارسی"),
  ...["مطالعه سند روش‌شناسی",
      "تأیید لیست شش‌گانه مدل‌ها",
      "تأیید استراتژی‌های مدیریت عدم‌توازن (cost-sensitive و SMOTE)",
      "تأیید پروتکل Stratified-5-Fold CV",
      "تأیید مجموعه متریک‌ها (Macro-F1، F1 اقلیت، ROC-AUC، PR-AUC)",
      "آگاهی از بازه‌های نتیجه و قانون صداقت",
      "تأیید شروع فاز سوم (1D-CNN روی سری زمانی پوز)"
  ].map((t) => new Paragraph({
    numbering: { reference: "checks", level: 0 },
    bidirectional: true, alignment: AlignmentType.RIGHT,
    spacing: { after: 80 },
    children: [txtFa(t)],
  })),
];

// ---------- assembly ---------------------------------------------------------

const doc = new Document({
  creator: "airano",
  title: "Speed Climbing — Phase 2 Methodology",
  description: "PhD ML Track — Phase 2 Baseline Methodology Document",
  styles: {
    default: { document: { run: { font: FONT_LATIN, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT_LATIN, color: "1F4E79" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT_LATIN, color: "2E74B5" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT_LATIN, color: "404040" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "checks",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "☐",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "PhD ML Track — Phase 2", font: FONT_LATIN, size: 18, color: "808080" })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Speed Climbing Performance Analysis — Phase 2 Methodology v1.0   |   Page ",
            font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ text: " / ", font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT_LATIN, size: 18, color: "808080" }),
        ],
      })] }),
    },
    children: [
      ...COVER,
      ...EXEC_EN,
      ...EXEC_FA,
      pagebreak(),
      h1("Table of Contents"),
      new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
      pagebreak(),
      ...SECTIONS,
    ],
  }],
});

const outPath = path.resolve(__dirname, "..", "phase2", "PHASE2_METHODOLOGY.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`Wrote ${outPath} (${buf.length} bytes)`);
});

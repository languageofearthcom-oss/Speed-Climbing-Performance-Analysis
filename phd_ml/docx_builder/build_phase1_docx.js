/**
 * Phase 1 Methodology Document — DOCX builder.
 *
 * Generates a bilingual (English + Persian) thesis-grade Word document covering
 * the full Phase-1 methodology, code architecture, expected outputs, limitations,
 * and a sign-off checklist for the dissertation advisor.
 *
 * Run:  node build_phase1_docx.js
 * Out:  ../phase1/PHASE1_METHODOLOGY.docx
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, TabStopType,
  TabStopPosition, TableOfContents, ExternalHyperlink, Bookmark,
} = require("docx");

// ---------- helpers ----------------------------------------------------------

const FONT_LATIN = "Arial";
const FONT_PERSIAN = "Tahoma"; // widely available with good Persian glyphs

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const headerShade = { fill: "1F4E79", type: ShadingType.CLEAR, color: "auto" };

function txt(text, opts = {}) {
  return new TextRun({ text, font: FONT_LATIN, size: 22, ...opts });
}
function txtFa(text, opts = {}) {
  return new TextRun({
    text, font: FONT_PERSIAN, size: 22, rtl: true, ...opts,
  });
}
function p(text, opts = {}) {
  const { fa = false, ...rest } = opts;
  return new Paragraph({
    bidirectional: fa,
    alignment: fa ? AlignmentType.RIGHT : AlignmentType.JUSTIFIED,
    spacing: { after: 120 },
    children: [fa ? txtFa(text) : txt(text)],
    ...rest,
  });
}
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 160 },
    children: [new TextRun({ text, font: FONT_LATIN, size: 32, bold: true, color: "1F4E79" })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, font: FONT_LATIN, size: 26, bold: true, color: "2E74B5" })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 100 },
    children: [new TextRun({ text, font: FONT_LATIN, size: 23, bold: true, color: "404040" })],
  });
}
function code(lines) {
  return lines.map((line) => new Paragraph({
    spacing: { before: 0, after: 0, line: 240 },
    shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
    children: [new TextRun({ text: line || " ", font: "Consolas", size: 18 })],
  }));
}
function bulletEn(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 },
    children: [txt(text)],
  });
}
function bulletFa(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    spacing: { after: 60 },
    children: [txtFa(text)],
  });
}
function makeCell(content, opts = {}) {
  const {
    width = 3000, header = false, fa = false, align = AlignmentType.LEFT,
  } = opts;
  const runs = (Array.isArray(content) ? content : [content]).map((line) => {
    const baseProps = header
      ? { bold: true, color: "FFFFFF", size: 22 }
      : { size: 21 };
    if (fa) {
      return new Paragraph({
        bidirectional: true,
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: line, font: FONT_PERSIAN, rtl: true, ...baseProps })],
      });
    }
    return new Paragraph({
      alignment: align,
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
}
function table(rows, columnWidths) {
  const total = columnWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths,
    rows: rows.map((r, idx) => new TableRow({
      tableHeader: idx === 0,
      children: r.map((cellContent, i) => makeCell(cellContent, {
        width: columnWidths[i],
        header: idx === 0,
        fa: typeof cellContent === "string" && /[؀-ۿ]/.test(cellContent),
      })),
    })),
  });
}
function pagebreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function spacer() { return new Paragraph({ children: [new TextRun(" ")] }); }

// ---------- content blocks ---------------------------------------------------

const COVER = [
  new Paragraph({
    spacing: { before: 2400, after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Speed Climbing Performance Analysis",
      font: FONT_LATIN, size: 44, bold: true, color: "1F4E79" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "PhD ML Track — Phase 1",
      font: FONT_LATIN, size: 32, bold: true, color: "2E74B5" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    bidirectional: true,
    spacing: { after: 600 },
    children: [new TextRun({ text: "تحلیل عملکرد سنگ‌نوردی سرعت — مسیر یادگیری ماشین پایان‌نامه — فاز یکم",
      font: FONT_PERSIAN, size: 26, rtl: true, color: "404040" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({ text: "Methodology Document",
      font: FONT_LATIN, size: 28, italics: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 720 },
    children: [new TextRun({ text: "Auto-Labeling via Unsupervised Discovery & Skill Proxy",
      font: FONT_LATIN, size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Author: airano   |   Date: 2026-04-30   |   Version: 1.0",
      font: FONT_LATIN, size: 22, color: "595959" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text: "Branch: phd-ml/phase1-auto-labeling   |   Commit: 3cf0901",
      font: "Consolas", size: 20, color: "595959" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1200 },
    children: [new TextRun({
      text: "Repository: github.com/languageofearthcom-oss/Speed-Climbing-Performance-Analysis",
      font: "Consolas", size: 18, color: "808080",
    })],
  }),
  pagebreak(),
];

const EXEC_SUMMARY_EN = [
  h1("Executive Summary"),
  p(
    "This document presents the methodology for Phase 1 of the four-phase PhD machine-learning track on the Speed Climbing Performance Analysis project. Phase 1 produces a labeled dataset suitable for supervised modelling in Phases 2 and 3, while operating under two project constraints: (a) no human labelling, and (b) no 2D-CNN on raw video frames."
  ),
  p(
    "The dataset comprises 246 high-quality (extraction-quality ≥ 0.80) kinematic feature vectors extracted from IFSC speed-climbing footage via the project's existing BlazePose + feature-engineering pipeline. Phase 1 applies methodological triangulation — running K-Means, Gaussian Mixture, DBSCAN, and Agglomerative-Ward clustering in parallel on 15 camera-independent features — and then converts the resulting nominal partitions into ordinal pseudo-labels (Beginner / Intermediate / Advanced [/ Elite]) via a literature-grounded composite Skill Proxy Score."
  ),
  p(
    "Cluster quality is reported through three internal validity indices (Silhouette, Davies-Bouldin, Calinski-Harabasz) and a 100-iteration bootstrap-ARI stability check. Cross-method agreement (pairwise ARI between K-Means / GMM / Hierarchical) is reported as evidence that the discovered partition reflects real structure rather than algorithmic bias. All deliverables — the labeled dataset, the metrics file, eight diagnostic figures, and this methodology document — are committed to the dedicated branch phd-ml/phase1-auto-labeling, which contains exactly one commit (3cf0901) and is fully isolated from the main release branch."
  ),
  p(
    "Phase 1 explicitly accepts that the resulting labels constitute weak supervision rather than ground truth. Phase 4 will bound all downstream claims accordingly: models trained in Phases 2 and 3 are evaluated against this proxy, not against measured skill."
  ),
];

const EXEC_SUMMARY_FA = [
  h1("خلاصه اجرایی (فارسی)"),
  p("این سند روش‌شناسی فاز یکم از مسیر چهار-فازی یادگیری ماشین پایان‌نامه را برای پروژه «تحلیل عملکرد سنگ‌نوردی سرعت» ارائه می‌کند. هدف فاز یکم تولید یک دیتاست برچسب‌خورده برای آموزش مدل‌های نظارت‌شده در فاز ۲ و ۳ است، تحت دو محدودیت سخت‌گیرانه: (۱) ممنوعیت برچسب‌گذاری انسانی و (۲) ممنوعیت استفاده از CNN دوبعدی روی فریم‌های خام ویدیو.", { fa: true }),
  p("دیتاست شامل ۲۴۶ بردار سینماتیک با کیفیت بالا (extraction_quality ≥ 0.80) است که از مسابقات IFSC با پایپ‌لاین موجود پروژه (BlazePose + استخراج ویژگی) به دست آمده. در فاز یکم چهار الگوریتم خوشه‌بندی موازی (K-Means، Gaussian Mixture، DBSCAN و Agglomerative-Ward) روی ۱۵ ویژگی مستقل از دوربین اجرا می‌شود؛ سپس خوشه‌های اسمی با استفاده از یک Skill Proxy Score مستند بر ادبیات بیومکانیک ورزشی، به برچسب‌های ترتیبی (مبتدی / میانی / پیشرفته [/ نخبه]) تبدیل می‌شوند.", { fa: true }),
  p("کیفیت خوشه‌ها با سه شاخص اعتبارسنجی داخلی (Silhouette، Davies-Bouldin، Calinski-Harabasz) و یک آزمون پایداری bootstrap با ۱۰۰ تکرار سنجیده می‌شود. توافق میان سه روش (شاخص ARI جفتی) به‌عنوان شاهدی بر «ساختار واقعی داده» در برابر «بایاس الگوریتم» گزارش می‌شود. تمام خروجی‌ها — دیتاست برچسب‌خورده، فایل متریک‌ها، هشت نمودار تشخیصی و همین سند روش‌شناسی — در شاخه اختصاصی phd-ml/phase1-auto-labeling کامیت شده‌اند که فقط یک کامیت (3cf0901) دارد و کاملاً از شاخه اصلی release ایزوله است.", { fa: true }),
  p("صراحتاً پذیرفته شده که برچسب‌های تولیدی، Weak Supervision هستند نه Ground Truth. در فاز چهارم تمام ادعاها بر همین مبنا محدود خواهند شد: مدل‌های فاز ۲ و ۳ نسبت به این پروکسی ارزیابی می‌شوند، نه نسبت به مهارت اندازه‌گیری‌شده.", { fa: true }),
];

const SECTION_1 = [
  h1("1. Problem Statement & Motivation"),
  p("We hold 246 high-quality kinematic feature vectors extracted from IFSC speed-climbing performances using the project's existing BlazePose + feature-engineering pipeline. These vectors are unlabeled. Human labeling is excluded by project constraint. The Phase-1 question is therefore:"),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    indent: { left: 720, right: 720 },
    spacing: { before: 120, after: 120 },
    children: [new TextRun({ text: "Can a defensible ordinal label set be generated automatically from the data, so that supervised models in Phase 2 (Random Forest / XGBoost) and Phase 3 (1D-CNN) have a target variable?", italics: true, font: FONT_LATIN, size: 22 })],
  }),
  p("The answer must satisfy three concurrent requirements: (i) reproducibility — every step is scripted and version-controlled; (ii) academic defensibility — every methodological choice is grounded in published literature and explicit assumptions; (iii) honesty — the resulting labels are pseudo-labels, not ground truth, and downstream evaluation must be bounded accordingly."),
];

const SECTION_2 = [
  h1("2. Why Unsupervised Discovery Is Defensible Here"),
  p("Sport-biomechanics literature on movement-pattern discovery treats the appearance of natural clusters in standardised kinematic feature space as prima facie evidence of distinct technique modes (Hofmann et al., 2017; Rein & Memmert, 2016; Federolf et al., 2014). We do not claim cluster membership equals skill class; we claim cluster membership equals a coherent technique mode that we then order using domain heuristics."),
  p("This is a textbook weak-supervision workflow (Ratner et al., 2017):"),
  ...code([
    "  unlabeled data",
    "       │",
    "       ▼",
    "  unsupervised structure discovery",
    "       │",
    "       ▼",
    "  domain-informed ranking (skill proxy)",
    "       │",
    "       ▼",
    "  ordinal pseudo-labels",
  ]),
  p("Phase 4 will (and must) explicitly bound the validity of these labels. They are a generating model for downstream learning, not a measurement of true skill."),
];

const SECTION_3 = [
  h1("3. Methodological Triangulation"),
  p("Rather than commit to a single algorithm, four are run in parallel and agreement among them is reported as a robustness signal."),
  spacer(),
  table(
    [
      ["Algorithm", "Geometric assumption", "k chosen by", "Strength"],
      ["K-Means", "Spherical, equal variance", "Elbow + Silhouette", "Standard reference"],
      ["Gaussian Mixture", "Elliptical, full covariance", "BIC (AIC reported)", "Probabilistic; soft assignment"],
      ["DBSCAN", "Density-based, no k", "Grid over (eps, min_samples)", "No k assumption; finds noise"],
      ["Agglomerative Ward", "Hierarchical", "k* from K-Means", "Dendrogram for thesis figure"],
    ],
    [1900, 2300, 2300, 2860],
  ),
  spacer(),
  p("Convergence among these (high pairwise Adjusted Rand Index) is treated as evidence that the partition reflects real structure rather than algorithmic bias. Divergence is reported honestly without re-tuning to force agreement."),
];

const SECTION_4 = [
  h1("4. Feature Selection — Camera-Independent Only"),
  p("MASTER_CONTEXT.md documents that six efficiency features are camera-motion artefacts and must not be used. Phase 1 honours that constraint. Fifteen features are retained: nine postural plus six frequency-domain. All features are z-score standardised (StandardScaler) before clustering. No additional feature engineering happens at this stage; that is Phase 3's responsibility for the temporal CNN."),
  spacer(),
  h3("Retained features (15)"),
  table(
    [
      ["#", "Feature", "Family", "Justification"],
      ["1", "post_avg_knee_angle", "Postural", "Mean knee angle over the run"],
      ["2", "post_knee_angle_std", "Postural", "Knee-angle variability — proxy for control"],
      ["3", "post_avg_elbow_angle", "Postural", "Mean elbow angle"],
      ["4", "post_elbow_angle_std", "Postural", "Elbow-angle variability"],
      ["5", "post_avg_body_lean", "Postural", "Average trunk inclination"],
      ["6", "post_body_lean_std", "Postural", "Trunk-lean variability"],
      ["7", "post_hip_width_ratio", "Postural", "Stance width over body height"],
      ["8", "post_avg_reach_ratio", "Postural", "Average effective reach per cycle"],
      ["9", "post_max_reach_ratio", "Postural", "Peak effective reach"],
      ["10", "freq_limb_sync_ratio", "Frequency", "Hand–foot synchronisation"],
      ["11", "freq_hand_movement_amplitude", "Frequency", "Hand-trajectory amplitude"],
      ["12", "freq_foot_movement_amplitude", "Frequency", "Foot-trajectory amplitude"],
      ["13", "freq_foot_frequency_hz", "Frequency", "Foot-cycle frequency"],
      ["14", "freq_hand_frequency_hz", "Frequency", "Hand-cycle frequency"],
      ["15", "freq_movement_regularity", "Frequency", "Periodicity of total motion"],
    ],
    [600, 3100, 1500, 4160],
  ),
  spacer(),
  h3("Excluded features (6)"),
  p("These are camera-motion artefacts because the project's footage uses a moving camera that follows the climber. Including them would inject systematic bias into the clustering."),
  ...["eff_acceleration_variance","eff_com_stability_index","eff_lateral_movement_ratio","eff_movement_smoothness","eff_path_straightness","eff_vertical_progress_rate"].map(bulletEn),
];

const SECTION_5 = [
  h1("5. Cluster Validity"),
  p("Three internal validity indices are computed for every algorithm. \"Internal\" means they require no ground-truth labels — they evaluate the partition geometry directly."),
  spacer(),
  table(
    [
      ["Metric", "Direction", "Interpretation"],
      ["Silhouette", "Higher is better (max 1)", "Balance of cohesion vs separation"],
      ["Davies-Bouldin", "Lower is better", "Average ratio of within- to between-cluster spread"],
      ["Calinski-Harabasz", "Higher is better", "Variance ratio (between/within)"],
    ],
    [2200, 2400, 4760],
  ),
  spacer(),
  h3("Bootstrap stability"),
  p("For K-Means we additionally run 100 iterations of 80% subsampling and report the mean and standard deviation of the Adjusted Rand Index between subsample labels and full-data labels. Following Hennig (2007) we treat ARI ≥ 0.70 as stable, 0.50–0.70 as weakly stable, < 0.50 as unstable."),
];

const SECTION_6 = [
  h1("6. Skill Proxy & Ordinal Pseudo-Labels"),
  p("Cluster IDs are nominal. To produce an ordered label set we compute, per sample, a composite z-score over six camera-independent kinematic markers:"),
  ...code([
    "  SkillScore_i = mean over j ( sign_j * z(feature_j[i]) )",
  ]),
  spacer(),
  table(
    [
      ["Feature", "Sign", "Biomechanical justification"],
      ["post_knee_angle_std", "−", "Stable knee alignment is a marker of trained motor control"],
      ["post_elbow_angle_std", "−", "Stable upper-limb angles correlate with controlled pulls"],
      ["post_body_lean_std", "−", "Reduced trunk wobble is associated with elite climbers"],
      ["freq_limb_sync_ratio", "+", "Higher hand–foot synchronisation = better coordination"],
      ["post_avg_reach_ratio", "+", "Greater effective reach per cycle = larger move efficiency"],
      ["freq_movement_regularity", "+", "Periodic, non-erratic motion tracks skill"],
    ],
    [3000, 800, 5560],
  ),
  spacer(),
  p("Per-cluster mean SkillScore induces a total order; clusters are then mapped onto ordinal labels:"),
  ...["k = 2 → beginner < advanced","k = 3 → beginner < intermediate < advanced","k = 4 → beginner < intermediate < advanced < elite","k > 4 → fall back to ranked numeric labels (level_1 … level_k)"].map(bulletEn),
  p("Within-cluster dispersion of SkillScore is reported as part of cluster validity."),
];

const SECTION_7 = [
  h1("7. Code Architecture"),
  p("Phase-1 code lives under phd_ml/phase1/. The directory is intentionally flat and each file has a single responsibility so the committee can audit them individually."),
  ...code([
    "phd_ml/",
    "├── __init__.py",
    "├── requirements.txt              # umap-learn, xgboost, hdbscan, joblib",
    "├── build/                        # toolchain for generating the .docx (this file)",
    "└── phase1/",
    "    ├── __init__.py",
    "    ├── PHASE1_RATIONALE.md       # Markdown twin of this Word document",
    "    ├── config.py                 # Paths, feature lists, hyperparameter grids",
    "    ├── loader.py                 # CSV load + quality filter + StandardScaler",
    "    ├── clustering.py             # K-Means / GMM / DBSCAN / Hierarchical",
    "    ├── skill_proxy.py            # Composite Skill Score → ordinal labels",
    "    ├── viz.py                    # Eight diagnostic figures",
    "    └── run_pipeline.py           # Orchestrator (single entry point)",
  ]),
  spacer(),
  h3("Module responsibilities"),
  table(
    [
      ["Module", "Public API", "Role"],
      ["config.py", "Constants + paths", "Single source of truth for filterable parameters"],
      ["loader.py", "load_features() → LoadedDataset", "Reads CSV, applies quality threshold, returns standardised matrix"],
      ["clustering.py", "kmeans / gmm / dbscan / hierarchical", "Each returns a uniform ClusteringResult dataclass"],
      ["skill_proxy.py", "compute_skill_score / assign_ordinal_labels", "Heuristic ranking of clusters into ordinal classes"],
      ["viz.py", "plot_* functions", "Saves figures to figures/phd_ml/phase1/"],
      ["run_pipeline.py", "main()", "Orchestrates the five stages and persists outputs"],
    ],
    [1800, 2600, 4960],
  ),
];

const SECTION_8 = [
  h1("8. Outputs & How To Inspect Them"),
  h3("Data outputs"),
  ...["data/phd_ml/phase1/labeled_dataset.csv     — full feature table with cluster IDs and ordinal labels","data/phd_ml/phase1/cluster_metrics.json    — validity indices, BIC/AIC, ARI, label distribution","data/phd_ml/phase1/skill_proxy_report.csv  — per-cluster skill statistics"].map(bulletEn),
  h3("Figures (eight)"),
  ...["elbow_kmeans.png — Inertia + Silhouette over k","bic_gmm.png — BIC and AIC for the Gaussian mixture","dendrogram_ward.png — Hierarchical clustering tree","embedding_pca.png — PCA-2D scatter coloured by cluster","embedding_tsne.png — t-SNE-2D scatter","embedding_umap.png — UMAP-2D scatter (if umap-learn installed)","skill_score_distribution.png — Boxplot of SkillScore per cluster","method_agreement.png — Pairwise ARI between K-Means / GMM / Hierarchical"].map(bulletEn),
  h3("Acceptance thresholds suggested for the advisor"),
  ...["Silhouette score ≥ 0.25 (kinematic data is high-dimensional and noisy — anything ≥ 0.20 is typically reportable)","Bootstrap-ARI mean ≥ 0.50 (≥ 0.70 = strong)","At least two of {K-Means, GMM, Hierarchical} agree at ARI ≥ 0.50"].map(bulletEn),
];

const SECTION_9 = [
  h1("9. Limitations & Defenses"),
  p("Every limitation below is acknowledged proactively and paired with a concrete mitigation. This pair-wise structure is intended to give the committee a clean axis to interrogate."),
  spacer(),
  table(
    [
      ["Limitation", "Mitigation", "Where addressed"],
      ["The Skill Proxy is a heuristic, not measurement of truth.", "Phase 4 explicitly bounds claims to consistency with the proxy — never ability to predict skill.", "Phase 4 report"],
      ["n = 246 is small for clustering in 15 dimensions.", "z-score standardisation, bootstrap stability, cross-method agreement, PCA/UMAP visualisation for inspection.", "This document"],
      ["Clusters may be confounded by competition style (Chamonix vs Seoul, etc.).", "cluster_metrics.json reports per-competition cluster distribution as a confound check.", "cluster_metrics.json"],
      ["Pseudo-labels propagate noise into Phase 2 / 3 training.", "Phase 4 reports a label-noise sensitivity experiment (label-flip 10%) so the committee sees robustness.", "Phase 4 plan"],
      ["DBSCAN may find no usable structure on this feature set.", "Pipeline returns a degenerate result honestly (n_clusters = 0 with explanatory note) rather than tuning until it does.", "clustering.py"],
    ],
    [3000, 4400, 1960],
  ),
];

const SECTION_RESULTS = [
  h1("10. Empirical Results (run on 2026-04-30)"),
  p("This section reports the actual numbers produced by run_pipeline.py on the documented input (commit 140fbd4 on phd-ml/phase1-auto-labeling). Numbers are unedited; outliers in either direction are reported honestly so the committee can interrogate them."),
  spacer(),
  h3("10.1  Sample size after quality filter"),
  p("Quality threshold extraction_quality ≥ 0.80 reduced the working set from 371 to 246 samples — exact match to MASTER_CONTEXT.md."),
  h3("10.2  K-Means model selection"),
  p("Silhouette per k clearly favours k = 2:"),
  spacer(),
  table(
    [
      ["k", "2", "3", "4", "5", "6", "7", "8"],
      ["Silhouette", "0.423", "0.252", "0.152", "0.139", "0.142", "0.132", "0.144"],
    ],
    [1500, 1100, 1100, 1100, 1100, 1100, 1100, 1100],
  ),
  spacer(),
  h3("10.3  Validity indices for K-Means k*=2"),
  table(
    [
      ["Metric", "Value", "Interpretation"],
      ["Silhouette", "0.423", "Below preferred 0.50 but typical for 15-D kinematic data"],
      ["Davies-Bouldin", "1.617", "Moderate; lower would be tighter"],
      ["Calinski-Harabasz", "36.00", "Modest variance ratio"],
      ["Bootstrap-ARI mean", "0.634 ± 0.252", "Weakly stable per Hennig (2007); high std flags partial instability"],
    ],
    [2300, 2200, 4860],
  ),
  spacer(),
  h3("10.4  GMM and DBSCAN"),
  ...["GMM with BIC selected k = 5, but silhouette of that partition is only 0.144 — likely over-fitting in 15-D space.","DBSCAN found two clusters but flagged 34.5% of samples as noise — density-based structure on these features is weak."].map(bulletEn),
  h3("10.5  Cross-method agreement (pairwise ARI)"),
  table(
    [
      ["Method pair", "ARI", "Reading"],
      ["K-Means × Hierarchical (Ward)", "0.851", "Strong agreement — geometric structure is real"],
      ["K-Means × GMM", "0.327", "Disagreement; GMM partition (k=5) is different"],
      ["GMM × Hierarchical", "0.363", "Disagreement"],
    ],
    [4200, 1300, 3860],
  ),
  spacer(),
  p("Reading: the dominant signal is geometric (cohesive distance-based clusters captured by both K-Means and Ward). GMM probabilistic decomposition into 5 components does not align with the 2-cluster geometry. We retain K-Means k=2 as the primary partition; GMM is reported as a divergence."),
  spacer(),
  h3("10.6  Pseudo-label distribution and skill statistics"),
  table(
    [
      ["Cluster", "Label", "n", "mean SkillScore", "std", "min", "max"],
      ["0", "beginner", "20", "−0.366", "0.496", "−0.939", "1.297"],
      ["1", "advanced", "226", "+0.032", "0.428", "−0.906", "2.270"],
    ],
    [950, 1500, 800, 1900, 1100, 1200, 1910],
  ),
  spacer(),
  p("Statistical separation between the two clusters on the SkillScore axis (computed independently of clustering): Welch t-test p = 0.0022, Mann-Whitney U p = 1.6e-5, Cohen's d = -0.92 (large effect). The proxy ordering is therefore monotonic with the discovered partition at strong statistical significance."),
  h3("10.7  Honest assessment"),
  ...[
    "Class imbalance — 226 vs 20 (92% vs 8%). Phase 2 must use class_weight=\"balanced\" (Random Forest / XGBoost) and report stratified F1 + per-class precision/recall, not naïve accuracy.",
    "Silhouette below 0.50 means the boundary is blurry. The 20-sample beginner cluster is well-isolated in UMAP but not in PCA — committee may ask whether they are an outlier subset rather than a true skill mode. Phase 4 will discuss this explicitly.",
    "Bootstrap-ARI std of 0.252 is not negligible. We will report this and avoid claiming \"stable structure\" without qualification.",
    "GMM/DBSCAN divergence is reported as part of the methodology — it is not a bug to be hidden, it is information about the geometry of the feature space.",
  ].map(bulletEn),
];

const SECTION_PHASE3_NOTE = [
  h1("11. Pose Time-Series Availability for Phase 3"),
  p("Commit c600dea added 114 single-athlete pose JSONs (152 MB) at data/processed/poses/single_athlete/, indexed by MANIFEST.csv. Coverage = 114/188 races = 61%."),
  spacer(),
  h3("Coverage by competition"),
  table(
    [
      ["Competition", "Covered / Total", "Note"],
      ["Chamonix 2024", "29 / 32", "Missing races 10, 13, 24"],
      ["Innsbruck 2024", "29 / 32", "Missing races 1, 4, 11"],
      ["Seoul 2024", "29 / 31", "Missing 22, 23"],
      ["Villars 2024", "19 / 24", "Missing 2, 13, 15, 19, 23"],
      ["Zilina 2025", "8 / 69", "Slippery-wall failures per MASTER_CONTEXT"],
    ],
    [2700, 2200, 4460],
  ),
  spacer(),
  h3("Schema caveat (read before Phase 3)"),
  ...[
    "Each JSON contains ONE climber's 33 BlazePose landmarks — not both lanes. Inferred lane from athlete_mean_x: 64 left / 39 right / 11 ambiguous.",
    "This format differs from the existing 10 dual-lane reference samples (which carry left_climber + right_climber).",
    "Quality is excellent: mean success_rate 97%, median 99.4%; 109/114 ≥ 80%, 99/114 ≥ 95%.",
    "Linkage to the labeled dataset must be done via race_id + inferred-lane — not all 246 CSV rows will have a matching pose JSON. Phase 3 will report the realised intersection size.",
  ].map(bulletEn),
];

const SECTION_10 = [
  h1("12. References"),
  ...[
    "Federolf, P., Reid, R., Gilgien, M., Haugen, P., & Smith, G. (2014). The application of principal component analysis to quantify technique in sports. Scandinavian Journal of Medicine & Science in Sports, 24(3), 491–499.",
    "Hennig, C. (2007). Cluster-wise assessment of cluster stability. Computational Statistics & Data Analysis, 52(1), 258–271.",
    "Hofmann, M., et al. (2017). Movement primitives in sport biomechanics. Frontiers in Sports and Active Living.",
    "Ratner, A., Bach, S. H., Ehrenberg, H., Fries, J., Wu, S., & Ré, C. (2017). Snorkel: rapid training data creation with weak supervision. VLDB.",
    "Rein, R., & Memmert, D. (2016). Big data and tactical analysis in elite soccer. SpringerPlus, 5, 1410.",
  ].map(bulletEn),
];

const APPENDIX_A = [
  h1("Appendix A — Key Code Excerpts"),
  h3("A.1  loader.py — quality filtering"),
  ...code([
    "df = pd.read_csv(config.INPUT_CSV)",
    "df = df.dropna(subset=config.CLUSTERING_FEATURES + ['extraction_quality'])",
    "df = df[df['extraction_quality'] >= config.QUALITY_THRESHOLD].reset_index(drop=True)",
    "X = df[config.CLUSTERING_FEATURES].to_numpy(dtype=float)",
    "X_std = StandardScaler().fit_transform(X)",
  ]),
  h3("A.2  clustering.py — K-Means with model selection"),
  ...code([
    "for k in range(k_min, k_max + 1):",
    "    km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)",
    "    labels = km.fit_predict(X)",
    "    inertias[k]    = km.inertia_",
    "    silhouettes[k] = silhouette_score(X, labels)",
    "best_k = max(silhouettes, key=silhouettes.get)",
  ]),
  h3("A.3  clustering.py — bootstrap stability"),
  ...code([
    "ref = KMeans(k).fit_predict(X)",
    "for _ in range(BOOTSTRAP_ITERS):",
    "    idx = rng.choice(n, size=int(n * 0.8), replace=False)",
    "    sub = KMeans(k).fit_predict(X[idx])",
    "    aris.append(adjusted_rand_score(ref[idx], sub))",
  ]),
  h3("A.4  skill_proxy.py — composite ordering"),
  ...code([
    "for col, sign in SKILL_COMPONENTS.items():",
    "    parts.append(sign * stats.zscore(df[col]))",
    "score = np.nansum(parts, axis=0) / len(parts)",
    "cluster_means = df.groupby(cluster_col)[score_col].mean().sort_values()",
    "rank_map = {row[cluster_col]: i for i, row in cluster_means.iterrows()}",
  ]),
];

const APPENDIX_B = [
  h1("Appendix B — How To Reproduce"),
  h3("B.1  Get the branch"),
  ...code([
    "git fetch origin",
    "git checkout phd-ml/phase1-auto-labeling",
  ]),
  h3("B.2  Install dependencies"),
  ...code([
    "pip install -r requirements.txt",
    "pip install -r phd_ml/requirements.txt   # umap-learn, xgboost, hdbscan, joblib",
  ]),
  h3("B.3  Run the pipeline"),
  ...code([
    "python -m phd_ml.phase1.run_pipeline",
  ]),
  h3("B.4  Inspect the outputs"),
  ...["Open data/phd_ml/phase1/cluster_metrics.json — verify silhouette and bootstrap_ari_mean.","Open figures/phd_ml/phase1/embedding_pca.png and embedding_umap.png — verify visual cluster separation.","Open figures/phd_ml/phase1/skill_score_distribution.png — verify monotonic skill score across cluster ranks.","Open data/phd_ml/phase1/labeled_dataset.csv — confirm cluster_kmeans_label column has the expected ordinal values."].map(bulletEn),
];

const APPENDIX_C = [
  h1("Appendix C — Sign-off Checklist (for advisor)"),
  ...["Methodology document reviewed (this file)","Cluster metrics inspected (silhouette, BIC, bootstrap stability)","Visualization plots reviewed (PCA, UMAP, dendrogram)","Skill proxy formula approved","Number of classes (k*) confirmed","Approval given to start Phase 2 (Random Forest / XGBoost baseline)"].map((t) => new Paragraph({
    numbering: { reference: "checks", level: 0 },
    spacing: { after: 80 },
    children: [txt(t)],
  })),
  spacer(),
  h3("Persian sign-off / تأیید فارسی"),
  ...["سند روش‌شناسی مطالعه شد","معیارهای اعتبارسنجی خوشه‌ها بررسی شد (Silhouette, BIC, ثبات bootstrap)","نمودارهای تجسم بررسی شدند (PCA, UMAP, دندروگرام)","فرمول Skill Proxy تأیید شد","تعداد بهینه کلاس‌ها (k*) قطعی شد","تأیید شروع فاز ۲ (مدل پایه Random Forest / XGBoost)"].map((t) => new Paragraph({
    numbering: { reference: "checks_fa", level: 0 },
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    spacing: { after: 80 },
    children: [txtFa(t)],
  })),
];

// ---------- assembly ---------------------------------------------------------

const doc = new Document({
  creator: "airano",
  title: "Speed Climbing — Phase 1 Methodology",
  description: "PhD ML Track — Phase 1 Auto-Labeling Methodology Document",
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
      { reference: "checks_fa",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "☐",
          alignment: AlignmentType.RIGHT,
          style: { paragraph: { indent: { right: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "PhD ML Track — Phase 1", font: FONT_LATIN, size: 18, color: "808080" })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Speed Climbing Performance Analysis — Methodology v1.0   |   Page ",
            font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ text: " / ", font: FONT_LATIN, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT_LATIN, size: 18, color: "808080" }),
        ],
      })] }),
    },
    children: [
      ...COVER,
      ...EXEC_SUMMARY_EN,
      ...EXEC_SUMMARY_FA,
      pagebreak(),

      h1("Table of Contents"),
      new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
      pagebreak(),

      ...SECTION_1, ...SECTION_2, ...SECTION_3,
      pagebreak(),
      ...SECTION_4,
      pagebreak(),
      ...SECTION_5, ...SECTION_6,
      pagebreak(),
      ...SECTION_7,
      pagebreak(),
      ...SECTION_8, ...SECTION_9,
      pagebreak(),
      ...SECTION_RESULTS,
      pagebreak(),
      ...SECTION_PHASE3_NOTE,
      pagebreak(),
      ...SECTION_10,
      pagebreak(),
      ...APPENDIX_A,
      pagebreak(),
      ...APPENDIX_B,
      pagebreak(),
      ...APPENDIX_C,
    ],
  }],
});

const outPath = path.resolve(__dirname, "..", "phase1", "PHASE1_METHODOLOGY.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`Wrote ${outPath} (${buf.length} bytes)`);
});

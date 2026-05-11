/**
 * Comprehensive Persian project guide — for the PhD student and advisor.
 *
 * Covers:
 *   - What was done in Phase 1 and Phase 2 (with embedded figures)
 *   - What Phase 3 and Phase 4 mean and how they will be executed
 *   - Critical findings (Phase 2 tautology caveat, Phase 3 minority bottleneck)
 *   - Open decisions before Phase 3 execution
 *   - Glossary
 *
 * Run:  node build_project_guide_docx.js
 * Out:  ../../PROJECT_GUIDE_FA.docx (at repository root)
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, TableOfContents,
} = require("docx");

const FONT = "Tahoma";

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const FIG_P1 = path.join(REPO_ROOT, "figures", "phd_ml", "phase1");
const FIG_P2 = path.join(REPO_ROOT, "figures", "phd_ml", "phase2");

// ---------- helpers ---------------------------------------------------------

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const headerShade = { fill: "1F4E79", type: ShadingType.CLEAR, color: "auto" };
const cautionShade = { fill: "FFF4E5", type: ShadingType.CLEAR, color: "auto" };

const fa = (t, o = {}) => new TextRun({
  text: t, font: FONT, size: 22, rtl: true, ...o,
});

const pFa = (t, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: 120, line: 360 },
  children: [fa(t, o)],
});

const calloutFa = (label, body) => new Paragraph({
  bidirectional: true,
  alignment: AlignmentType.RIGHT,
  spacing: { before: 120, after: 160, line: 360 },
  shading: cautionShade,
  border: {
    left: { style: BorderStyle.SINGLE, size: 18, color: "E67E22", space: 6 },
  },
  indent: { right: 240, left: 240 },
  children: [
    new TextRun({ text: `${label}: `, font: FONT, rtl: true, size: 22, bold: true, color: "B7510B" }),
    new TextRun({ text: body, font: FONT, rtl: true, size: 22 }),
  ],
});

const h1Fa = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 320, after: 200 },
  children: [new TextRun({ text: t, font: FONT, size: 32, bold: true, color: "1F4E79", rtl: true })],
});
const h2Fa = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 240, after: 160 },
  children: [new TextRun({ text: t, font: FONT, size: 26, bold: true, color: "2E74B5", rtl: true })],
});
const h3Fa = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { before: 180, after: 120 },
  children: [new TextRun({ text: t, font: FONT, size: 23, bold: true, color: "404040", rtl: true })],
});

const bulletFa = (t) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { after: 80, line: 340 },
  children: [fa(t)],
});

const spacer = () => new Paragraph({ children: [new TextRun(" ")] });
const pagebreak = () => new Paragraph({ children: [new PageBreak()] });

const cellFa = (t, opts = {}) => {
  const { width = 3000, header = false, color } = opts;
  const baseProps = header
    ? { bold: true, color: "FFFFFF", size: 22 }
    : { size: 21, ...(color ? { color } : {}) };
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: header ? headerShade : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      bidirectional: true, alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: t, font: FONT, rtl: true, ...baseProps })],
    })],
  });
};

const tableFa = (rows, columnWidths) => {
  const total = columnWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((cell, j) => cellFa(cell, {
        width: columnWidths[j], header: i === 0,
      })),
    })),
  });
};

const figure = (figDir, filename, captionFa, opts = {}) => {
  const { width = 540, height = 350 } = opts;
  const filePath = path.join(figDir, filename);
  if (!fs.existsSync(filePath)) {
    return [pFa(`[تصویر یافت نشد: ${filename}]`, { color: "CC0000" })];
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 80 },
      children: [new ImageRun({
        type: "png",
        data: fs.readFileSync(filePath),
        transformation: { width, height },
        altText: { title: filename, description: captionFa, name: filename },
      })],
    }),
    new Paragraph({
      bidirectional: true, alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
      children: [new TextRun({
        text: `شکل — ${captionFa}`, font: FONT, rtl: true, size: 20,
        italics: true, color: "595959",
      })],
    }),
  ];
};

// ---------- content ---------------------------------------------------------

const COVER = [
  new Paragraph({
    spacing: { before: 2400, after: 240 }, alignment: AlignmentType.CENTER,
    bidirectional: true,
    children: [new TextRun({
      text: "راهنمای جامع پروژه",
      font: FONT, size: 44, bold: true, color: "1F4E79", rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    spacing: { after: 120 },
    children: [new TextRun({
      text: "تحلیل عملکرد سنگ‌نوردی سرعت با یادگیری ماشین",
      font: FONT, size: 32, bold: true, color: "2E74B5", rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
    children: [new TextRun({
      text: "Speed Climbing Performance Analysis",
      font: "Arial", size: 24, italics: true, color: "595959",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    spacing: { after: 120 },
    children: [new TextRun({
      text: "گزارش نتایج فاز ۱ و ۲ + راهنمای فاز ۳ و ۴",
      font: FONT, size: 24, rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    spacing: { after: 720 },
    children: [new TextRun({
      text: "(سند جامع برای دانشجو و استاد)",
      font: FONT, size: 22, italics: true, color: "595959", rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    children: [new TextRun({
      text: "نگارنده: airano  |  تاریخ: ۲۰۲۶/۰۵/۱۱  |  نسخه: ۲.۰",
      font: FONT, size: 22, color: "595959", rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({
      text: "github.com/languageofearthcom-oss/Speed-Climbing-Performance-Analysis",
      font: "Consolas", size: 18, color: "808080",
    })],
  }),
  pagebreak(),
];

const EXEC = [
  h1Fa("خلاصه اجرایی"),
  pFa("این سند جامع، وضعیت پروژه‌ی تحلیل عملکرد سنگ‌نوردی سرعت با یادگیری ماشین را در تاریخ نگارش جمع‌بندی می‌کند. پروژه در چهار فاز طراحی شده: فاز ۱ تولید برچسب خودکار با خوشه‌بندی بدون نظارت، فاز ۲ آموزش مدل‌های سنتی پایه با مدیریت عدم‌توازن کلاس، فاز ۳ آموزش شبکه عصبی 1D-CNN روی سری زمانی نقاط بدن، و فاز ۴ گزارش مقایسه‌ای علمی نهایی."),
  pFa("تا این لحظه: فاز ۱ و ۲ اجرا و کامیت شده‌اند. فاز ۳ به‌صورت scaffold روی شاخه‌ی phd-ml/phase3-cnn آماده‌ی اجراست. فاز ۴ هنوز شروع نشده."),
  pFa("نتیجه‌ی برجسته‌ی فاز ۱: ساختار باینری در داده وجود دارد (Macro K-Means × Hierarchical ARI = ۰٫۸۵)، اما با عدم‌توازن شدید کلاس (۲۲۶ پیشرفته در برابر ۲۰ مبتدی). نتیجه‌ی برجسته‌ی فاز ۲: بهترین مدل (logreg_balanced) به Macro-F1 = ۰٫۹۷۸ رسید، اما این یک سقف tautological است نه دستاورد — برچسب‌های فاز ۱ از همان فیچرهایی ساخته شده‌اند که ورودی فاز ۲ هستند، و این موضوع آزمون واقعی پروژه را به فاز ۳ منتقل می‌کند."),
  pFa("آزمون واقعی فاز ۳: آیا یک 1D-CNN که از داده‌ی خام نقاط بدن (و نه فیچرهای مهندسی‌شده) تغذیه می‌شود می‌تواند همان پارتیشن را بازیابی کند؟ Scaffold فاز ۳ نشان داد فقط ۱۳ نمونه‌ی مبتدی پس از intersect با فایل‌های پوز باقی می‌ماند — این تنگنای واقعی‌ای است که در ادامه‌ی این سند به آن می‌پردازیم."),
];

const NAV = [
  h1Fa("نقشه‌راه و مرور سریع"),
  spacer(),
  tableFa(
    [
      ["فاز", "موضوع", "وضعیت"],
      ["۱", "تولید برچسب خودکار (Unsupervised)", "اجرا شد، نتایج کامیت شدند، در انتظار تأیید استاد"],
      ["۲", "مدل‌های سنتی پایه (RF/XGB با مدیریت عدم‌توازن)", "اجرا شد، نتایج کامیت شدند، در انتظار تأیید استاد"],
      ["۳", "1D-CNN روی سری زمانی نقاط بدن", "Scaffold آماده، دو تصمیم باز قبل از اجرا"],
      ["۴", "گزارش مقایسه‌ای علمی نهایی", "شروع نشده — پس از فاز ۳"],
    ],
    [700, 4700, 4060],
  ),
  spacer(),
  pFa("بخش‌های این سند:"),
  bulletFa("فصل ۱ — فاز ۱: چه شد، نتایج، تصاویر"),
  bulletFa("فصل ۲ — فاز ۲: چه شد، نتایج، تصاویر، caveat حیاتی"),
  bulletFa("فصل ۳ — فاز ۳: چیست، scaffold، تصمیم‌های باز"),
  bulletFa("فصل ۴ — فاز ۴: چیست، چطور انجام می‌شود"),
  bulletFa("فصل ۵ — توصیه‌های مشخص برای دانشجو و استاد"),
  bulletFa("ضمیمه — واژه‌نامه‌ی فنی فارسی-انگلیسی"),
];

// ===== CHAPTER 1: PHASE 1 ==================================================

const PHASE1 = [
  h1Fa("فصل ۱ — فاز یکم: تولید برچسب خودکار"),
  h2Fa("۱.۱  مسئله و چرا یادگیری بدون نظارت؟"),
  pFa("ما ۲۴۶ نمونه‌ی باکیفیت (extraction_quality ≥ ۰٫۸) از مسابقات IFSC داریم که هیچ‌کدام برچسب «مهارت» ندارند. لیبل‌گذاری دستی هم در محدودیت‌های پروژه ممنوع است. در ادبیات بیومکانیک ورزشی، وقتی نمونه‌ها به‌طور طبیعی در فضای ویژگی‌های سینماتیک به خوشه‌های جدا تقسیم می‌شوند، آن را شاهدی می‌گیرند بر وجود سبک‌های حرکتی متمایز. ما خوشه‌ها را با چهار الگوریتم موازی پیدا کردیم و سپس بر اساس یک معیار بیومکانیکی، مرتبه (مبتدی / پیشرفته) به آن‌ها زدیم."),

  h2Fa("۱.۲  مراحل اجرایی"),
  bulletFa("بارگذاری CSV ویژگی‌ها و فیلتر کیفیت ≥ ۰٫۸ → ۲۴۶ نمونه باقی می‌ماند (دقیقاً مطابق MASTER_CONTEXT)"),
  bulletFa("استانداردسازی z-score روی ۱۵ ویژگی مستقل از حرکت دوربین"),
  bulletFa("اجرای چهار الگوریتم خوشه‌بندی به‌موازات یکدیگر: K-Means، Gaussian Mixture، DBSCAN، Agglomerative Ward"),
  bulletFa("اعتبارسنجی با سه شاخص داخلی (Silhouette، Davies-Bouldin، Calinski-Harabasz)"),
  bulletFa("آزمون پایداری Bootstrap با ۱۰۰ تکرار روی K-Means"),
  bulletFa("محاسبه‌ی توافق میان روش‌ها با شاخص ARI"),
  bulletFa("ساخت Skill Proxy Score با شش معیار بیومکانیکی برای رتبه‌بندی خوشه‌ها"),
  bulletFa("نگاشت خوشه‌ها به برچسب ترتیبی: مبتدی / پیشرفته"),

  h2Fa("۱.۳  نتایج عددی"),
  spacer(),
  tableFa(
    [
      ["معیار", "مقدار", "تفسیر"],
      ["Silhouette (K-Means k=۲)", "۰٫۴۲۳", "متوسط — زیر هدف ۰٫۵ ولی برای داده‌ی ۱۵-بعدی سینماتیک قابل‌قبول"],
      ["Bootstrap-ARI", "۰٫۶۳۴ ± ۰٫۲۵۲", "پایداری متوسط، انحراف معیار بالا یعنی دامنه‌ی ناپایداری"],
      ["K-Means × Hierarchical (Ward)", "ARI = ۰٫۸۵۱", "توافق قوی — ساختار geometric واقعی است"],
      ["K-Means × GMM", "ARI = ۰٫۳۲۷", "ناهماهنگی — GMM با k=۵ ساختار دیگری دیده"],
      ["DBSCAN", "۳۴٫۵٪ نویز", "ساختار density ضعیف؛ کلاس‌ها بر اساس فاصله بهتر تعریف می‌شوند"],
      ["توزیع کلاس", "۲۲۶ پیشرفته / ۲۰ مبتدی", "عدم‌توازن شدید (۹۲٪ / ۸٪)"],
      ["جدایی Skill Score", "Cohen's d = -۰٫۹۲", "اثر بزرگ آماری — برچسب‌ها از نظر معیار بیومکانیکی واقعاً متمایزند"],
    ],
    [2400, 2400, 4460],
  ),
  pFa("نتیجه‌گیری: ساختار دو-کلاسه واقعی است، اما عدم‌توازن کلاس‌ها مشکل اصلی فازهای بعدی خواهد بود."),
];

const PHASE1_FIGURES = [
  h2Fa("۱.۴  تصاویر تشخیصی فاز ۱"),
  pFa("هشت نمودار در figures/phd_ml/phase1/ تولید شدند. در ادامه هر کدام را با توضیح ساده می‌بینید:"),

  h3Fa("۱.۴.۱  انتخاب تعداد خوشه‌ها در K-Means"),
  pFa("سؤال: چند خوشه بسازیم؟ پاسخ از روی Inertia (مجموع مربعات فاصله) و Silhouette به‌دست می‌آید. در داده‌ی ما k=۲ به‌وضوح بهترین Silhouette را دارد."),
  ...figure(FIG_P1, "elbow_kmeans.png", "Inertia و Silhouette به ازای k در K-Means", { width: 540, height: 348 }),

  h3Fa("۱.۴.۲  انتخاب تعداد مؤلفه‌های GMM"),
  pFa("معیار اطلاعاتی BIC و AIC. GMM با k=۵ کمترین BIC را داد، اما Silhouette آن فقط ۰٫۱۴ شد — احتمالاً over-fit است."),
  ...figure(FIG_P1, "bic_gmm.png", "BIC و AIC به ازای تعداد مؤلفه‌های GMM", { width: 540, height: 348 }),

  h3Fa("۱.۴.۳  درخت سلسله‌مراتبی Ward"),
  pFa("درخت Dendrogram. شکست واضح در ارتفاع بالا، دو خوشه‌ی اصلی را تأیید می‌کند."),
  ...figure(FIG_P1, "dendrogram_ward.png", "درخت خوشه‌بندی سلسله‌مراتبی Ward", { width: 540, height: 220 }),

  h3Fa("۱.۴.۴  تجسم PCA، t-SNE، UMAP"),
  pFa("سه روش کاهش بُعد برای دیدن خوشه‌ها در فضای دوبعدی. UMAP بهترین جدایی را برای خوشه‌ی مبتدی نشان می‌دهد:"),
  ...figure(FIG_P1, "embedding_pca.png", "تجسم PCA — جدایی متوسط خطی", { width: 460, height: 390 }),
  ...figure(FIG_P1, "embedding_tsne.png", "تجسم t-SNE — جدایی غیرخطی محلی", { width: 460, height: 390 }),
  ...figure(FIG_P1, "embedding_umap.png", "تجسم UMAP — قوی‌ترین شاهد بصری برای ساختار دو-کلاسه", { width: 460, height: 390 }),

  h3Fa("۱.۴.۵  توزیع Skill Score در خوشه‌ها"),
  pFa("اگر نگاشت خوشه به برچسب ترتیبی درست باشد، خوشه‌ی پیشرفته باید به‌طور سیستماتیک Skill Score بالاتری داشته باشد. این رابطه برقرار است (Cohen's d = ۰٫۹۲، اثر بزرگ)."),
  ...figure(FIG_P1, "skill_score_distribution.png", "توزیع Skill Proxy Score درون هر خوشه", { width: 540, height: 348 }),

  h3Fa("۱.۴.۶  توافق میان روش‌های خوشه‌بندی"),
  pFa("شاخص ARI بین جفت‌های روش‌ها. توافق K-Means و Ward روی ۰٫۸۵، توافق GMM با دیگران حدود ۰٫۳۳."),
  ...figure(FIG_P1, "method_agreement.png", "توافق میان روش‌های خوشه‌بندی (پایداری ساختار)", { width: 540, height: 314 }),
];

// ===== CHAPTER 2: PHASE 2 ==================================================

const PHASE2 = [
  h1Fa("فصل ۲ — فاز دوم: مدل‌های پایه با مدیریت عدم‌توازن"),
  h2Fa("۲.۱  چالش اصلی"),
  pFa("توزیع کلاس‌ها ۲۲۶ به ۲۰ شد (۹۲٪ به ۸٪). یعنی اگر مدلی برای همه‌ی نمونه‌ها بگوید «پیشرفته»، به دقت ۹۱٫۹٪ می‌رسد — بدون اینکه حتی یک مبتدی را تشخیص دهد. **دقت خام (accuracy) برای ما بی‌معنا است** و باید با معیارهای مناسب کلاس کمیاب کار کنیم."),

  h2Fa("۲.۲  شش مدل که اجرا شدند"),
  spacer(),
  tableFa(
    [
      ["نام مدل", "نوع", "استراتژی عدم‌توازن"],
      ["dummy_majority", "Trivial", "هیچ — کف منطقی"],
      ["logreg_balanced", "Linear", "وزن کلاس متعادل"],
      ["rf_balanced", "Random Forest", "وزن کلاس متعادل"],
      ["xgb_scale_pos_weight", "XGBoost", "scale_pos_weight=۱۱٫۳"],
      ["rf_smote", "Random Forest", "SMOTE روی fold آموزش"],
      ["xgb_smote", "XGBoost", "SMOTE روی fold آموزش"],
    ],
    [2900, 2300, 4360],
  ),

  h2Fa("۲.۳  نتایج عددی (Stratified-5-Fold CV)"),
  spacer(),
  tableFa(
    [
      ["مدل", "Macro-F1", "F1 مبتدی", "ROC-AUC", "PR-AUC"],
      ["dummy_majority", "۰٫۴۷۹ ± ۰٫۰۰۰", "۰٫۰۰۰", "۰٫۵۰", "۰٫۰۸"],
      ["logreg_balanced ★", "۰٫۹۷۸ ± ۰٫۰۴۵", "۰٫۹۶۰ ± ۰٫۰۸۰", "۱٫۰۰", "۱٫۰۰"],
      ["rf_balanced", "۰٫۹۴۹ ± ۰٫۰۷۰", "۰٫۹۰۵ ± ۰٫۱۳۱", "۱٫۰۰", "۰٫۹۹"],
      ["xgb_scale_pos_weight", "۰٫۹۷۲ ± ۰٫۰۳۴", "۰٫۹۴۹ ± ۰٫۰۶۳", "۱٫۰۰", "۱٫۰۰"],
      ["rf_smote", "۰٫۹۶۹ ± ۰٫۰۳۸", "۰٫۹۴۳ ± ۰٫۰۷۰", "۱٫۰۰", "۰٫۹۹"],
      ["xgb_smote", "۰٫۹۷۲ ± ۰٫۰۳۴", "۰٫۹۴۹ ± ۰٫۰۶۳", "۱٫۰۰", "۱٫۰۰"],
    ],
    [2600, 1700, 1700, 1700, 1700],
  ),
  spacer(),
  pFa("Pooled confusion (همه‌ی foldها روی هم): logreg تمام ۲۰ مبتدی را گرفت با ۲ FP — بهترین recall. XGB ۱۹ از ۲۰ را گرفت با ۱ FP. RF محافظه‌کارتر است (۱۷-۱۸ از ۲۰، صفر FP)."),
  pFa("Top features مشترک بین permutation و native: `post_body_lean_std` (غالب)، `post_avg_body_lean`، `freq_foot_movement_amplitude`، `post_max_reach_ratio`، `post_elbow_angle_std`. این با Cohen's d = -۰٫۹۲ روی body lean در فاز ۱ هم‌خوانی دارد."),

  h2Fa("۲.۴  کشف حیاتی — Tautology Caveat"),
  calloutFa("هشدار", "ROC-AUC=۱٫۰۰۰ یک سقف تاتولوژیک است نه دستاورد. برچسب‌های K-Means فاز ۱ از همان ۱۵ ویژگی‌ای ساخته شده‌اند که الان به‌عنوان ورودی فاز ۲ استفاده می‌شوند. این مدل‌ها دارند یک پارتیشن قطعی از فضای فیچر را reverse-engineer می‌کنند، نه پیش‌بینی از شواهد مستقل."),
  pFa("پیامد این کشف:"),
  bulletFa("هر مدلی با ظرفیت کافی روی این ۱۵ فیچر به نزدیک ۱٫۰ خواهد رسید — این یک ویژگی ریاضی است، نه قدرت یادگیری مدل"),
  bulletFa("آزمون واقعی پروژه به فاز ۳ منتقل شده: آیا CNN از داده‌ی متفاوت (raw pose time-series) می‌تواند همان پارتیشن را بازیابی کند؟"),
  bulletFa("خط پایه برای فاز ۳ = ۰٫۹۷ (logreg level) — نه ۰٫۹۲ (dummy floor)"),
  bulletFa("نتیجه‌ی ۰٫۶۵ تا ۰٫۹۷ macro-F1 از CNN روی raw pose یک نتیجه‌ی منفی قابل‌انتشار است طبق Constraint 4"),
];

const PHASE2_FIGURES = [
  h2Fa("۲.۵  تصاویر تشخیصی فاز ۲"),
  pFa("پنج نمودار در figures/phd_ml/phase2/ تولید شدند. در ادامه هر کدام را با توضیح می‌بینید:"),

  h3Fa("۲.۵.۱  مقایسه‌ی متریک‌های مدل‌ها"),
  pFa("Macro-F1، F1-minority، ROC-AUC، PR-AUC در یک نمودار میله‌ای با میله‌های خطای ± std. واضح است که dummy_majority کف است (Macro-F1 ≈ ۰٫۴۸) و پنج مدل دیگر همگی به نزدیک ۱ می‌رسند — همان tautology که اشاره شد."),
  ...figure(FIG_P2, "metric_comparison.png", "مقایسه‌ی متریک‌های ۶ مدل با میله‌های خطا", { width: 540, height: 337 }),

  h3Fa("۲.۵.۲  ماتریس‌های درهم‌ریختگی"),
  pFa("شش ماتریس کنار هم. سطر = برچسب واقعی، ستون = پیش‌بینی. dummy همه را advanced پیش‌بینی می‌کند (FN=۲۰). logreg ۲۰ از ۲۰ مبتدی را گرفت (FN=۰، FP=۲). توجه کنید رفتار RF محافظه‌کارتر است."),
  ...figure(FIG_P2, "confusion_matrices.png", "ماتریس درهم‌ریختگی برای شش مدل", { width: 540, height: 320 }),

  h3Fa("۲.۵.۳  منحنی‌های ROC"),
  pFa("منحنی‌های ROC تقریباً همگی به گوشه‌ی بالا-چپ چسبیده‌اند (AUC ≈ ۱٫۰)، که با tautology هم‌خوانی دارد. منحنی dummy روی خط قطر (AUC = ۰٫۵) است."),
  ...figure(FIG_P2, "roc_curves.png", "منحنی‌های ROC شش مدل، pooled روی foldها", { width: 460, height: 390 }),

  h3Fa("۲.۵.۴  منحنی‌های Precision-Recall"),
  pFa("PR در عدم‌توازن از ROC اطلاعاتی‌تر است. کف PR-AUC = نرخ پایه (۰٫۰۸ برای کلاس مبتدی)، که dummy روی همان است. مدل‌های دیگر همگی نزدیک ۱٫۰ هستند."),
  ...figure(FIG_P2, "pr_curves.png", "منحنی‌های Precision-Recall شش مدل", { width: 460, height: 390 }),

  h3Fa("۲.۵.۵  اهمیت ویژگی‌ها"),
  pFa("Native (impurity) و Permutation برای پنج مدل غیر-dummy. فیچر post_body_lean_std در همه‌ی مدل‌ها غالب است. این هم‌سو با یافته‌ی فاز ۱ که Body Lean قوی‌ترین تمایزدهنده بود."),
  ...figure(FIG_P2, "feature_importance.png", "اهمیت ویژگی‌ها (Native + Permutation) برای پنج مدل", { width: 560, height: 504 }),
];

// ===== CHAPTER 3: PHASE 3 ==================================================

const PHASE3 = [
  h1Fa("فصل ۳ — فاز سوم: شبکه عصبی 1D-CNN روی سری زمانی پوز"),
  h2Fa("۳.۱  فاز ۳ چیست؟"),
  pFa("فاز ۳ یک شبکه‌ی عصبی کانولوشن یک‌بعدی (1D-CNN) را روی **سری زمانی نقاط بدن** آموزش می‌دهد. ورودی هر نمونه یک ماتریس T فریم × ۹۹ کانال است (۳۳ نقطه‌ی BlazePose × ۳ مختصات xyz)، یعنی به‌جای ۱۵ عدد خلاصه‌شده، کل توالی حرکت ورزشکار را به مدل می‌دهیم."),
  pFa("هدف: آیا یک شبکه‌ی عصبی که از داده‌ی متفاوت (raw motion) تغذیه می‌شود می‌تواند همان برچسب‌های فاز ۱ را پیش‌بینی کند؟ این آزمون مستقیماً tautology فاز ۲ را دور می‌زند."),

  h2Fa("۳.۲  چرا 1D-CNN و نه CNN دوبعدی؟"),
  pFa("CNN دوبعدی روی فریم خام ویدیو سه ایراد بزرگ دارد:"),
  bulletFa("دوباره‌کاری: همان کاری را می‌کند که MediaPipe قبلاً انجام داده (استخراج نقاط بدن)"),
  bulletFa("هزینه‌ی محاسباتی بسیار بالا (هزاران فریم × میلیون‌ها پیکسل)"),
  bulletFa("با ۲۴۶ نمونه قطعاً overfit می‌شود (CNN معمولاً هزاران نمونه می‌خواهد)"),
  pFa("در عوض 1D-CNN روی سری زمانی نقاط، یک شبکه‌ی سبک (~۶۰ هزار پارامتر) است که با augmentation روی ۲۴۶ نمونه قابل آموزش است."),

  h2Fa("۳.۳  Scaffold اجرا شد — یافته‌های کلیدی"),
  pFa("کد scaffold روی شاخه‌ی phd-ml/phase3-cnn کامیت شد (commit 1a06001). Smoke test روی بخش‌های غیر-torch این یافته‌ها را در پی داشت:"),
  bulletFa("۱۱۶ فایل پوز کشف شد (۱۱۴ single-athlete + 2 dual-lane)"),
  bulletFa("پس از intersect با CSV برچسب‌خورده: ۲۰۱ از ۲۴۶ ردیف باقی می‌ماند"),
  bulletFa("پوشش advanced: ۱۸۸ از ۲۲۶ (۸۳٪)"),
  bulletFa("پوشش beginner: ۱۳ از ۲۰ (۶۵٪) — این تنگنای واقعی است"),
  bulletFa("۷ نمونه‌ی مبتدی از دست رفته: ۱ از Chamonix race013 + ۶ از Zilina"),

  h2Fa("۳.۴  چالش حیاتی — فقط ۱۳ نمونه‌ی مبتدی"),
  calloutFa("تنگنا", "با CV_FOLDS=۵ و ۱۳ نمونه‌ی positive، هر fold فقط ۲٫۶ نمونه‌ی مبتدی دارد. این برای آموزش یک شبکه‌ی عصبی بسیار کم است."),
  pFa("دو راه‌حل پیش‌نهادی در PHASE3_RATIONALE.md:"),
  bulletFa("راه‌حل ۱: CV_FOLDS = ۳ → هر fold ~۴ نمونه‌ی مبتدی (هنوز کم، اما کارا)"),
  bulletFa("راه‌حل ۲: LOOCV (Leave-One-Out) روی کلاس مبتدی → ۱۳ بار اجرا، هر بار یک مبتدی برای آزمون"),
  pFa("توصیه: راه‌حل ۲ به دلیل پایداری آماری بهتر، اما هزینه‌ی محاسباتی بیشتر دارد. تصمیم نهایی باید قبل از اجرا گرفته شود."),

  h2Fa("۳.۵  Augmentation — چطور با ۱۳ نمونه‌ی مبتدی CNN آموزش دهیم؟"),
  pFa("سه تکنیک augmentation روی سری زمانی پوز در augmentation.py پیاده شده:"),
  bulletFa("نویز گاوسی روی نقاط (شبیه‌سازی خطای BlazePose)"),
  bulletFa("Time-warping — کش‌دادن یا فشرده‌کردن خطی محور زمان"),
  bulletFa("Mirror — قرینه کردن چپ-راست (۱۶ جفت نقطه‌ی anatomical طبق BlazePose)"),
  pFa("هر نمونه‌ی مبتدی می‌تواند به ۵-۱۰ نسخه گسترش یابد، که عملاً اندازه‌ی dataset را برای CNN افزایش می‌دهد. توجه: augmentation فقط روی training fold اعمال می‌شود، هرگز روی validation."),

  h2Fa("۳.۶  معماری 1D-CNN"),
  pFa("یک شبکه‌ی سبک با ساختار زیر (در models.py):"),
  bulletFa("ورودی: (T=۲۰۰، C=۹۹) — سری زمانی resample شده به طول ثابت"),
  bulletFa("۲-۳ لایه‌ی Conv1D + BatchNorm + ReLU + Dropout"),
  bulletFa("Global Average Pooling روی محور زمان"),
  bulletFa("یک لایه‌ی Dense + Sigmoid برای کلاس باینری"),
  bulletFa("حدود ۶۰ هزار پارامتر — کوچک به‌اندازه‌ای که overfit نشود"),
  pFa("آموزش با AdamW + Cosine LR schedule + Early Stopping + Class-Weighted Cross-Entropy. در سند روش‌شناسی به ST-GCN (Spatial-Temporal Graph Convolutional Network) به‌عنوان معماری ایده‌آل آینده اشاره شده — با داده‌ی بیشتر، ST-GCN روی این مسئله state-of-the-art است."),

  h2Fa("۳.۷  بازه‌های نتیجه‌ی فاز ۳"),
  spacer(),
  tableFa(
    [
      ["Macro-F1", "تفسیر"],
      ["≥ ۰٫۹۷", "CNN با سقف فاز ۲ برابر — فیچرها و representation برابرند"],
      ["۰٫۸۰ – ۰٫۹۷", "رقابتی — ST-GCN قدم بعدی"],
      ["۰٫۶۵ – ۰٫۸۰", "نتیجه‌ی منفی قابل‌انتشار — فیچرهای مهندسی‌شده اطلاعاتی دارند که CNN از raw pose نمی‌گیرد"],
      ["۰٫۵۰ – ۰٫۶۵", "pseudo-label با raw-pose ناهمراستا — خود برچسب‌ها زیر سؤال می‌روند"],
      ["< ۰٫۵۰", "شکست روش — گزارش نشود"],
    ],
    [1500, 7860],
  ),

  h2Fa("۳.۸  تصمیم‌های باز قبل از اجرای فاز ۳"),
  pFa("دو تصمیم باید قطعی شود:"),
  bulletFa("استراتژی CV — 3-fold یا LOOCV روی minority؟ پیشنهاد: LOOCV"),
  bulletFa("Subject-aware split — race_id athlete identity ندارد؛ نیاز به join با data/race_segments/*_results.json. در حال حاضر placeholder در loader.py:_athlete_from_race_id است"),
  pFa("پس از تأیید این دو تصمیم، scaffold به یک pipeline قابل اجرا تبدیل می‌شود و دانشجو می‌تواند آن را اجرا کند."),
];

// ===== CHAPTER 4: PHASE 4 ==================================================

const PHASE4 = [
  h1Fa("فصل ۴ — فاز چهارم: گزارش مقایسه‌ای علمی"),
  h2Fa("۴.۱  فاز ۴ چیست؟"),
  pFa("فاز ۴ نتایج فاز ۲ و فاز ۳ را روی نمونه‌های یکسان (به‌کمک sample_index در cv_predictions.csv) مقایسه می‌کند و متن آکادمیک نهایی برای فصل پایان‌نامه آماده می‌کند."),

  h2Fa("۴.۲  محصولات فاز ۴"),
  bulletFa("نمودار ROC ترکیبی برای همه‌ی مدل‌های فاز ۲ و فاز ۳"),
  bulletFa("نمودار Precision-Recall ترکیبی"),
  bulletFa("جدول مقایسه‌ی Macro-F1 و F1-minority با میانگین ± انحراف معیار"),
  bulletFa("آزمون آماری McNemar برای بررسی معناداری اختلاف CNN و بهترین baseline"),
  bulletFa("آزمون حساسیت برچسب: ۱۰٪ از برچسب‌های فاز ۱ را عوض می‌کنیم و دوباره آموزش می‌دهیم تا robustness بسنجیم"),
  bulletFa("متن آکادمیک نهایی با اسکیل research-paper-writing (aiScore=۸۸، نصب شده در پروژه)"),

  h2Fa("۴.۳  سناریوهای ممکن و نحوه‌ی گزارش هر کدام"),
  spacer(),
  tableFa(
    [
      ["سناریو", "نحوه‌ی گزارش در پایان‌نامه"],
      ["CNN از baseline قابل‌توجه بهتر می‌شود", "ادعای کشف الگوی زمانی که فیچرهای مهندسی‌شده نمی‌بینند؛ ST-GCN را به‌عنوان ادامه پیشنهاد می‌کنیم"],
      ["CNN با baseline برابر می‌شود", "نشان می‌دهد فیچرهای مهندسی‌شده‌ی فعلی تمام اطلاعات سری زمانی را capture می‌کنند — یافته‌ی آموزنده"],
      ["CNN از baseline بدتر می‌شود", "صادقانه گزارش می‌کنیم: با ۱۳ نمونه‌ی مبتدی، deep learning به ساختار feature-engineered نمی‌رسد — یافته‌ی روشن برای ادبیات"],
    ],
    [3500, 5860],
  ),
  pFa("هر سه سناریو پایان‌نامه را تقویت می‌کنند. صداقت علمی > نتیجه‌ی خاص."),

  h2Fa("۴.۴  چرا فاز ۴ مهم است حتی اگر CNN ضعیف‌تر شد؟"),
  pFa("اگر CNN از baseline بدتر شد، این به معنای آن نیست که پروژه شکست خورده. به معنای آن است که:"),
  bulletFa("ما یک baseline آماری قوی ساختیم که در ادبیات قابل گزارش است"),
  bulletFa("نشان دادیم با n=۲۴۶ و فقط ۲۰ minority، deep learning روی time-series هنوز به feature engineering ضعیف‌تر است"),
  bulletFa("روش‌شناسی تولید pseudo-label با weak supervision را برای جوامع مشابه (n محدود + ground truth ممنوع) معرفی کردیم"),
  bulletFa("راه آینده (ST-GCN + n بزرگ‌تر) را برای پژوهش‌گران بعدی روشن کردیم"),
];

// ===== CHAPTER 5: RECOMMENDATIONS ==========================================

const RECOMMEND = [
  h1Fa("فصل ۵ — توصیه‌های مشخص برای دانشجو و استاد"),

  h2Fa("۵.۱  برای دانشجو"),
  bulletFa("اسناد PHASE1_METHODOLOGY.docx و PHASE2_METHODOLOGY.docx جزئیات فنی کامل را دارند — قبل از جلسه‌ی استاد یک بار بخوانید"),
  bulletFa("اگر استاد پرسید «چرا دقت همه‌جا ۱۰۰٪ است؟»، پاسخ: tautology — برچسب‌ها از همان فیچرها ساخته شده‌اند، آزمون واقعی فاز ۳ است"),
  bulletFa("سعی نکنید CNN را با تنظیم hyperparameter به ۰٫۹۸ برسانید؛ هر بازه‌ای صادقانه گزارش شود — این جزء روش‌شناسی است"),
  bulletFa("اگر فاز ۳ به نتیجه‌ی منفی رسید، آن را به‌عنوان «شواهد در مورد کفایت feature-engineering» معرفی کنید، نه شکست CNN"),
  bulletFa("در آخرین فصل پایان‌نامه، حتماً به ST-GCN و نیاز به n بزرگ‌تر به‌عنوان کار آینده اشاره کنید"),

  h2Fa("۵.۲  برای استاد"),
  bulletFa("سه سند روش‌شناسی فنی موجود است: PHASE1_METHODOLOGY.docx (متن آکادمیک با ۹ بخش)، PHASE2_METHODOLOGY.docx (با emperical results)، و PHASE3_RATIONALE.md (Markdown)"),
  bulletFa("جدول‌های نتایج، با میانگین ± std و معیارهای imbalance-aware، در فرمت قابل کپی به پایان‌نامه هستند"),
  bulletFa("هر فاز روی شاخه‌ی Git جداگانه است؛ شاخه‌ی main همیشه پایدار و قابل بازگشت است"),
  bulletFa("Tautology caveat فاز ۲ یک نکته‌ی اصیل روش‌شناختی است که در ادبیات مشابه کمتر دیده می‌شود — می‌تواند یک سهم کوچک علمی پایان‌نامه باشد"),
  bulletFa("سند PROJECT_GUIDE_FA.docx (همین فایل) برای دفاع از پایان‌نامه به‌عنوان مرور سریع مفید است"),

  h2Fa("۵.۳  گام بعدی فوری"),
  pFa("قبل از اجرای فاز ۳، این دو تصمیم باید گرفته شوند:"),
  bulletFa("CV strategy: 3-fold یا LOOCV روی کلاس مبتدی؟"),
  bulletFa("subject-aware split: آیا اکنون باید placeholder در _athlete_from_race_id را با join واقعی جایگزین کنیم، یا فعلاً با competition-aware split جلو برویم؟"),
  pFa("پس از تأیید این دو، scaffold به pipeline قابل اجرا تبدیل می‌شود و دانشجو می‌تواند آن را در حدود ۲-۳ ساعت روی GPU اجرا کند."),
];

// ===== GLOSSARY ============================================================

const GLOSSARY = [
  h1Fa("ضمیمه — واژه‌نامه‌ی فنی"),
  tableFa(
    [
      ["اصطلاح", "توضیح فارسی"],
      ["Stratified K-Fold", "تقسیم داده به K بخش با حفظ نسبت کلاس‌ها در هر بخش"],
      ["Class Imbalance", "وقتی یک کلاس به‌طور قابل‌توجهی بیش‌تر از دیگری در داده است"],
      ["SMOTE", "نمونه‌برداری مصنوعی از کلاس کمیاب با درون‌یابی بین نمونه‌های موجود"],
      ["Macro-F1", "میانگین F1 دو کلاس — مستقل از اندازه‌ی کلاس‌ها"],
      ["ROC-AUC", "سطح زیر منحنی ROC؛ کیفیت رتبه‌بندی صرف‌نظر از آستانه"],
      ["PR-AUC", "سطح زیر منحنی Precision-Recall؛ در عدم‌توازن از ROC اطلاعاتی‌تر است"],
      ["Silhouette", "معیار کیفیت خوشه‌بندی — بالاتر بهتر (max=۱)"],
      ["ARI", "Adjusted Rand Index — توافق دو خوشه‌بندی (بالاتر بهتر)"],
      ["BIC", "Bayesian Information Criterion — معیار انتخاب مدل، کمتر بهتر"],
      ["Tautology", "وقتی نتیجه به‌خاطر طراحی همان ورودی-خروجی، نه قدرت مدل، بالا است"],
      ["Weak Supervision", "آموزش با برچسب‌هایی که توسط heuristic ساخته شده‌اند نه انسان"],
      ["Bootstrap-ARI", "ARI میانگین روی sub-sampleها — معیار پایداری ساختار خوشه‌بندی"],
      ["1D-CNN", "شبکه‌ی کانولوشن یک‌بعدی — برای سری زمانی"],
      ["ST-GCN", "Spatial-Temporal Graph Convolutional Network — معماری مرجع برای حرکت skeleton-based"],
      ["LOOCV", "Leave-One-Out Cross-Validation — هر نمونه یک بار test می‌شود"],
      ["Augmentation", "گسترش داده با تبدیل‌های مصنوعی (نویز، Time-Warp، Mirror)"],
      ["BlazePose", "مدل MediaPipe برای استخراج ۳۳ نقطه‌ی بدن"],
    ],
    [2700, 6660],
  ),
];

// ---------- assembly ------------------------------------------------------

const doc = new Document({
  creator: "airano",
  title: "راهنمای جامع پروژه — تحلیل عملکرد سنگ‌نوردی سرعت",
  description: "Comprehensive Persian guide for student and advisor covering all four phases",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT, color: "1F4E79" },
        paragraph: { spacing: { before: 320, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "2E74B5" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT, color: "404040" },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
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
        bidirectional: true, alignment: AlignmentType.RIGHT,
        children: [new TextRun({
          text: "راهنمای جامع پروژه — تحلیل عملکرد سنگ‌نوردی سرعت",
          font: FONT, size: 18, color: "808080", rtl: true,
        })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "صفحه ", font: FONT, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" }),
          new TextRun({ text: " از ", font: FONT, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18, color: "808080" }),
        ],
      })] }),
    },
    children: [
      ...COVER,
      ...EXEC,
      ...NAV,
      pagebreak(),
      h1Fa("فهرست مطالب"),
      new TableOfContents("فهرست مطالب", { hyperlink: true, headingStyleRange: "1-3" }),
      pagebreak(),
      ...PHASE1,
      ...PHASE1_FIGURES,
      pagebreak(),
      ...PHASE2,
      ...PHASE2_FIGURES,
      pagebreak(),
      ...PHASE3,
      pagebreak(),
      ...PHASE4,
      pagebreak(),
      ...RECOMMEND,
      pagebreak(),
      ...GLOSSARY,
    ],
  }],
});

const outPath = path.resolve(REPO_ROOT, "PROJECT_GUIDE_FA.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`Wrote ${outPath} (${buf.length} bytes)`);
});

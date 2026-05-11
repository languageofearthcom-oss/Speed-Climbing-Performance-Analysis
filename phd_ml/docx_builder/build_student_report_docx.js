/**
 * Persian-language progress report for the PhD student.
 *
 * A narrative, student-facing document explaining what has been done in
 * Phases 1 & 2, what is coming in Phases 3 & 4, and what each diagnostic
 * figure in figures/phd_ml/phase1/ means.
 *
 * Run:  node build_student_report_docx.js
 * Out:  ../STUDENT_REPORT_FA.docx (at repository root via path resolution)
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
const FIG_PHASE1 = path.join(REPO_ROOT, "figures", "phd_ml", "phase1");

// ---------- helpers ---------------------------------------------------------

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const headerShade = { fill: "1F4E79", type: ShadingType.CLEAR, color: "auto" };

const fa = (t, o = {}) => new TextRun({
  text: t, font: FONT, size: 22, rtl: true, ...o,
});

const pFa = (t, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: 120, line: 360 },
  children: [fa(t, o)],
});

const pEn = (t, o = {}) => new Paragraph({
  alignment: AlignmentType.LEFT,
  spacing: { after: 80 },
  children: [new TextRun({ text: t, font: "Consolas", size: 18, ...o })],
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

const code = (lines) => lines.map((line) => new Paragraph({
  spacing: { before: 0, after: 0, line: 240 },
  shading: { fill: "F2F2F2", type: ShadingType.CLEAR, color: "auto" },
  children: [new TextRun({ text: line || " ", font: "Consolas", size: 18 })],
}));

const spacer = () => new Paragraph({ children: [new TextRun(" ")] });
const pagebreak = () => new Paragraph({ children: [new PageBreak()] });

const cellFa = (t, opts = {}) => {
  const { width = 3000, header = false } = opts;
  const props = header
    ? { bold: true, color: "FFFFFF", size: 22 }
    : { size: 21 };
  return new TableCell({
    borders: cellBorders,
    width: { size: width, type: WidthType.DXA },
    shading: header ? headerShade : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      bidirectional: true, alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: t, font: FONT, rtl: true, ...props })],
    })],
  });
};

const tableFa = (rows, columnWidths) => {
  const total = columnWidths.reduce((a, b) => a + b, 0);
  // RTL table: visual right-most column is the first cell
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

const figure = (filename, captionFa, opts = {}) => {
  const { width = 540, height = 350 } = opts;
  const filePath = path.join(FIG_PHASE1, filename);
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
        text: `شکل: ${captionFa}`, font: FONT, rtl: true, size: 20,
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
      text: "گزارش پیشرفت پروژه پایان‌نامه",
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
      text: "گزارش وضعیت فاز یکم و دوم،  و نقشه‌راه فاز سوم و چهارم",
      font: FONT, size: 24, rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    spacing: { after: 720 },
    children: [new TextRun({
      text: "(گزارش غیرفنی برای دانشجوی پایان‌نامه)",
      font: FONT, size: 22, italics: true, color: "595959", rtl: true,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, bidirectional: true,
    children: [new TextRun({
      text: "نگارنده: airano  |  تاریخ: ۲۰۲۶/۰۴/۳۰  |  نسخه: ۱.۰",
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

// ---- Section 1: Introduction & Framing -----------------------------------

const INTRO = [
  h1Fa("۱. مقدمه و چارچوب کلی"),
  pFa("این گزارش برای دوست شما (دانشجوی دکترا) نوشته شده تا بداند تا اینجای کار چه گام‌هایی برداشته‌ایم، چرا آن‌ها را برداشته‌ایم، و در ادامه قرار است چه کنیم. تلاش شده زبان روان و قابل‌فهم باشد و نقشه‌راه کلی پروژه واضح بماند."),
  pFa("هدف اصلی پروژه: گرفتن یک ویدیوی مسابقه‌ی سنگ‌نوردی سرعت و خروجی دادن یک تحلیل تکنیکی که برای ورزشکار و مربی کاربردی باشد. سیستم پایه (که از قبل در پروژه ساخته شده) با MediaPipe BlazePose نقاط بدن (۳۳ نقطه) را روی فریم‌های ویدیو پیدا می‌کند و سپس ۲۲ ویژگی سینماتیک (مثل میانگین زاویه زانو، انحراف وضعیت بدن، هم‌زمانی دست و پا) از این نقاط استخراج می‌کند و در یک سامانه‌ی منطق فازی برای تولید بازخورد مربیگری استفاده می‌کند."),
  pFa("استاد محترم درخواست افزودن یک مدل CNN را داده‌اند. ما به‌جای CNN دوبعدی روی فریم خام (که با ۲۴۶ نمونه قطعاً overfit می‌شد و کاری را که MediaPipe انجام می‌دهد دوباره‌کاری می‌کرد) مسیر زیر را برگزیده‌ایم:"),
  spacer(),
  bulletFa("فاز یکم: تولید برچسب خودکار با خوشه‌بندی بدون نظارت (چون لیبل دستی نداریم)"),
  bulletFa("فاز دوم: مدل‌های پایه سنتی (Random Forest و XGBoost) به‌عنوان معیار مقایسه"),
  bulletFa("فاز سوم: شبکه عصبی یک‌بعدی (1D-CNN) روی سری زمانی نقاط بدن"),
  bulletFa("فاز چهارم: گزارش مقایسه‌ای علمی فاز ۲ و فاز ۳"),
  pFa("اگر در نهایت CNN از مدل‌های پایه بهتر نشد (که با ۲۴۶ نمونه احتمالش وجود دارد)، این هم یک نتیجه‌ی علمی قابل‌دفاع است و پایان‌نامه آن را به‌صورت صادقانه گزارش می‌کند."),
];

// ---- Section 2: Project map ----------------------------------------------

const PROJECT_MAP = [
  h1Fa("۲. نقشه‌راه چهار فاز"),
  pFa("جدول زیر یک نگاه کلی از وضعیت چهار فاز پروژه می‌دهد:"),
  spacer(),
  tableFa(
    [
      ["فاز", "هدف", "وضعیت", "شاخه گیت"],
      ["۱", "تولید برچسب خودکار با خوشه‌بندی", "اجرا شد، در انتظار تأیید استاد", "phd-ml/phase1-auto-labeling"],
      ["۲", "مدل پایه سنتی با مدیریت عدم‌توازن", "کد آماده، در انتظار اجرای دانشجو", "phd-ml/phase2-baseline"],
      ["۳", "شبکه 1D-CNN روی سری زمانی پوز", "در انتظار شروع", "phd-ml/phase3-cnn"],
      ["۴", "گزارش مقایسه‌ای علمی نهایی", "در انتظار شروع", "phd-ml/phase4-report"],
    ],
    [600, 2900, 2700, 3060],
  ),
];

// ---- Section 3: Phase 1 — what we did ------------------------------------

const PHASE1 = [
  h1Fa("۳. فاز یکم — تولید برچسب خودکار"),
  h2Fa("۳.۱  چرا یادگیری بدون نظارت؟"),
  pFa("ما ۲۴۶ نمونه‌ی باکیفیت داریم که هیچ‌کدام برچسب «مهارت» ندارند. لیبل‌گذاری دستی هم در محدودیت‌های پروژه ممنوع است. در ادبیات بیومکانیک ورزشی، وقتی نمونه‌ها به‌طور طبیعی در فضای ویژگی‌های سینماتیک به خوشه‌های جدا تقسیم می‌شوند، این را شاهدی می‌گیرند بر وجود سبک‌های حرکتی متمایز. پس ما با خوشه‌بندی، خوشه‌ها را پیدا می‌کنیم و سپس بر اساس یک معیار بیومکانیکی مرتبه (مهارت کم/متوسط/زیاد) به آن‌ها می‌زنیم."),

  h2Fa("۳.۲  مراحل اجرایی فاز یکم"),
  bulletFa("بارگذاری CSV ویژگی‌ها و فیلتر کیفیت ≥ ۰٫۸ → ۲۴۶ نمونه باقی می‌ماند (دقیقاً مطابق MASTER_CONTEXT)"),
  bulletFa("استانداردسازی z-score روی ۱۵ ویژگی مستقل از حرکت دوربین"),
  bulletFa("اجرای چهار الگوریتم خوشه‌بندی به‌موازات یکدیگر: K-Means، Gaussian Mixture، DBSCAN، Agglomerative Ward"),
  bulletFa("اعتبارسنجی با سه شاخص داخلی (Silhouette، Davies-Bouldin، Calinski-Harabasz)"),
  bulletFa("آزمون پایداری Bootstrap با ۱۰۰ تکرار روی K-Means"),
  bulletFa("محاسبه‌ی توافق میان روش‌ها با شاخص ARI"),
  bulletFa("ساخت Skill Proxy Score با شش معیار بیومکانیکی برای رتبه‌بندی خوشه‌ها"),
  bulletFa("نگاشت خوشه‌ها به برچسب ترتیبی: مبتدی / پیشرفته"),

  h2Fa("۳.۳  نتایج عددی فاز یکم"),
  pFa("پس از اجرا، K-Means با k = ۲ (دو کلاس) انتخاب شد و نتایج زیر گزارش شد:"),
  spacer(),
  tableFa(
    [
      ["معیار", "مقدار", "تفسیر"],
      ["Silhouette", "۰٫۴۲۳", "متوسط؛ زیر هدف ۰٫۵ ولی برای داده‌ی ۱۵-بعدی سینماتیک قابل‌قبول"],
      ["Bootstrap-ARI", "۰٫۶۳۴ ± ۰٫۲۵۲", "پایداری متوسط — انحراف معیار بالا نشان از دامنه‌ی ناپایداری دارد"],
      ["K-Means × Hierarchical (Ward)", "ARI = ۰٫۸۵۱", "توافق قوی — ساختار geometric واقعی است"],
      ["K-Means × GMM", "ARI = ۰٫۳۲۷", "ناهماهنگی — GMM با k=۵ ساختار دیگری دیده"],
      ["DBSCAN", "۳۴٫۵٪ نویز", "ساختار density ضعیف است؛ کلاس‌ها بر اساس فاصله‌ی مرکز بهتر تعریف می‌شوند"],
      ["توزیع کلاس", "۲۲۶ پیشرفته / ۲۰ مبتدی", "عدم‌توازن شدید (۹۲٪ / ۸٪) — چالش مهم برای فاز ۲"],
      ["جدایی Skill Score", "Cohen's d = -۰٫۹۲", "اثر بزرگ آماری — برچسب‌ها از نظر معیار بیومکانیکی واقعاً متمایزند"],
    ],
    [2400, 2400, 4460],
  ),
  pFa("نتیجه‌گیری: ساختار باینری (دو کلاس) واقعی است، اما عدم‌توازن کلاس‌ها مشکل اصلی فاز بعد خواهد بود. ضمناً ۲۰ نمونه‌ی مبتدی در نمودار UMAP کاملاً جدا هستند ولی در PCA نه — این نشان می‌دهد ساختار غیرخطی قوی‌تر از ساختار خطی است."),
];

// ---- Section 4: figure walkthrough --------------------------------------

const FIGURES = [
  h1Fa("۴. توضیح تصاویر تشخیصی فاز یکم"),
  pFa("هشت تصویر تشخیصی در پوشه figures/phd_ml/phase1/ ساخته شده‌اند. هر تصویر یک سؤال متفاوت را پاسخ می‌دهد. در ادامه هر کدام را با تصویر و توضیح می‌بینید:"),

  h3Fa("۴.۱  elbow_kmeans.png — انتخاب تعداد خوشه‌ها در K-Means"),
  pFa("این نمودار به سؤال «چند خوشه بسازیم؟» پاسخ می‌دهد. روی محور افقی k (تعداد خوشه)، روی محور عمودی دو معیار: Inertia (مجموع مربعات فاصله — کمتر بهتر) و Silhouette Score (هرچه نزدیک‌تر به ۱، خوشه‌ها متمایزتر). انتخاب k ایده‌آل وقتی است که Inertia شکست (Elbow) ایجاد کند و Silhouette حداکثر شود. در داده‌ی ما k=۲ به‌وضوح بهترین Silhouette را دارد (۰٫۴۲ در k=۲ در برابر ۰٫۲۵ در k=۳)."),
  ...figure("elbow_kmeans.png", "Inertia و Silhouette به ازای k در K-Means", { width: 540, height: 348 }),

  h3Fa("۴.۲  bic_gmm.png — انتخاب تعداد مؤلفه‌ها در Gaussian Mixture"),
  pFa("این نمودار همان کار را برای الگوریتم GMM انجام می‌دهد، اما با دو معیار اطلاعاتی: BIC (Bayesian Information Criterion) و AIC. هر دو پایین‌تر بهتر است. GMM ما k=۵ را انتخاب کرد، اما Silhouette آن فقط ۰٫۱۴ شد — یعنی GMM با ۵ مؤلفه احتمالاً over-fit کرده و ساختار k=۲ که K-Means دیده، حقیقی‌تر است."),
  ...figure("bic_gmm.png", "BIC و AIC به ازای تعداد مؤلفه‌های GMM", { width: 540, height: 348 }),

  h3Fa("۴.۳  dendrogram_ward.png — درخت سلسله‌مراتبی"),
  pFa("این درخت (Dendrogram) نشان می‌دهد اگر نمونه‌ها را از پایین به بالا یکی‌یکی در هم بپیچانیم، خوشه‌ها چطور شکل می‌گیرند. هر شاخه یک خوشه است؛ ارتفاع نقاط ادغام، فاصله بین خوشه‌ها را نشان می‌دهد. این تصویر برای پایان‌نامه‌ی شما عالی است چون به استاد نشان می‌دهد ساختار طبیعی داده چند خوشه پیشنهاد می‌دهد. در داده‌ی ما، یک شکست واضح در ارتفاع بالا وجود دارد که دو خوشه‌ی اصلی را جدا می‌کند — همان نتیجه‌ی K-Means."),
  ...figure("dendrogram_ward.png", "درخت خوشه‌بندی سلسله‌مراتبی Ward", { width: 540, height: 220 }),

  h3Fa("۴.۴  embedding_pca.png — تجسم با PCA"),
  pFa("PCA دو بُعد اول واریانس‌محور را نشان می‌دهد. هر نقطه یک نمونه (یک ورزشکار در یک مسابقه) و رنگ آن خوشه‌ای است که K-Means به آن داده. اگر دو رنگ در PCA واضح جدا نباشند، یعنی ساختار خطی‌محور ضعیف است. در داده‌ی ما PCA جدایی متوسطی نشان می‌دهد."),
  ...figure("embedding_pca.png", "تجسم PCA دوبعدی، رنگ‌بندی بر اساس خوشه K-Means", { width: 480, height: 406 }),

  h3Fa("۴.۵  embedding_tsne.png — تجسم با t-SNE"),
  pFa("t-SNE یک روش غیرخطی برای تجسم است که فاصله‌های محلی را حفظ می‌کند. اگر نمونه‌ها در فضای اصلی به‌هم نزدیک بودند، در تصویر t-SNE هم نزدیک می‌مانند. این تصویر برای دیدن ساختارهای پیچیده‌تر از PCA مفیدتر است."),
  ...figure("embedding_tsne.png", "تجسم t-SNE دوبعدی، رنگ‌بندی بر اساس خوشه K-Means", { width: 480, height: 406 }),

  h3Fa("۴.۶  embedding_umap.png — تجسم با UMAP"),
  pFa("UMAP روشی نو‌تر و معمولاً بهتر از t-SNE است که هم ساختارهای محلی و هم سراسری را حفظ می‌کند. در داده‌ی ما، UMAP خوشه‌ی مبتدی (۲۰ نمونه) را به‌وضوح کامل از خوشه‌ی پیشرفته جدا می‌کند — این یکی از قوی‌ترین شواهد ماست برای وجود ساختار باینری واقعی."),
  ...figure("embedding_umap.png", "تجسم UMAP دوبعدی — جدایی واضح خوشه‌ی مبتدی", { width: 480, height: 406 }),

  h3Fa("۴.۷  skill_score_distribution.png — توزیع امتیاز مهارت"),
  pFa("این نمودار جعبه‌ای، توزیع Skill Proxy Score درون هر خوشه را نشان می‌دهد. اگر نگاشت خوشه به برچسب ترتیبی ما درست کار کرده باشد، خوشه‌ی «پیشرفته» باید به‌طور سیستماتیک Skill بالاتری داشته باشد. در داده‌ی ما این رابطه برقرار است: میانگین خوشه ۱ (پیشرفته) برابر ۰٫۰۳ و خوشه ۰ (مبتدی) برابر -۰٫۳۷ است (Cohen's d = ۰٫۹۲ یعنی اثر بزرگ)."),
  ...figure("skill_score_distribution.png", "توزیع Skill Proxy Score درون هر خوشه", { width: 540, height: 348 }),

  h3Fa("۴.۸  method_agreement.png — توافق میان روش‌ها"),
  pFa("این نمودار میله‌ای، شاخص ARI بین جفت‌های روش‌های خوشه‌بندی را نشان می‌دهد. اگر K-Means و Hierarchical به نتیجه‌ی یکسانی برسند، ARI آن‌ها نزدیک به ۱ خواهد بود — همان چیزی که در داده‌ی ما اتفاق افتاده (ARI=۰٫۸۵). توافق GMM با دیگران فقط ۰٫۳۳ است، که قبلاً توضیح دادیم چرا (GMM با k=۵، ساختاری متفاوت دیده)."),
  ...figure("method_agreement.png", "توافق میان روش‌های خوشه‌بندی (پایداری ساختار)", { width: 540, height: 314 }),
];

// ---- Section 5: Phase 2 — what we did -----------------------------------

const PHASE2 = [
  h1Fa("۵. فاز دوم — مدل‌های پایه با مدیریت عدم‌توازن"),
  h2Fa("۵.۱  چالش اصلی این فاز"),
  pFa("توزیع کلاس‌ها در فاز ۱ به ۲۲۶ به ۲۰ شد (۹۲٪ به ۸٪). یعنی اگر یک مدل بی‌فکر برای همه نمونه‌ها بگوید «پیشرفته»، به دقت ۹۱٫۹٪ می‌رسد — اما هیچ نمونه‌ی مبتدی را تشخیص نداده. این یعنی **دقت خام (accuracy) برای ما بی‌معناست** و باید با معیارهای دیگری کار کنیم."),

  h2Fa("۵.۲  شش مدل که با هم مقایسه می‌شوند"),
  spacer(),
  tableFa(
    [
      ["نام مدل", "نوع", "استراتژی عدم‌توازن", "نقش"],
      ["dummy_majority", "ساده", "هیچ", "کف منطقی — پیش‌بینی کلاس اکثریت برای همه"],
      ["logreg_balanced", "خطی", "وزن کلاس متعادل", "خط پایه‌ی خطی"],
      ["rf_balanced", "Random Forest", "وزن کلاس متعادل", "استراتژی A روی RF"],
      ["xgb_scale_pos_weight", "XGBoost", "scale_pos_weight=۱۱٫۳", "استراتژی A روی XGBoost"],
      ["rf_smote", "Random Forest", "SMOTE روی fold آموزش", "استراتژی B روی RF"],
      ["xgb_smote", "XGBoost", "SMOTE روی fold آموزش", "استراتژی B روی XGBoost"],
    ],
    [2300, 1700, 2700, 2660],
  ),

  h2Fa("۵.۳  دو استراتژی برخورد با عدم‌توازن"),
  pFa("استراتژی A — یادگیری حساس به هزینه: داده دست‌نخورده می‌ماند، اما تابع ضرر مدل طوری بازوزن می‌شود که خطای کلاس مبتدی بسیار گران‌تر از خطای کلاس پیشرفته باشد. در RF با class_weight='balanced'، در XGBoost با scale_pos_weight."),
  pFa("استراتژی B — نمونه‌برداری مصنوعی (SMOTE): از نمونه‌های مبتدی موجود، نمونه‌های جدید مصنوعی ساخته می‌شود تا تعداد مبتدی به سطح پیشرفته برسد. **نکته‌ی حیاتی**: SMOTE فقط روی fold آموزش اعمال می‌شود، نه روی fold آزمون — وگرنه نتیجه‌ی نادرست (data leakage) به‌دست می‌آید."),

  h2Fa("۵.۴  متریک‌های مناسب (که گزارش می‌کنیم)"),
  bulletFa("Macro-F1: میانگین F1 دو کلاس — به‌جای دقت خام، این معیار اصلی است"),
  bulletFa("F1 کلاس مبتدی: مستقیماً نشان می‌دهد چقدر خوب کلاس کمیاب را تشخیص می‌دهیم"),
  bulletFa("Precision و Recall به‌صورت جداگانه برای هر کلاس"),
  bulletFa("ROC-AUC: کیفیت رتبه‌بندی صرف‌نظر از آستانه"),
  bulletFa("PR-AUC: در عدم‌توازن از ROC-AUC اطلاعاتی‌تر است"),
  bulletFa("ماتریس درهم‌ریختگی: نوع خطا (FP در برابر FN) را نشان می‌دهد"),
  bulletFa("Stratified-5-Fold CV: نتایج با میانگین ± انحراف معیار گزارش می‌شوند"),

  h2Fa("۵.۵  بازه‌های نتیجه — متعهد قبل از اجرا"),
  pFa("برای حفظ صداقت علمی، قبل از اجرای مدل‌ها به این بازه‌بندی متعهد شده‌ایم:"),
  spacer(),
  tableFa(
    [
      ["Macro-F1", "تفسیر برای کمیته"],
      ["≥ ۰٫۸۰", "خط پایه قوی — CNN باید قانع‌کننده برتر باشد"],
      ["۰٫۶۵ تا ۰٫۸۰", "خط پایه معقول — CNN احتمالاً برابر یا بهتر"],
      ["۰٫۵۰ تا ۰٫۶۵", "خط پایه ضعیف — برچسب‌ها نویزدارند، بحث صادقانه در فاز ۴"],
      ["< ۰٫۵۰", "شکست — برچسب‌های Phase 1 از این ۱۵ ویژگی قابل یادگیری نیستند"],
    ],
    [1700, 7660],
  ),
  pFa("به هر بازه‌ای که برسیم، آن را گزارش می‌کنیم بدون آن‌که با تنظیم مجدد hyperparameter از آن فرار کنیم. نتیجه‌ی منفی هم یک نتیجه‌ی علمی است."),

  h2Fa("۵.۶  بررسی کیفیت کد قبل از کامیت"),
  pFa("قبل از پوش کردن کد فاز ۲، با اسکیل code-review بررسی شد و سه مسئله‌ی HIGH و دو مسئله‌ی MEDIUM پیدا و اصلاح شد. مهم‌ترین آن‌ها: اضافه کردن sample_index در خروجی پیش‌بینی‌ها (تا فاز ۴ بتواند مدل CNN و baseline را روی نمونه‌های یکسان مقایسه کند) و decorrelation seed permutation_importance بین foldها."),

  h2Fa("۵.۷  نتایج تجربی فاز ۲ (اجرا: ۲۰۲۶-۰۵-۱۱)"),
  pFa("Pipeline فاز ۲ روی کامیت 4710bb5 با موفقیت اجرا شد. خلاصه نتایج Stratified-5-Fold CV (میانگین ± انحراف معیار) در جدول زیر — همه‌ی پنج مدل غیرتُرویال در بازه قوی (≥ ۰٫۸۰) قرار گرفتند:"),
  spacer(),
  tableFa(
    [
      ["مدل", "F1-macro", "F1 مبتدی", "ROC-AUC", "PR-AUC"],
      ["dummy_majority (کف)", "۰٫۴۷۹ ± ۰٫۰۰۰", "۰٫۰۰۰", "۰٫۵۰۰", "۰٫۰۸۱"],
      ["logreg_balanced ⭐", "۰٫۹۷۸ ± ۰٫۰۴۵", "۰٫۹۶۰ ± ۰٫۰۸۰", "۱٫۰۰۰", "۱٫۰۰۰"],
      ["rf_balanced", "۰٫۹۴۹ ± ۰٫۰۷۰", "۰٫۹۰۵ ± ۰٫۱۳۱", "۱٫۰۰۰", "۰٫۹۹۰"],
      ["xgb_scale_pos_weight", "۰٫۹۷۲ ± ۰٫۰۳۴", "۰٫۹۴۹ ± ۰٫۰۶۳", "۱٫۰۰۰", "۱٫۰۰۰"],
      ["rf_smote", "۰٫۹۶۹ ± ۰٫۰۳۸", "۰٫۹۴۳ ± ۰٫۰۷۰", "۰٫۹۹۹", "۰٫۹۹۰"],
      ["xgb_smote", "۰٫۹۷۲ ± ۰٫۰۳۴", "۰٫۹۴۹ ± ۰٫۰۶۳", "۱٫۰۰۰", "۱٫۰۰۰"],
    ],
    [2400, 1740, 1740, 1740, 1740],
  ),
  spacer(),
  pFa("ماتریس درهم‌ریختگی pooled (مجموع همه foldها، ۲۲۶ پیشرفته + ۲۰ مبتدی):"),
  bulletFa("logreg_balanced: ۲۰ از ۲۰ مبتدی شناسایی شد، ۲ خطای FP — بهترین recall کلاس مبتدی"),
  bulletFa("xgb (هر دو حالت): ۱۹ از ۲۰ شناسایی، ۱ خطای FP"),
  bulletFa("rf_smote: ۱۸ از ۲۰، rf_balanced: ۱۷ از ۲۰ — هیچ FP ندارد"),

  h2Fa("۵.۸  ویژگی‌های برتر (consistent بین permutation و native)"),
  bulletFa("post_body_lean_std — غالب: permutation ۰٫۲۴ (LR)، native ۰٫۲۵ (RF). شیب بدن متغیرترین ویژگی است"),
  bulletFa("post_avg_body_lean — native ۰٫۲۳ (RF). میانگین شیب بدن مرز اصلی بین کلاس‌ها"),
  bulletFa("freq_foot_movement_amplitude — native ≈ ۰٫۰۶ (RF/XGB)"),
  bulletFa("post_max_reach_ratio و post_elbow_angle_std در رتبه‌های بعدی"),
  pFa("این یافته با Cohen's d = -۰٫۹۲ فاز ۱ (که شیب بدن را بزرگ‌ترین تفاوت بین دو کلاس نشان داد) کاملاً همخوان است."),

  h2Fa("۵.۹  هشدار حیاتی — قبل از تفسیر این نتایج بخوانید"),
  pFa("**ROC-AUC = ۱٫۰۰۰ یک سقف tautological است، نه پیروزی واقعی.** برچسب‌های فاز ۱ از K-Means روی همان ۱۵ ویژگی استخراج شدند که اکنون ورودی فاز ۲ هستند. پس فاز ۲ در عمل دارد «X را از X پیش‌بینی می‌کند». هر مدل با ظرفیت کافی روی این ویژگی‌ها به ۱۰۰٪ می‌رسد — این «نمره کامل» نشانه قدرت مدل نیست، نشانه طراحی است."),
  pFa("آزمون واقعی فاز ۳ این است: آیا یک 1D-CNN روی **سری زمانی پوز خام** (که هرگز ویژگی‌های summary را ندیده) می‌تواند همان partition را بازیابی کند؟ اگر CNN به Macro-F1 بین ۰٫۶۵ تا ۰٫۹۷ برسد، این یافته‌ی علمی است — نشانه آن که ویژگی‌های summary همه‌ی سیگنال را گرفته‌اند (نتیجه‌ی منفی قابل انتشار طبق Constraint 4)."),
  pFa("**برای فاز ۳ هدف واقعی** ≥ ۰٫۹۷ macro-F1 است (هم‌تراز logreg)، نه ۰٫۹۲ کف. همچنین subject/competition holdout (نه random CV ساده) لازم است تا overfitting روی برچسب‌های وابسته‌به‌ویژگی کنترل شود."),
];

// ---- Section 6: Phase 3 — what's next -----------------------------------

const PHASE3 = [
  h1Fa("۶. فاز سوم — شبکه عصبی 1D-CNN روی سری زمانی پوز"),
  h2Fa("۶.۱  چرا 1D-CNN و نه CNN دوبعدی؟"),
  pFa("CNN دوبعدی روی فریم خام ویدیو دو ایراد بزرگ دارد: (الف) دوباره‌کاری کاری که MediaPipe انجام می‌دهد؛ (ب) با ۲۴۶ نمونه قطعاً overfit می‌شود (CNN معمولاً هزاران نمونه نیاز دارد). در عوض، 1D-CNN روی سری زمانی نقاط پوز کار می‌کند — ورودی یک ماتریس T فریم × ۹۹ کانال (۳۳ نقطه × ۳ مختصات xyz) است. این مقیاس به‌مراتب کوچک‌تر است و با augmentation قابل آموزش روی ۲۴۶ نمونه است."),

  h2Fa("۶.۲  داده‌ی موجود برای آموزش"),
  pFa("شما در کامیت c600dea مجموعاً ۱۱۴ فایل JSON پوز را اضافه کردید — یعنی ۶۱٪ از ۱۸۸ مسابقه. این برای فاز ۳ کافی است، با یک هشدار: تنها ۲۰ نمونه‌ی برچسب «مبتدی» داریم و فقط حدود ۱۰ تا از آن‌ها با فایل پوز match می‌شوند. بنابراین تنگنای واقعی فاز ۳ تعداد نمونه‌های minority است، نه تعداد کلی نمونه‌ها."),

  h2Fa("۶.۳  Augmentation — چطور با ۲۴۶ نمونه CNN آموزش دهیم؟"),
  pFa("سه تکنیک augmentation روی سری زمانی پوز اعمال می‌کنیم:"),
  bulletFa("افزودن نویز گاوسی به نقاط (شبیه‌سازی خطای BlazePose)"),
  bulletFa("Time-warping: کش‌دادن یا فشرده‌کردن خطی محور زمان"),
  bulletFa("Mirroring: قرینه کردن left/right (با جابجایی نقاط چپ و راست) — ورزشکار راست‌دست به چپ‌دست تبدیل می‌شود"),
  pFa("هر نمونه می‌تواند به ۵ تا ۱۰ نسخه‌ی متفاوت گسترش یابد، که عملاً اندازه‌ی dataset را برای CNN چند برابر می‌کند."),

  h2Fa("۶.۴  معماری پیشنهادی"),
  pFa("یک شبکه‌ی سبک با ۲ تا ۳ لایه‌ی کانولوشن یک‌بعدی، Global Average Pooling، یک لایه‌ی Dense، و خروجی sigmoid برای دو کلاس. تعداد پارامتر کلی زیر ۱۰۰هزار تا overfit نشود. در سند روش‌شناسی فاز ۳ به ST-GCN (Spatial-Temporal Graph Convolutional Network) به‌عنوان نقطه‌ی ایده‌آل آینده اشاره می‌کنیم — با داده‌ی بیشتر، ST-GCN روی این مسئله state-of-the-art است."),
];

// ---- Section 7: Phase 4 ---------------------------------------------------

const PHASE4 = [
  h1Fa("۷. فاز چهارم — گزارش مقایسه‌ای علمی"),
  pFa("در فاز چهارم نتایج فاز ۲ و فاز ۳ روی نمونه‌های یکسان (sample_index مشترک) با هم مقایسه می‌شوند:"),
  bulletFa("نمودار ROC در یک تصویر برای همه‌ی مدل‌ها (RF، XGB، CNN)"),
  bulletFa("نمودار Precision-Recall در یک تصویر برای همه‌ی مدل‌ها"),
  bulletFa("جدول مقایسه‌ی Macro-F1 و F1 کلاس مبتدی، با میانگین ± انحراف معیار"),
  bulletFa("آزمون آماری McNemar برای بررسی معناداری اختلاف بین CNN و بهترین baseline"),
  bulletFa("آزمون حساسیت برچسب: ۱۰٪ از برچسب‌های Phase 1 را عوض می‌کنیم و دوباره مدل را آموزش می‌دهیم تا ببینیم نتایج چقدر robust هستند"),
  bulletFa("متن آکادمیک نهایی برای فصل پایان‌نامه — با اسکیل research-paper-writing (با aiScore=۸۸) که در پروژه نصب شده"),

  h2Fa("سناریوهای ممکن و نحوه گزارش هر کدام"),
  spacer(),
  tableFa(
    [
      ["سناریو", "نحوه گزارش در پایان‌نامه"],
      ["CNN از baseline قابل‌توجه بهتر می‌شود", "ادعای کشف الگوی زمانی که فیچرهای مهندسی‌شده آن را از دست می‌دهند؛ ST-GCN را به‌عنوان مسیر ادامه پیشنهاد می‌کنیم"],
      ["CNN با baseline برابر می‌شود", "نشان می‌دهد فیچرهای مهندسی‌شده‌ی فعلی همان اطلاعات را دارند که CNN از سری زمانی استخراج می‌کند — یافته‌ی آموزنده"],
      ["CNN از baseline بدتر می‌شود", "صادقانه گزارش می‌کنیم: با ۲۴۶ نمونه و ۲۰ مبتدی، deep learning به فضای ساختاریافته‌ی RF نمی‌رسد. این یک یافته‌ی روشن برای ادبیات است"],
    ],
    [3500, 5860],
  ),
];

// ---- Section 8: Status & Next Steps ---------------------------------------

const STATUS = [
  h1Fa("۸. وضعیت کنونی و گام‌های بعدی"),
  spacer(),
  tableFa(
    [
      ["وضعیت", "اقدام"],
      ["فاز ۱ — اجرا، نتایج و سند Word کامیت شدند", "استاد روش‌شناسی Phase 1 را بررسی و تأیید کند"],
      ["فاز ۲ — اجرا و کامیت شد (commit 24d12df)", "استاد جدول نتایج (۵.۷) و هشدار tautology (۵.۹) را بررسی کند"],
      ["فاز ۳ — اسکفولد روی شاخه phd-ml/phase3-cnn", "دانشجو/استاد سند روش‌شناسی فاز ۳ را بررسی، سپس pipeline اجرا شود"],
      ["فاز ۴ — هنوز شروع نشده", "پس از اجرای فاز ۳، گزارش مقایسه‌ای با اسکیل research-paper-writing"],
    ],
    [3300, 6060],
  ),

  h2Fa("نکات مهم برای دانشجو"),
  bulletFa("هر فاز روی شاخه‌ی گیت جداگانه کار می‌کند تا main همیشه پایدار بماند"),
  bulletFa("هر فاز یک سند Word متدولوژی + یک سند Markdown همراه دارد"),
  bulletFa("سند پایان‌نامه می‌تواند مستقیماً از این اسناد ساخته شود — بسیاری از جداول و نتایج آماده هستند"),
  bulletFa("در فاز چهارم، اسکیل research-paper-writing (با ساختار NeurIPS/ICML) متن نهایی را با کیفیت ژورنال آماده می‌کند"),
  bulletFa("هر اشتباهی در یک فاز، در فاز بعد قابل اصلاح است؛ فعلاً فاز ۱ تأیید استاد را برای حرکت رسمی به فاز بعد می‌خواهد"),
];

// ---- Section 9: Closing -------------------------------------------------

const CLOSING = [
  h1Fa("۹. سخن پایانی"),
  pFa("این پروژه یک نمونه‌ی خوب از کاربرد روش‌های یادگیری ماشین در ورزش است که با دو محدودیت سخت کار می‌کند: داده‌ی کم (۲۴۶ نمونه) و ممنوعیت برچسب‌گذاری دستی. به‌جای فرار از این محدودیت‌ها، آن‌ها را به‌عنوان بخش روش‌شناسی پایان‌نامه پذیرفته‌ایم: weak supervision با Skill Proxy، triangulation با چهار الگوریتم خوشه‌بندی، و باند صداقت برای پذیرش هر نتیجه."),
  pFa("امیدوارم این گزارش به دانشجو کمک کند تا تصویر کامل پروژه را داشته باشد و هر زمان استاد سؤال کرد، با اطمینان پاسخ بدهد. در صورت نیاز به توضیح بیشتر، اسناد روش‌شناسی هر فاز (PHASE1_METHODOLOGY.docx و PHASE2_METHODOLOGY.docx) جزئیات فنی کامل‌تری دارند."),
  spacer(),
  pFa("موفق باشید!", { bold: true }),
];

// ---------- assembly ------------------------------------------------------

const doc = new Document({
  creator: "airano",
  title: "گزارش پیشرفت پایان‌نامه — تحلیل عملکرد سنگ‌نوردی سرعت",
  description: "Persian student-facing progress report covering Phases 1-4",
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
          text: "گزارش دانشجو — تحلیل عملکرد سنگ‌نوردی سرعت",
          font: FONT, size: 18, color: "808080", rtl: true,
        })],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", font: FONT, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "808080" }),
          new TextRun({ text: " / ", font: FONT, size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 18, color: "808080" }),
        ],
      })] }),
    },
    children: [
      ...COVER,
      h1Fa("فهرست مطالب"),
      new TableOfContents("فهرست مطالب", { hyperlink: true, headingStyleRange: "1-3" }),
      pagebreak(),
      ...INTRO,
      ...PROJECT_MAP,
      pagebreak(),
      ...PHASE1,
      pagebreak(),
      ...FIGURES,
      pagebreak(),
      ...PHASE2,
      pagebreak(),
      ...PHASE3,
      ...PHASE4,
      pagebreak(),
      ...STATUS,
      ...CLOSING,
    ],
  }],
});

const outPath = path.resolve(REPO_ROOT, "STUDENT_REPORT_FA.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`Wrote ${outPath} (${buf.length} bytes)`);
});

/**
 * Phase 4 Comparative Academic Report - DOCX builder.
 *
 * Generates a Persian advisor/student-facing Word report comparing Phase 2
 * feature-engineered baselines and Phase 3 1D-CNN on the identical
 * lane-matched sample_index subset.
 *
 * Run:  node phd_ml/docx_builder/build_phase4_docx.js
 * Out:  phd_ml/phase4/PHASE4_COMPARATIVE_REPORT.docx
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, TableOfContents,
  ImageRun,
} = require("docx");

const FONT_FA = "Tahoma";
const FONT_LATIN = "Arial";
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const OUT_PATH = path.resolve(REPO_ROOT, "phd_ml", "phase4", "PHASE4_COMPARATIVE_REPORT.docx");
const RESULTS_PATH = path.resolve(REPO_ROOT, "data", "phd_ml", "phase4", "results.json");
const FIG_DIR = path.resolve(REPO_ROOT, "figures", "phd_ml", "phase4");

const results = JSON.parse(fs.readFileSync(RESULTS_PATH, "utf8"));
const metrics = results.metrics_common;
const audit = results.audit;
const paired = results.paired_tests.mcnemar_exact;
const boot = results.paired_tests.bootstrap_reference_minus_cnn;

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const headerShade = { fill: "1F4E79", type: ShadingType.CLEAR, color: "auto" };
const warnShade = { fill: "FFF2CC", type: ShadingType.CLEAR, color: "auto" };
const goodShade = { fill: "E2F0D9", type: ShadingType.CLEAR, color: "auto" };

const faRun = (text, opts = {}) => new TextRun({
  text, font: FONT_FA, size: 22, rtl: true, ...opts,
});

const enRun = (text, opts = {}) => new TextRun({
  text, font: FONT_LATIN, size: 21, ...opts,
});

const pFa = (text, opts = {}) => new Paragraph({
  bidirectional: true,
  alignment: opts.align || AlignmentType.RIGHT,
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
  children: [faRun(text, opts.run || {})],
});

const pMixed = (runs, opts = {}) => new Paragraph({
  bidirectional: true,
  alignment: opts.align || AlignmentType.RIGHT,
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
  children: runs,
});

const h1Fa = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  bidirectional: true,
  alignment: AlignmentType.RIGHT,
  spacing: { before: 260, after: 180 },
  children: [faRun(text, { size: 32, bold: true, color: "1F4E79" })],
});

const h2Fa = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  bidirectional: true,
  alignment: AlignmentType.RIGHT,
  spacing: { before: 220, after: 140 },
  children: [faRun(text, { size: 26, bold: true, color: "2E74B5" })],
});

const h3Fa = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  bidirectional: true,
  alignment: AlignmentType.RIGHT,
  spacing: { before: 170, after: 100 },
  children: [faRun(text, { size: 23, bold: true, color: "404040" })],
});

const bulletFa = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  bidirectional: true,
  alignment: AlignmentType.RIGHT,
  spacing: { after: 70 },
  children: [faRun(text)],
});

const pagebreak = () => new Paragraph({ children: [new PageBreak()] });
const spacer = () => new Paragraph({ children: [new TextRun(" ")] });

const fmt = (value, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "تعریف‌نشده";
  return Number(value).toFixed(digits);
};

const metricByModel = (name) => metrics.find((row) => row.model === name);
const bootByMetric = (name) => boot.find((row) => row.metric === name);

const makeCell = (content, opts = {}) => {
  const lines = Array.isArray(content) ? content : [content];
  const header = opts.header || false;
  const shade = opts.shade;
  return new TableCell({
    borders: cellBorders,
    width: { size: opts.width || 2500, type: WidthType.DXA },
    shading: header ? headerShade : shade,
    margins: { top: 90, bottom: 90, left: 120, right: 120 },
    children: lines.map((line) => new Paragraph({
      bidirectional: true,
      alignment: AlignmentType.RIGHT,
      children: [faRun(String(line), {
        bold: header,
        color: header ? "FFFFFF" : "202020",
        size: header ? 20 : 19,
      })],
    })),
  });
};

const tableFa = (rows, widths) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: widths,
  rows: rows.map((row, i) => new TableRow({
    tableHeader: i === 0,
    children: row.map((cell, j) => makeCell(cell, {
      width: widths[j],
      header: i === 0,
    })),
  })),
});

const callout = (title, body, shade = warnShade) => new Table({
  width: { size: 9360, type: WidthType.DXA },
  rows: [new TableRow({
    children: [new TableCell({
      borders: cellBorders,
      shading: shade,
      margins: { top: 160, bottom: 160, left: 180, right: 180 },
      children: [
        new Paragraph({
          bidirectional: true,
          alignment: AlignmentType.RIGHT,
          spacing: { after: 80 },
          children: [faRun(title, { bold: true, size: 23 })],
        }),
        pFa(body, { after: 0 }),
      ],
    })],
  })],
});

const figure = (filename, caption, width = 560, height = 330) => {
  const figPath = path.join(FIG_DIR, filename);
  if (!fs.existsSync(figPath)) {
    return [pFa(`شکل پیدا نشد: ${filename}`)];
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 80 },
      children: [new ImageRun({
        type: "png",
        data: fs.readFileSync(figPath),
        transformation: { width, height },
        altText: { title: filename, description: caption, name: filename },
      })],
    }),
    pFa(caption, { align: AlignmentType.CENTER, run: { italics: true, color: "595959", size: 19 } }),
  ];
};

const compactModelName = (name) => ({
  dummy_majority: "Dummy",
  logreg_balanced: "LogReg balanced",
  rf_balanced: "RF balanced",
  xgb_scale_pos_weight: "XGB weighted",
  rf_smote: "RF SMOTE",
  xgb_smote: "XGB SMOTE",
  cnn1d: "1D-CNN",
}[name] || name);

const cover = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 2200, after: 260 },
    children: [enRun("Speed Climbing Performance Analysis", {
      size: 44, bold: true, color: "1F4E79",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 160 },
    children: [enRun("PhD ML Track, Phase 4", {
      size: 32, bold: true, color: "2E74B5",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    bidirectional: true,
    spacing: { after: 520 },
    children: [faRun("گزارش مقایسه‌ای فاز ۲ و فاز ۳", {
      size: 30, bold: true, color: "404040",
    })],
  }),
  pMixed([
    faRun("شاخه: ", { color: "595959" }),
    enRun("phd-ml/phase4-report", { font: "Consolas", color: "595959" }),
  ], { align: AlignmentType.CENTER }),
  pMixed([
    faRun("تاریخ اجرا: ", { color: "595959" }),
    enRun("2026-06-27", { color: "595959" }),
  ], { align: AlignmentType.CENTER }),
  pFa("مقایسه منصفانه baselineهای feature-engineered با 1D-CNN روی نمونه‌های مشترک lane-matched", {
    align: AlignmentType.CENTER,
    before: 700,
    run: { size: 22, color: "595959" },
  }),
  pagebreak(),
];

const logreg = metricByModel("logreg_balanced");
const cnn = metricByModel("cnn1d");

const executive = [
  h1Fa("خلاصه اجرایی"),
  pFa(`فاز چهارم برای پاسخ دقیق به سؤال مقایسه‌ای استاد ساخته شد: آیا baselineهای فاز ۲ و 1D-CNN فاز ۳ روی نمونه‌های یکسان چه تفاوتی دارند؟ برای جلوگیری از مقایسه ناعادلانه، همه متریک‌ها فقط روی ${audit.common_n_samples} نمونه مشترک محاسبه شدند، شامل ${audit.common_advanced_samples} advanced و فقط ${audit.common_beginner_samples} beginner.`),
  pFa("نتیجه اصلی صادقانه است. `logreg_balanced` روی subset مشترک کامل عمل کرد، اما این مدل همان سقف feature-engineered و تا حدی تاتولوژیک است، چون برچسب‌های فاز ۱ از همان فضای فیچر ساخته شده‌اند. در مقابل، 1D-CNN فاز ۳ آزمون مستقل‌تری است، چون فقط سری زمانی pose را دیده است."),
  callout(
    "نتیجه مرکزی",
    `روی ۱۰۷ نمونه مشترک، Macro-F1 مدل logreg برابر ${fmt(logreg.f1_macro)} و Macro-F1 مدل CNN برابر ${fmt(cnn.f1_macro)} شد. CNN فقط ${cnn.tp} نمونه از ${audit.common_beginner_samples} beginner را درست گرفت. نتیجه منفی است، اما دلیل اصلی آن کمبود beginner lane-matched است، نه اینکه ایده CNN به شکل مطلق رد شده باشد.`,
    goodShade,
  ),
  pFa(`آزمون McNemar exact بین logreg و CNN نشان داد ${paired.reference_only_correct} نمونه فقط توسط logreg درست پیش‌بینی شده و هیچ نمونه‌ای فقط توسط CNN درست نشده است. p-value برابر ${fmt(paired.exact_binomial_p_value, 6)} است. bootstrap جفتی نیز فاصله Macro-F1 را به نفع فاز ۲ تایید کرد.`),
];

const method = [
  h1Fa("۱. طراحی مقایسه"),
  h2Fa("۱.۱ قانون sample_index مشترک"),
  pFa("فاز ۲ روی ۲۴۶ نمونه اجرا شده بود، اما فاز ۳ پس از اصلاح lane-aware loader فقط ۱۰۷ نمونه معتبر داشت. بنابراین گزارش مستقیم نمره‌های کل فاز ۲ کنار فاز ۳ عادلانه نیست. در این گزارش، خروجی‌های held-out فاز ۲ با خروجی‌های held-out فاز ۳ فقط روی sample_indexهای مشترک join شدند."),
  tableFa([
    ["مورد", "تعداد"],
    ["نمونه‌های فاز ۱ و فاز ۲", audit.phase2_total_samples],
    ["beginner در فاز ۱ و فاز ۲", audit.phase2_beginner_samples],
    ["نمونه‌های lane-matched فاز ۳", audit.phase3_total_samples],
    ["نمونه‌های مشترک مقایسه", audit.common_n_samples],
    ["beginner مشترک", audit.common_beginner_samples],
  ], [5200, 4160]),
  h2Fa("۱.۲ caveat فاز ۲"),
  pFa("فاز ۲ از همان ۱۵ فیچر مهندسی‌شده‌ای استفاده می‌کند که فاز ۱ برای ساخت pseudo-labelها به کار برده بود. بنابراین عملکرد عالی فاز ۲ باید سقف feature-engineered در نظر گرفته شود، نه شواهد مستقل کامل از یادگیری مهارت."),
  h2Fa("۱.۳ استقلال نسبی فاز ۳"),
  pFa("فاز ۳ فیچرهای مهندسی‌شده را نمی‌بیند. مدل 1D-CNN فقط ورودی pose time-series با شکل T=200 و C=99 را دریافت می‌کند. به همین دلیل فاز ۳ آزمون مستقل‌تری از این پرسش است که آیا raw pose می‌تواند partition فاز ۱ را بازیابی کند یا نه."),
];

const dataSection = [
  h1Fa("۲. ممیزی داده"),
  pFa("اصلاح lane-aware در فاز ۳ باعث حذف نمونه‌هایی شد که pose موجود با lane برچسب‌خورده هم‌خوان نبود یا pose نداشتند. این اصلاح از نظر روش‌شناختی ضروری بود، اما تعداد beginner معتبر را شدیداً کم کرد."),
  tableFa([
    ["وضعیت intersect فاز ۳", "تعداد"],
    ["ok", audit.phase3_intersect_status_counts.ok || 0],
    ["single_lane_mismatch:left", audit.phase3_intersect_status_counts["single_lane_mismatch:left"] || 0],
    ["single_lane_mismatch:right", audit.phase3_intersect_status_counts["single_lane_mismatch:right"] || 0],
    ["single_lane_uncertain:center", audit.phase3_intersect_status_counts["single_lane_uncertain:center"] || 0],
    ["missing_pose", audit.phase3_intersect_status_counts.missing_pose || 0],
  ], [5600, 3760]),
  ...figure("lane_matched_data_bottleneck.png", "کاهش تعداد کل نمونه‌ها و کاهش شدید beginner پس از strict lane matching.", 520, 285),
  callout("محدودیت اصلی", "با ۶ نمونه beginner، هر fold فاز ۳ فقط دو نمونه beginner در validation دارد. بنابراین ضعف recall کلاس beginner در CNN بیشتر از هر چیز، محدودیت داده معتبر را نشان می‌دهد.", warnShade),
];

const resultsSection = [
  h1Fa("۳. نتایج روی نمونه‌های مشترک"),
  tableFa([
    ["مدل", "فاز", "Macro-F1", "F1 beginner", "Recall beginner", "ROC-AUC", "PR-AUC", "Confusion"],
    ...metrics.map((row) => [
      compactModelName(row.model),
      row.source_phase.includes("phase2") ? "۲" : "۳",
      fmt(row.f1_macro),
      fmt(row.f1_beginner),
      fmt(row.recall_beginner),
      fmt(row.roc_auc),
      fmt(row.pr_auc),
      `[[${row.tn}, ${row.fp}], [${row.fn}, ${row.tp}]]`,
    ]),
  ], [1550, 700, 1200, 1250, 1350, 1050, 1050, 2210]),
  spacer(),
  ...figure("common_metric_comparison.png", "مقایسه متریک‌های اصلی روی همان ۱۰۷ sample_index مشترک.", 610, 330),
  ...figure("beginner_precision_recall.png", "تمرکز روی کلاس beginner نشان می‌دهد CNN فقط یک نمونه beginner را درست تشخیص داده است.", 590, 315),
  ...figure("reference_vs_cnn_confusion.png", "ماتریس‌های درهم‌ریختگی logreg و CNN روی subset مشترک.", 520, 250),
  ...figure("reference_vs_cnn_curves.png", "ROC و PR روی نمونه‌های مشترک. PR-AUC پایین CNN با کمیابی beginner سازگار است.", 610, 255),
];

const pairedSection = [
  h1Fa("۴. آزمون‌های جفتی"),
  h2Fa("۴.۱ McNemar exact"),
  tableFa([
    ["شاخص", "مقدار"],
    ["هر دو درست", paired.both_correct],
    ["هر دو غلط", paired.both_wrong],
    ["فقط logreg درست", paired.reference_only_correct],
    ["فقط CNN درست", paired.cnn_only_correct],
    ["تعداد discordant", paired.discordant_pairs],
    ["p-value exact", fmt(paired.exact_binomial_p_value, 6)],
  ], [5200, 4160]),
  h2Fa("۴.۲ Bootstrap جفتی"),
  pFa("در جدول زیر جهت اختلاف `logreg_balanced - cnn1d` است. عدد مثبت یعنی برتری مدل feature-engineered فاز ۲."),
  tableFa([
    ["Metric", "میانگین اختلاف", "CI 95%"],
    ...["accuracy", "balanced_accuracy", "f1_macro", "f1_beginner", "recall_beginner", "roc_auc", "pr_auc"].map((name) => {
      const row = bootByMetric(name);
      return [
        name,
        fmt(row.reference_minus_cnn_mean),
        `[${fmt(row.ci95_low)}, ${fmt(row.ci95_high)}]`,
      ];
    }),
  ], [3300, 3000, 3060]),
];

const interpretation = [
  h1Fa("۵. تفسیر آکادمیک"),
  h2Fa("۵.۱ آیا فاز ۲ بهتر است؟"),
  pFa("از نظر عددی بله. روی subset مشترک، تمام baselineهای غیر trivial فاز ۲ بسیار بهتر از CNN هستند. اما این جمله باید همراه با caveat بیاید: فاز ۲ از همان فیچرهایی استفاده کرده که labelهای فاز ۱ از آنها ساخته شده‌اند. بنابراین فاز ۲ سقف مهندسی‌شده است."),
  h2Fa("۵.۲ آیا CNN شکست خورده است؟"),
  pFa("خیر، نتیجه CNN منفی است، اما از نظر علمی قابل دفاع است. فاز ۳ آزمون سخت‌تری انجام داد: بازیابی pseudo-labelها از raw pose time-series بدون دسترسی به summary featureها. با فقط ۶ beginner معتبر، این کار برای 1D-CNN کوچک بیش از حد داده‌محدود است."),
  callout("جمله پیشنهادی برای استاد", "نتایج نشان می‌دهد baselineهای feature-engineered سقف عملکرد بالایی ایجاد می‌کنند، اما به دلیل وابستگی روش‌شناختی labelها به همان فیچرها، این نتیجه باید تاتولوژیک تفسیر شود. 1D-CNN آزمون مستقل‌تری روی pose time-series فراهم کرد و ضعیف‌تر بود؛ علت اصلی، کاهش دیتاست معتبر به ۱۰۷ نمونه و فقط ۶ beginner پس از strict lane matching است.", goodShade),
  h2Fa("۵.۳ نتیجه پایان‌نامه"),
  bulletFa("استفاده از CNN دوبعدی روی فریم خام حذف شد و ورودی عصبی فقط keypoint time-series بود."),
  bulletFa("هیچ label انسانی اضافه نشد. همه labelها همان pseudo-labelهای فاز ۱ هستند."),
  bulletFa("نتیجه منفی CNN گزارش شد و پنهان یا over-tune نشد."),
  bulletFa("گام بعدی علمی، افزایش coverage داده lane-matched و سپس آزمون ST-GCN است."),
];

const deliverables = [
  h1Fa("۶. خروجی‌ها و بازتولید"),
  tableFa([
    ["مسیر", "محتوا"],
    ["data/phd_ml/phase4/results.json", "خلاصه عددی، audit، paired tests و مسیر شکل‌ها"],
    ["data/phd_ml/phase4/metrics_common.csv", "متریک همه مدل‌ها روی ۱۰۷ نمونه مشترک"],
    ["data/phd_ml/phase4/common_predictions_long.csv", "پیش‌بینی همه مدل‌ها در قالب long"],
    ["data/phd_ml/phase4/paired_predictions_logreg_vs_cnn.csv", "مقایسه نمونه‌به‌نمونه logreg و CNN"],
    ["figures/phd_ml/phase4/*.png", "پنج شکل گزارش"],
    ["phd_ml/phase4/PHASE4_RATIONALE.md", "نسخه Markdown و قابل مرور سریع"],
  ], [4300, 5060]),
  h2Fa("دستور بازتولید"),
  pMixed([enRun("uv run python -m phd_ml.phase4.run_pipeline", { font: "Consolas", size: 20 })]),
  pMixed([enRun("node phd_ml/docx_builder/build_phase4_docx.js", { font: "Consolas", size: 20 })]),
];

const doc = new Document({
  creator: "airano",
  title: "Phase 4 Comparative Academic Report",
  description: "Persian comparative report for Phase 2 feature-engineered baselines and Phase 3 1D-CNN",
  styles: {
    default: { document: { run: { font: FONT_FA, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: FONT_FA, color: "1F4E79", rtl: true },
        paragraph: { spacing: { before: 260, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT_FA, color: "2E74B5", rtl: true },
        paragraph: { spacing: { before: 220, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT_FA, color: "404040", rtl: true },
        paragraph: { spacing: { before: 170, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: "•",
        alignment: AlignmentType.RIGHT,
        style: { paragraph: { indent: { right: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [pFa("تحلیل عملکرد سنگ‌نوردی سرعت، گزارش مقایسه‌ای فاز چهارم", {
        run: { size: 18, color: "808080" },
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          faRun("صفحه ", { size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT_FA, size: 18, color: "808080" }),
          faRun(" از ", { size: 18, color: "808080" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT_FA, size: 18, color: "808080" }),
        ],
      })] }),
    },
    children: [
      ...cover,
      h1Fa("فهرست مطالب"),
      new TableOfContents("فهرست مطالب", { hyperlink: true, headingStyleRange: "1-3" }),
      pagebreak(),
      ...executive,
      pagebreak(),
      ...method,
      pagebreak(),
      ...dataSection,
      pagebreak(),
      ...resultsSection,
      pagebreak(),
      ...pairedSection,
      pagebreak(),
      ...interpretation,
      pagebreak(),
      ...deliverables,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT_PATH, buf);
  console.log(`Wrote ${OUT_PATH} (${buf.length} bytes)`);
});


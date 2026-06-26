/**
 * Phase 3 Methodology + Results Document — DOCX builder.
 *
 * Generates a Persian advisor/student-facing Word document for the 1D-CNN
 * pose-time-series phase. The document is intentionally honest about the
 * lane-matched data bottleneck and frames the CNN result as a defensible
 * negative result rather than a failed implementation.
 *
 * Run:  node build_phase3_docx.js
 * Out:  ../phase3/PHASE3_METHODOLOGY.docx
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
const OUT_PATH = path.resolve(REPO_ROOT, "phd_ml", "phase3", "PHASE3_METHODOLOGY.docx");
const RESULTS_PATH = path.resolve(REPO_ROOT, "data", "phd_ml", "phase3", "results.json");
const FIG_DIR = path.resolve(REPO_ROOT, "figures", "phd_ml", "phase3");

const results = JSON.parse(fs.readFileSync(RESULTS_PATH, "utf8"));

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
  if (value === null || value === undefined) return "تعریف‌نشده";
  return Number(value).toFixed(digits);
};

const metric = (key) => {
  const mean = results.metrics_aggregated[`${key}_mean`];
  const std = results.metrics_aggregated[`${key}_std`];
  return `${fmt(mean)} ± ${fmt(std)}`;
};

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
        color: header ? "FFFFFF" : "000000",
        size: header ? 21 : 20,
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

const classBalance = results.dataset_audit.class_balance;
const statusCounts = results.dataset_audit.intersect_status_counts;
const folds = results.metrics_per_fold;

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
    children: [enRun("PhD ML Track — Phase 3", {
      size: 32, bold: true, color: "2E74B5",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    bidirectional: true,
    spacing: { after: 520 },
    children: [faRun("شبکه عصبی 1D-CNN روی سری زمانی نقاط بدن", {
      size: 28, bold: true, color: "404040",
    })],
  }),
  pMixed([
    faRun("شاخه: ", { color: "595959" }),
    enRun("phd-ml/phase3-cnn", { font: "Consolas", color: "595959" }),
  ], { align: AlignmentType.CENTER }),
  pMixed([
    faRun("تاریخ اجرا: ", { color: "595959" }),
    enRun("2026-06-27", { color: "595959" }),
  ], { align: AlignmentType.CENTER }),
  pFa("سند روش‌شناسی، اجرای تجربی، نتایج، محدودیت‌ها و توصیه‌های فاز سوم", {
    align: AlignmentType.CENTER,
    before: 700,
    run: { size: 22, color: "595959" },
  }),
  pagebreak(),
];

const executive = [
  h1Fa("خلاصه اجرایی"),
  pFa("فاز سوم برای پاسخ به درخواست استاد درباره مدل CNN اجرا شد، اما نه با CNN دوبعدی روی فریم خام ویدئو. ورودی مدل، سری زمانی نقاط بدن استخراج‌شده با BlazePose است: هر نمونه به شکل T=200 فریم و C=99 کانال، یعنی ۳۳ نقطه بدن در سه مختصات x، y و z."),
  pFa("هدف علمی این فاز این بود که ببینیم آیا یک 1D-CNN سبک، بدون دیدن فیچرهای مهندسی‌شده فاز اول، می‌تواند همان برچسب‌های خودکار فاز اول را بازیابی کند یا نه. این دقیقاً آزمونی است که caveat تاتولوژی فاز دوم را دور می‌زند."),
  pFa("در حین اجرا یک اصلاح مهم انجام شد: loader ابتدا فقط با race_id join می‌کرد، اما دیتاست برچسب‌خورده فاز اول per-lane است. بنابراین loader بازنویسی شد تا فقط pose مربوط به همان lane وارد مدل شود. پس از این اصلاح، دیتاست معتبر فاز سوم به ۱۰۷ نمونه lane-matched کاهش یافت: ۱۰۱ advanced و فقط ۶ beginner."),
  callout("نتیجه اصلی", `مدل 1D-CNN با ۷۹٬۹۲۲ پارامتر روی stratified 3-fold به Macro-F1 = ${metric("f1_macro")} و F1 کلاس beginner = ${metric("f1_minority")} رسید. این نتیجه پایین‌تر از baseline فاز دوم است، اما از نظر علمی ارزشمند است: با فقط ۶ نمونه beginner معتبر، bottleneck اصلی داده است، نه صرفاً معماری مدل.`),
  pFa("بنابراین پیام قابل دفاع برای استاد این است: پروژه CNN را اجرا کرده، اما با طراحی درست و بدون دوباره‌کاری ویدئویی. نتیجه نشان می‌دهد در اندازه داده فعلی، فیچرهای سینماتیک مهندسی‌شده بسیار قابل اعتمادتر از representation learning خام روی pose هستند. گام آینده، افزایش پوشش pose lane-matched و سپس ارزیابی ST-GCN است."),
];

const method = [
  h1Fa("۱. منطق علمی فاز سوم"),
  h2Fa("۱.۱ چرا 1D-CNN و نه CNN دوبعدی؟"),
  bulletFa("CNN دوبعدی روی فریم خام کار MediaPipe را دوباره انجام می‌دهد و با ۲۴۶ نمونه به احتمال زیاد overfit می‌شود."),
  bulletFa("1D-CNN روی سری زمانی نقاط بدن، ورودی کم‌حجم‌تر و مرتبط‌تری دارد و با داده محدود سازگارتر است."),
  bulletFa("این انتخاب با هدف پروژه هم‌خوان است: حفظ pipeline قابل تفسیر و اضافه‌کردن یک baseline عصبی قابل دفاع."),
  h2Fa("۱.۲ معماری مدل"),
  tableFa([
    ["بخش", "تنظیم"],
    ["ورودی", "T=200، C=99"],
    ["کانولوشن‌ها", "99→48، سپس 48→96، سپس 96→96"],
    ["Regularization", "BatchNorm + ReLU + Dropout 0.3"],
    ["Pooling", "Global Average Pooling روی محور زمان"],
    ["Classifier", "Linear 96→48→2"],
    ["تعداد پارامتر", String(results.model_parameters)],
  ], [3300, 6060]),
  h2Fa("۱.۳ Augmentation"),
  bulletFa("نویز گاوسی برای شبیه‌سازی jitter نقاط BlazePose"),
  bulletFa("time-warping برای تغییر ریتم صعود"),
  bulletFa("mirror برای قرینه‌سازی چپ و راست بدن"),
  bulletFa("augmentation فقط روی training fold اعمال شده و validation هرگز augmented نشده است."),
];

const dataAudit = [
  h1Fa("۲. اصلاح حیاتی: lane-aware loader"),
  pFa("برچسب‌های فاز اول در سطح lane هستند، یعنی هر race می‌تواند دو ردیف جداگانه left و right داشته باشد. اگر loader فقط با race_id join کند، ممکن است یک pose تک‌ورزشکار برای هر دو lane استفاده شود. این خطا پیش از گزارش نتیجه اصلاح شد."),
  tableFa([
    ["وضعیت intersect", "تعداد"],
    ["ok", statusCounts.ok || 0],
    ["single_lane_mismatch:left", statusCounts["single_lane_mismatch:left"] || 0],
    ["single_lane_mismatch:right", statusCounts["single_lane_mismatch:right"] || 0],
    ["single_lane_uncertain:center", statusCounts["single_lane_uncertain:center"] || 0],
    ["missing_pose", statusCounts.missing_pose || 0],
  ], [5200, 4160]),
  spacer(),
  tableFa([
    ["کلاس", "تعداد در subset معتبر"],
    ["advanced", classBalance.advanced || 0],
    ["beginner", classBalance.beginner || 0],
  ], [5200, 4160]),
  callout("تفسیر داده", "بعد از enforce کردن lane correctness، فقط ۶ نمونه beginner باقی ماند. در 3-fold CV هر fold فقط دو beginner در validation دارد. بنابراین متریک‌های minority بسیار ناپایدارند و هر نتیجه CNN باید با این محدودیت خوانده شود.", warnShade),
];

const resultsSection = [
  h1Fa("۳. نتایج تجربی"),
  h2Fa("۳.۱ نتایج میانگین روی foldها"),
  tableFa([
    ["متریک", "میانگین ± انحراف معیار"],
    ["Macro-F1", metric("f1_macro")],
    ["F1 beginner", metric("f1_minority")],
    ["Precision beginner", metric("precision_minority")],
    ["Recall beginner", metric("recall_minority")],
    ["ROC-AUC", metric("roc_auc")],
    ["PR-AUC", metric("pr_auc")],
    ["Epochs", metric("epochs")],
  ], [4300, 5060]),
  h2Fa("۳.۲ نتایج هر fold"),
  tableFa([
    ["Fold", "Confusion matrix", "Macro-F1", "F1 beginner", "ROC-AUC"],
    ...folds.map((f) => [
      String(f.fold),
      JSON.stringify(f.confusion_matrix),
      fmt(f.f1_macro),
      fmt(f.f1_minority),
      fmt(f.roc_auc),
    ]),
  ], [1000, 3200, 1700, 1700, 1760]),
  h2Fa("۳.۳ نمودارها"),
  ...figure("metric_summary.png", "مقایسه متریک‌های CNN با خط مرجع فاز دوم. فاصله زیاد با baseline فاز دوم دیده می‌شود.", 560, 400),
  ...figure("confusion_matrix.png", "ماتریس درهم‌ریختگی pooled. مدل فقط ۱ نمونه از ۶ beginner را درست گرفته است.", 430, 350),
  ...figure("training_curves.png", "منحنی‌های loss آموزش و اعتبارسنجی در سه fold. early stopping بین ۹ تا ۱۱ epoch رخ داده است.", 560, 390),
];

const interpretation = [
  h1Fa("۴. تفسیر قابل دفاع برای پایان‌نامه"),
  callout("نتیجه منفی، اما مفید", "این نتیجه شکست پروژه نیست. نتیجه نشان می‌دهد با n=107 و فقط ۶ نمونه beginner معتبر، 1D-CNN نمی‌تواند ساختار pseudo-label فاز اول را به‌خوبی بازیابی کند. این یافته دقیقاً با قانون صداقت علمی پروژه هم‌خوان است.", goodShade),
  h2Fa("۴.۱ مقایسه با فاز دوم"),
  pFa("فاز دوم روی فیچرهای مهندسی‌شده به Macro-F1 حدود ۰٫۹۷۸ رسید، اما همان نتیجه به‌دلیل تاتولوژی باید سقف مرجع در نظر گرفته شود. فاز سوم از raw pose time-series استفاده کرد و به Macro-F1 حدود ۰٫۵۲۵ رسید. این فاصله نشان می‌دهد فیچرهای سینماتیک مهندسی‌شده در داده کوچک فعلی سیگنال را بهتر فشرده کرده‌اند."),
  h2Fa("۴.۲ پاسخ پیشنهادی به استاد"),
  bulletFa("درخواست CNN انجام شد، اما به شکل علمی درست: 1D-CNN روی keypoint time-series، نه CNN دوبعدی روی فریم خام."),
  bulletFa("نتیجه CNN پایین‌تر از baseline است، ولی علت اصلی کمبود نمونه beginner lane-matched است."),
  bulletFa("برای ادامه پژوهش، ابتدا باید pose هر دو lane برای همه raceها استخراج شود. سپس می‌توان ST-GCN را به عنوان معماری skeleton-based قوی‌تر ارزیابی کرد."),
  h2Fa("۴.۳ جمله آماده برای گزارش"),
  pFa("«نتایج فاز سوم نشان داد که پس از اعمال هم‌ترازی دقیق lane میان برچسب‌ها و داده‌های pose، مجموعه آموزش معتبر به ۱۰۷ نمونه و فقط ۶ نمونه کلاس beginner کاهش یافت. در این شرایط، مدل 1D-CNN سبک نتوانست عملکرد baselineهای مبتنی بر فیچرهای مهندسی‌شده را بازتولید کند. این یافته نشان می‌دهد در داده‌های کوچک و نامتوازن، representation learning خام روی سری زمانی pose به پوشش داده بیشتری نیاز دارد و فیچرهای بیومکانیکی مهندسی‌شده همچنان مزیت عملی دارند.»"),
];

const nextSteps = [
  h1Fa("۵. گام‌های بعدی"),
  tableFa([
    ["اولویت", "اقدام", "دلیل"],
    ["۱", "استخراج pose هر دو lane برای همه raceها", "افزایش minority معتبر و حذف bottleneck اصلی"],
    ["۲", "اجرای مجدد فاز ۳ پس از افزایش coverage", "بررسی اینکه ضعف CNN از کمبود داده بوده یا از معماری"],
    ["۳", "فاز ۴: گزارش مقایسه‌ای", "ترکیب فاز ۲ و ۳، ROC/PR، تحلیل آماری و متن پایان‌نامه"],
    ["۴", "ST-GCN به عنوان کار آینده", "مدل مناسب‌تر برای skeleton و توپولوژی بدن، نیازمند داده بیشتر"],
  ], [1200, 4200, 3960]),
  pFa("فاز چهارم باید این نتیجه را به‌صورت مقایسه‌ای و صادقانه بنویسد: baseline فاز دوم قوی است اما تاتولوژیک؛ CNN فاز سوم مستقل‌تر است اما به‌دلیل داده lane-matched محدود ضعیف‌تر ظاهر شده است. این تضاد، بخش روش‌شناسی پایان‌نامه را قوی‌تر می‌کند."),
];

const doc = new Document({
  creator: "airano",
  title: "Phase 3 Methodology and Results",
  description: "Persian methodology and results document for 1D-CNN pose-time-series phase",
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
      default: new Header({ children: [pFa("تحلیل عملکرد سنگ‌نوردی سرعت، فاز سوم 1D-CNN", {
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
      })] },
      ),
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
      ...dataAudit,
      pagebreak(),
      ...resultsSection,
      pagebreak(),
      ...interpretation,
      pagebreak(),
      ...nextSteps,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT_PATH, buf);
  console.log(`Wrote ${OUT_PATH} (${buf.length} bytes)`);
});

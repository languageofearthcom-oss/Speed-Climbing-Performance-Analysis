# Speed Climbing Performance Analysis

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

**English** | [فارسی](#فارسی)

AI-powered speed climbing performance analysis using computer vision and machine learning. Analyzes athlete technique from video footage and provides personalized coaching feedback.

---

## Features

- **Pose Estimation**: Extract 33 body keypoints using MediaPipe BlazePose (no physical markers needed)
- **Biomechanics Analysis**: Calculate joint angles, body position, coordination metrics
- **Fuzzy Logic Feedback**: Personalized coaching recommendations in English and Persian
- **Camera-Agnostic**: Works with moving cameras (no fixed camera calibration required)
- **Web Interface**: Streamlit-based review dashboard
- **Docker Ready**: Easy deployment with Docker and Coolify

> 📘 **Learn More**: Read our [System Architecture & Workflow](SYSTEM_ARCHITECTURE.md) guide to understand how it works.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/airano-ir/speed-climbing-performance-analysis.git
cd speed-climbing-performance-analysis

# Run with Docker Compose
docker compose up -d

# Access web interface at http://localhost:8501
```

### Option 2: Local Installation

```bash
# Clone repository
git clone https://github.com/airano-ir/speed-climbing-performance-analysis.git
cd speed-climbing-performance-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run web interface
streamlit run scripts/analysis_app/app.py
```

### Sample Files (Included)

Sample files are included in the repository for testing:

- `examples/sample_output/pose_sample.json` - Sample pose input data
- `examples/sample_output/sample_feedback.json` - Sample analysis output

You can use these directly with the web interface without downloading anything.

### Download Additional Data (Optional)

```bash
# Download additional pose data and video examples
python scripts/download_sample_data.py

# Include sample video (larger download)
python scripts/download_sample_data.py --include-video

# Download race segment data (for advanced analysis)
python scripts/download_sample_data.py --download-races

# Or create offline samples without downloading
python scripts/download_sample_data.py --offline
```

## Usage

### Analyze a Video

```python
from speed_climbing.vision.pose import BlazePoseExtractor
from speed_climbing.analysis.feedback.feedback_generator import FeedbackGenerator

# Extract poses from video
extractor = BlazePoseExtractor()
pose_data = extractor.process_video("race_video.mp4")

# Generate feedback
generator = FeedbackGenerator(language="en")  # or "fa" for Persian
report = generator.generate_feedback(
    pose_data=pose_data,
    lane="left",
    include_comparison=True
)

print(report)
```

### Command Line

```bash
# Analyze video and get feedback
python examples/analyze_single_video.py path/to/video.mp4 --language fa --lane left

# Save output to file
python examples/analyze_single_video.py video.mp4 -o report.txt
```

## Project Structure

```
speed_climbing_performance_analysis/
├── speed_climbing/              # Main package
│   ├── vision/                  # Computer vision modules
│   ├── analysis/                # Analysis modules
│   ├── processing/              # Data processing
│   └── core/                    # Core utilities
├── scripts/
│   ├── analysis_app/            # Streamlit web app
│   ├── analyze_video.py         # CLI analysis script
│   └── download_sample_data.py  # Sample data downloader
├── examples/                    # Example scripts
│   └── sample_output/           # Sample pose & feedback files
├── configs/                     # Configuration files
├── Dockerfile                   # Docker configuration
├── docker-compose.yaml          # Docker Compose for Coolify
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation
```

## Deployment with Coolify

This project is configured for easy deployment with [Coolify](https://coolify.io/):

1. Connect your repository in Coolify
2. Select "Docker Compose" as build type
3. Coolify will automatically detect `docker-compose.yaml`
4. Deploy! The web interface will be available on port 8501

See [docker-compose.yaml](docker-compose.yaml) for configuration details.

## Sample Output

```json
{
  "performance_scores": {
    "coordination": {"score": 72.5, "rating": "good"},
    "leg_technique": {"score": 68.0, "rating": "average"},
    "arm_technique": {"score": 75.0, "rating": "good"},
    "body_position": {"score": 70.0, "rating": "good"},
    "reach": {"score": 65.0, "rating": "average"}
  },
  "overall_score": 70.1,
  "recommendations": [
    {
      "priority": "high",
      "category": "leg_technique",
      "recommendation_en": "Practice maintaining consistent knee angles during push-off phases",
      "recommendation_fa": "تمرین حفظ زوایای ثابت زانو در فازهای هل دادن"
    }
  ]
}
```

## API Reference

### BlazePoseExtractor

```python
from speed_climbing.vision.pose import BlazePoseExtractor

extractor = BlazePoseExtractor(
    model_complexity=1,      # 0, 1, or 2 (higher = more accurate)
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Process single frame
result = extractor.process_frame(frame, frame_id, timestamp)

# Process entire video
pose_data = extractor.process_video(video_path)
```

### FeedbackGenerator

```python
from speed_climbing.analysis.feedback.feedback_generator import FeedbackGenerator

generator = FeedbackGenerator(
    language="en"  # "en" or "fa"
)

report = generator.generate_feedback(
    pose_data=pose_data,
    lane="left",           # "left" or "right"
    include_comparison=True
)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Google MediaPipe Team
- IFSC Research Committee
- OpenCV Contributors

---

# فارسی

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

[English](#speed-climbing-performance-analysis) | **فارسی**

سیستم هوشمند تحلیل عملکرد صعود سرعتی با استفاده از بینایی کامپیوتری و یادگیری ماشین. تحلیل تکنیک ورزشکار از ویدئو و ارائه بازخورد شخصی‌سازی شده.

---

## ویژگی‌ها

- **تشخیص پوز**: استخراج 33 نقطه کلیدی بدن با MediaPipe BlazePose (بدون نیاز به مارکر فیزیکی)
- **تحلیل بیومکانیک**: محاسبه زوایای مفصل، وضعیت بدن، معیارهای هماهنگی
- **بازخورد منطق فازی**: توصیه‌های مربیگری شخصی‌سازی شده به فارسی و انگلیسی
- **مستقل از دوربین**: کار با دوربین‌های متحرک (بدون نیاز به کالیبراسیون دوربین ثابت)
- **رابط وب**: داشبورد بررسی مبتنی بر Streamlit
- **آماده Docker**: استقرار آسان با Docker و Coolify

> 📘 **بیشتر بدانید**: برای درک نحوه کارکرد سیستم، راهنمای [معماری سیستم و جریان کار](SYSTEM_ARCHITECTURE.md) را مطالعه کنید.

## شروع سریع

### روش 1: Docker (پیشنهادی)

```bash
# کلون مخزن
git clone https://github.com/airano-ir/speed-climbing-performance-analysis.git
cd speed-climbing-performance-analysis

# اجرا با Docker Compose
docker compose up -d

# دسترسی به رابط وب در http://localhost:8501
```

### روش 2: نصب محلی

```bash
# کلون مخزن
git clone https://github.com/airano-ir/speed-climbing-performance-analysis.git
cd speed-climbing-performance-analysis

# ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای رابط وب
streamlit run scripts/analysis_app/app.py
```

### فایل‌های نمونه (شامل شده)

فایل‌های نمونه برای تست در مخزن موجود هستند:

- `examples/sample_output/pose_sample.json` - داده پوز نمونه
- `examples/sample_output/sample_feedback.json` - خروجی تحلیل نمونه

می‌توانید این فایل‌ها را مستقیماً در رابط وب استفاده کنید.

### دانلود داده‌های اضافی (اختیاری)

```bash
# دانلود داده‌های پوز و ویدئوهای نمونه اضافی
python scripts/download_sample_data.py

# شامل ویدئوی نمونه (دانلود بزرگ‌تر)
python scripts/download_sample_data.py --include-video

# دانلود داده‌های race segments (برای تحلیل پیشرفته)
python scripts/download_sample_data.py --download-races

# ایجاد نمونه‌های آفلاین بدون دانلود
python scripts/download_sample_data.py --offline
```

## استفاده

### تحلیل یک ویدئو

```python
from speed_climbing.vision.pose import BlazePoseExtractor
from speed_climbing.analysis.feedback.feedback_generator import FeedbackGenerator

# استخراج پوز از ویدئو
extractor = BlazePoseExtractor()
pose_data = extractor.process_video("race_video.mp4")

# تولید بازخورد
generator = FeedbackGenerator(language="fa")  # یا "en" برای انگلیسی
report = generator.generate_feedback(
    pose_data=pose_data,
    lane="left",
    include_comparison=True
)

print(report)
```

### خط فرمان

```bash
# تحلیل ویدئو و دریافت بازخورد
python examples/analyze_single_video.py path/to/video.mp4 --language fa --lane left

# ذخیره خروجی در فایل
python examples/analyze_single_video.py video.mp4 -o report.txt
```

## ساختار پروژه

```
speed_climbing_performance_analysis/
├── speed_climbing/              # پکیج اصلی
│   ├── vision/                  # ماژول‌های بینایی کامپیوتری
│   ├── analysis/                # ماژول‌های تحلیل
│   ├── processing/              # پردازش داده
│   └── core/                    # ابزارهای پایه
├── scripts/
│   ├── analysis_app/            # برنامه وب Streamlit
│   ├── analyze_video.py         # اسکریپت تحلیل خط فرمان
│   └── download_sample_data.py  # دانلودکننده داده نمونه
├── examples/                    # اسکریپت‌های نمونه
│   └── sample_output/           # فایل‌های نمونه پوز و بازخورد
├── configs/                     # فایل‌های پیکربندی
├── Dockerfile                   # پیکربندی Docker
├── docker-compose.yaml          # Docker Compose برای Coolify
├── requirements.txt             # وابستگی‌های Python
└── README.md                    # مستندات
```

## استقرار با Coolify

این پروژه برای استقرار آسان با [Coolify](https://coolify.io/) پیکربندی شده است:

1. مخزن خود را در Coolify متصل کنید
2. "Docker Compose" را به عنوان نوع ساخت انتخاب کنید
3. Coolify به طور خودکار `docker-compose.yaml` را تشخیص می‌دهد
4. استقرار! رابط وب در پورت 8501 در دسترس خواهد بود

برای جزئیات پیکربندی، [docker-compose.yaml](docker-compose.yaml) را ببینید.

## نمونه خروجی

```json
{
  "performance_scores": {
    "coordination": {"score": 72.5, "rating": "خوب"},
    "leg_technique": {"score": 68.0, "rating": "متوسط"},
    "arm_technique": {"score": 75.0, "rating": "خوب"},
    "body_position": {"score": 70.0, "rating": "خوب"},
    "reach": {"score": 65.0, "rating": "متوسط"}
  },
  "overall_score": 70.1,
  "recommendations": [
    {
      "priority": "بالا",
      "category": "تکنیک پا",
      "recommendation_fa": "تمرین حفظ زوایای ثابت زانو در فازهای هل دادن"
    }
  ]
}
```

## مشارکت

از مشارکت شما استقبال می‌کنیم! لطفاً [CONTRIBUTING.md](CONTRIBUTING.md) را برای راهنما ببینید.

## مجوز

این پروژه تحت مجوز MIT منتشر شده است - برای جزئیات [LICENSE](LICENSE) را ببینید.

## قدردانی

- تیم Google MediaPipe
- کمیته تحقیقات IFSC
- مشارکت‌کنندگان OpenCV

---

**Made with care for the climbing community / ساخته شده با عشق برای جامعه کوهنوردی**

# Changelog
# تاریخچه تغییرات

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[English](#english) | [فارسی](#فارسی)

---

## English

## [1.0.0] - 2025-11-29

### Added

- **Fuzzy Logic Feedback System** - Personalized coaching feedback using fuzzy logic
  - 5 performance categories: Coordination, Leg Technique, Arm Technique, Body Position, Reach
  - Comparison with professional athlete baselines (371 samples)
  - Bilingual output (English/Persian)

- **Pose Extraction Pipeline**
  - BlazePose integration for 33 body keypoints
  - Dual-lane detection for competition videos
  - Quality validation and filtering

- **Feature Extraction System**
  - 22 ML-ready features
  - Automatic race segment detection
  - Camera-independent metrics (angles, ratios, sync)

- **Web Interface (Streamlit)**
  - Manual review interface for race detection
  - Video library browser
  - Bulk operations support
  - Bilingual UI

- **Docker Support**
  - Multi-stage Dockerfile
  - docker-compose for Coolify deployment
  - Health checks and production-ready configuration

### Technical Details

- Python 3.11+ support
- MediaPipe for pose estimation
- scikit-fuzzy for fuzzy logic
- Streamlit for web interface

---

## فارسی

## [1.0.0] - 1403/09/09

### اضافه شده

- **سیستم بازخورد منطق فازی** - بازخورد مربیگری شخصی‌سازی شده با منطق فازی
  - 5 دسته عملکرد: هماهنگی، تکنیک پا، تکنیک دست، وضعیت بدن، دسترسی
  - مقایسه با خط پایه ورزشکاران حرفه‌ای (371 نمونه)
  - خروجی دوزبانه (انگلیسی/فارسی)

- **خط لوله استخراج حالت بدن**
  - یکپارچه‌سازی BlazePose برای 33 نقطه کلیدی بدن
  - تشخیص دو خط برای ویدیوهای مسابقه
  - اعتبارسنجی و فیلتر کیفیت

- **سیستم استخراج ویژگی**
  - 22 ویژگی آماده ML
  - تشخیص خودکار بخش مسابقه
  - معیارهای مستقل از دوربین (زوایا، نسبت‌ها، همگام‌سازی)

- **رابط وب (Streamlit)**
  - رابط بررسی دستی برای تشخیص مسابقه
  - مرورگر کتابخانه ویدیو
  - پشتیبانی از عملیات دسته‌ای
  - رابط کاربری دوزبانه

- **پشتیبانی Docker**
  - Dockerfile چند مرحله‌ای
  - docker-compose برای deployment در Coolify
  - health check و پیکربندی آماده تولید

### جزئیات فنی

- پشتیبانی از Python 3.11+
- MediaPipe برای تخمین حالت بدن
- scikit-fuzzy برای منطق فازی
- Streamlit برای رابط وب

---

## [Unreleased]

### Planned (Phase 5-10)

- Enhanced visualization with keypoint overlays
- Single athlete detection improvement
- Label collection tool
- ML model training for time prediction
- Advanced position tracking

---

Made with ❤️ by Airano | ساخته شده با ❤️ توسط آیرانو

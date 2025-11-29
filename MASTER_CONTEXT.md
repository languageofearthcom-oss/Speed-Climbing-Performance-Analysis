# MASTER CONTEXT: Speed Climbing Performance Analysis

## Project Overview
**Goal**: Build an AI-powered system that analyzes speed climbing videos and provides **personalized feedback** to athletes, coaches, and enthusiasts.

**Current Status**: **Phase 6 Complete** → Phase 7 In Progress

---

## 🔗 Repository Information

### GitHub (Public Release)
- **URL**: https://github.com/airano-ir/speed-climbing-performance-analysis
- **Branch**: `main` (production-ready, clean)
- **Excludes**: MASTER_CONTEXT.md, development docs, notebooks

### Gitea (Internal Development)
- **URL**: https://gitea.airano.ir/dev/Speed-Climbing-Performance-Analysis
- **Branches**:
  - `main`: Same as GitHub release
  - `development`: Includes MASTER_CONTEXT.md for future phase planning

### Docker Deployment (Coolify-Ready)
```bash
# Local development
docker compose up -d
# Access: http://localhost:8501

# Coolify deployment
# 1. Connect repository in Coolify
# 2. Select "Docker Compose" as build type
# 3. Deploy! (port 8501)
```

---

## 🏗️ Project Journey

### Phase 1: Data Collection ✅
- Downloaded videos from IFSC competitions
- Cut videos into individual race clips
- 96+ videos from 5 competitions

### Phase 2: Pose Extraction ✅
- BlazePose for 33 body keypoints
- Dual-lane detection (left/right athletes)
- JSON storage for each video

### Phase 3: Feature Extraction ✅
- 22 ML-ready features extracted
- Automatic race segment detection
- Quality reports and validation

### Phase 4: Fuzzy Feedback System ✅
- Fuzzy Logic engine for interpretable analysis
- Personalized feedback in Persian/English
- Comparison with professional athletes
- **Camera-independent features only** (angles, ratios, sync)

### Phase 4.5: Production Release ✅ (2025-11-29)
- Docker/Coolify deployment ready
- GitHub clean release
- Bilingual documentation (EN/FA)
- Example scripts and sample data downloader

---

## 🗺️ Future Roadmap

### Phase 5: Web Interface ✅ (COMPLETE)
**Goal**: Create a user-facing web app for video analysis feedback

**Completed Features:**
- ✅ Upload Page: Video and pose file upload
- ✅ Analysis Progress: Real-time progress bar during processing
- ✅ Results Display: Scores, ratings, recommendations with Plotly charts
- ✅ Charts & Graphs: Gauge chart, radar chart, category bars
- ✅ Export Report: TXT, HTML (for PDF), JSON formats
- ✅ Bilingual: Full Persian/English support

**App Location:** `scripts/analysis_app/app.py`

### Phase 6: Enhanced Visualization ✅ (COMPLETE)
**Goal**: Add visual feedback overlaid on video

| Task | Status | Description |
|------|--------|-------------|
| Keypoint Overlay | ✅ | Draw skeleton on video frames |
| Angle Indicators | ✅ | Show joint angles on video |
| Race Segment Display | ✅ | Show start/end frame markers with activity chart |
| Score Timeline | ✅ | Graph of joint angles over time with race segment highlight |
| Comparison View | 📋 | Side-by-side with reference athlete |

### Phase 7: Single Athlete Detection 📋 (IN PROGRESS)
**Goal**: Fix detection for single-athlete videos

| Task | Status | Description |
|------|--------|-------------|
| Athlete Count Detection | ✅ | Auto-detect 1 or 2 athletes based on detection rates |
| Lane Selection | ✅ | Smart lane selection with auto/manual options |
| Detection Quality Display | ✅ | Show detection rates per lane with icons |
| Better Lane Assignment | 📋 | Improve left/right detection logic |

### Phase 8: Label Collection 📋
**Goal**: Collect labels for ML training

| Task | Priority | Description |
|------|----------|-------------|
| Time Annotation Tool | High | Mark start/finish for actual time |
| Skill Level Labels | Medium | Expert annotation of skill |
| Competition Results | Medium | Import win/lose data |
| Reference Technique | Low | Mark "good" vs "bad" examples |

### Phase 9: ML Model Training 📋
**Goal**: Train supervised ML models

| Task | Priority | Description |
|------|----------|-------------|
| Time Prediction | High | Predict finish time from technique |
| Skill Classification | Medium | Classify beginner/intermediate/advanced |
| Technique Clustering | Medium | Find similar climbing styles |
| Anomaly Detection | Low | Detect unusual movements |
| **Google Colab Notebook** | High | Create notebook for easy model training and inference |

### Phase 10: Advanced Position Tracking 📋
**Goal**: Solve camera-motion problem for absolute positioning

| Task | Priority | Description |
|------|----------|-------------|
| Wall Detection | High | Detect climbing wall in frame |
| Hold Tracking | High | Track holds despite occlusion |
| Camera Motion Estimation | High | Estimate camera pan/tilt/zoom |
| Absolute COM Position | Medium | Real position on wall |
| Actual Climbing Speed | Medium | Meters per second |
| Distance Traveled | Low | Total path length |

---

## 📦 Architecture

### `speed_climbing` Package
```
speed_climbing/
├── core/
│   └── settings.py           # IFSC standards, config
├── vision/
│   ├── holds.py              # HoldDetector
│   ├── lanes.py              # DualLaneDetector
│   ├── pose.py               # BlazePoseExtractor
│   └── calibration.py        # CameraCalibrator
├── processing/
│   ├── athlete_centric.py    # Main pipeline
│   └── dropout.py            # Dropout handling
└── analysis/
    ├── features/             # Feature extraction
    │   ├── frequency.py      # FFT-based rhythm
    │   ├── efficiency.py     # Path efficiency (⚠️ camera-dependent)
    │   ├── posture.py        # Joint angles
    │   └── extractor.py      # Main extractor
    └── feedback/             # Fuzzy feedback
        ├── baseline.py       # Pro athlete stats
        ├── fuzzy_engine.py   # Fuzzy logic
        └── feedback_generator.py  # Report generation
```

### Scripts
```
scripts/
├── review_interface/         # OLD - needs redesign in Phase 5
│   ├── app.py               # Streamlit main app
│   └── ...                  # Various modules
├── download_sample_data.py  # Sample data downloader
└── batch/                   # Batch processing scripts
```

---

## 🎯 Current Feedback System

### Valid Features (Camera-Independent)
```
✅ Used in Fuzzy System:
├── Joint Angles
│   ├── post_avg_knee_angle
│   ├── post_knee_angle_std
│   ├── post_avg_elbow_angle
│   └── post_elbow_angle_std
├── Body Position
│   ├── post_avg_body_lean
│   ├── post_body_lean_std
│   └── post_hip_width_ratio
├── Reach
│   ├── post_avg_reach_ratio
│   └── post_max_reach_ratio
└── Coordination
    ├── freq_limb_sync_ratio
    ├── freq_hand_movement_amplitude
    └── freq_foot_movement_amplitude
```

### Invalid Features (Camera Artifacts)
```
❌ NOT used (camera follows athlete):
├── eff_path_straightness
├── eff_com_stability_index
├── eff_lateral_movement_ratio
├── eff_movement_smoothness
├── eff_vertical_progress_rate
└── eff_acceleration_variance
```

### Performance Categories (5)
| Category | Persian | Features |
|----------|---------|----------|
| Coordination | هماهنگی اندام‌ها | limb_sync, amplitudes |
| Leg Technique | تکنیک پا | knee angles |
| Arm Technique | تکنیک دست | elbow angles |
| Body Position | وضعیت بدن | body lean, hip ratio |
| Reach | دسترسی و کشش | reach ratios |

---

## ⚠️ Known Issues

### Single Athlete Videos
- System always detects 2 lanes (left/right)
- For single-athlete videos, one lane may have invalid data
- **Workaround**: Use `--lane left` or `--lane right` flag

### Camera Motion
- Cannot measure actual climbing speed
- Cannot measure absolute position on wall
- **Requires**: Wall detection + camera motion compensation (Phase 10)

### Review Interface (OLD)
- Located at `scripts/review_interface/`
- Designed for internal race detection review
- **Needs redesign** for user-facing analysis display
- Currently NOT connected to FeedbackGenerator

---

## 🚀 Usage

### Command Line
```bash
# Analyze a video and get feedback
python examples/analyze_single_video.py video.mp4 --language fa --lane left

# Options:
#   --language fa|en    Output language
#   --lane left|right   Which lane to analyze
#   --output file.txt   Save report to file
```

### Python API
```python
from speed_climbing.vision.pose import BlazePoseExtractor
from speed_climbing.analysis.feedback.feedback_generator import FeedbackGenerator

# Extract poses
extractor = BlazePoseExtractor()
pose_data = extractor.process_video("video.mp4")

# Generate feedback
generator = FeedbackGenerator(language="fa")
report = generator.generate_feedback(pose_data, lane="left")
print(report)
```

### Docker
```bash
# Run web interface
docker compose up -d
# Access at http://localhost:8501
```

---

## 📊 Data Available

- **371 samples** from 5 competitions
- **246 high-quality** samples (extraction quality >= 0.8)
- **Pose files**: `data/processed/poses/samples/*.json`
- **ML dataset**: `data/ml_dataset/`

---

## 📝 Recent Updates

### 2025-11-29 (Latest - Phase 7 Progress)
- **Athlete Count Detection**: Auto-detect 1 or 2 athletes ✅
- **Smart Lane Selection**: Auto-select best lane or manual override ✅
- **Detection Quality Display**: Show detection rates with icons ✅
- **New Module**: `speed_climbing/vision/athlete_detector.py`

### 2025-11-29 (Phase 6 Complete)
- **Skeleton Overlay**: Draw skeleton on video frames with keypoints ✅
- **Joint Angles**: Show knee/elbow angles with arcs and labels ✅
- **Race Segment Display**: Activity chart with start/end markers ✅
- **Score Timeline**: Graph of joint angles over time ✅

### 2025-11-29 (Phase 5 Complete)
- **Web Interface**: Full analysis functionality with Streamlit
- **Export Formats**: TXT, HTML (for PDF), JSON
- **Bilingual UI**: Full Persian/English support in web app
- **Charts**: Plotly gauge, radar, and bar charts

### 2025-11-29 (Production Release)
- **Camera-Independent Features**: Removed 6 invalid efficiency features
- **New Categories**: 5 technique-focused categories
- **Limitation Note**: Added note about camera motion in reports
- **Tested**: Confirmed working with Ola Miroslaw video

### 2025-11-28
- **Fuzzy Feedback System**: Complete implementation
- **Baseline Statistics**: From 371 professional races
- **Bilingual Output**: Persian/English support

---

## 🔧 Development Notes

### Next Session TODO (Phase 6/7)
1. ~~Add angle indicators on video overlay~~ ✅ Done
2. ~~Add race segment display~~ ✅ Done
3. ~~Add score timeline graph~~ ✅ Done
4. Consider comparison view feature (optional)
5. Phase 7: Auto-detect single/dual athlete videos

### Key Files for Phase 6
- `scripts/analysis_app/app.py` - Main web interface with skeleton overlay
- `speed_climbing/vision/pose.py` - BlazePoseExtractor with draw_landmarks()
- `speed_climbing/analysis/features/posture.py` - Angle calculations

### Dependencies
- `streamlit` - Web interface
- `mediapipe` - Pose extraction
- `scikit-fuzzy` - Fuzzy logic
- `plotly` - Interactive charts
- `opencv-python` - Video processing

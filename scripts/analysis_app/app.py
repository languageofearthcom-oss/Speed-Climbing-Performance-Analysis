"""
Speed Climbing Performance Analysis - Web Interface
===================================================

User-facing web app for analyzing speed climbing videos and getting feedback.

Features:
- Upload video or pose JSON file
- Automatic pose extraction and analysis
- Personalized feedback in Persian/English
- Visual score charts
- Export reports

Usage:
    streamlit run scripts/analysis_app/app.py

Version: 1.0 (Phase 5)
Date: 2025-11-29
"""

import streamlit as st
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from speed_climbing.analysis.feedback.feedback_generator import FeedbackGenerator, Language, Feedback
from speed_climbing.analysis.features.extractor import FeatureExtractor


# =============================================================================
# TRANSLATIONS
# =============================================================================

TRANSLATIONS = {
    'en': {
        'page_title': 'Speed Climbing Analysis',
        'page_icon': '🧗',
        'header': 'Speed Climbing Performance Analysis',
        'subheader': 'Get personalized feedback on your climbing technique',
        'upload_section': '📤 Upload Your Data',
        'upload_video': 'Upload Video (MP4, MOV, AVI)',
        'upload_pose': 'Upload Pose File (JSON)',
        'or_text': '— OR —',
        'use_sample': '📂 Use Sample Data',
        'select_lane': 'Select Lane',
        'left_lane': 'Left Lane',
        'right_lane': 'Right Lane',
        'analyze_button': '🔍 Analyze Performance',
        'analyzing': 'Analyzing your performance...',
        'results_header': '📊 Analysis Results',
        'overall_score': 'Overall Score',
        'level': 'Level',
        'strengths': '💪 Strengths',
        'improvements': '⚠️ Areas for Improvement',
        'recommendations': '🎯 Training Recommendations',
        'category_scores': '📈 Category Scores',
        'comparison': '📊 Professional Comparison',
        'export_report': '📥 Export Report',
        'language_selector': 'Language / زبان',
        'no_file': 'Please upload a video or pose file to analyze',
        'processing_video': 'Processing video... This may take a few minutes.',
        'error_processing': 'Error processing file',
        'note_camera': 'Note: Analysis is based on body angles and coordination. Actual speed cannot be measured due to camera motion.',
        'coordination': 'Coordination',
        'leg_technique': 'Leg Technique',
        'arm_technique': 'Arm Technique',
        'body_position': 'Body Position',
        'reach': 'Reach',
        'high_priority': 'High Priority',
        'medium_priority': 'Medium Priority',
        'training_tips': '📝 Training Tips',
        'about': 'About',
        'about_text': 'This tool analyzes speed climbing technique using AI-powered pose estimation and fuzzy logic.',
        'github_link': 'View on GitHub',
    },
    'fa': {
        'page_title': 'تحلیل سنگنوردی سرعتی',
        'page_icon': '🧗',
        'header': 'تحلیل عملکرد سنگنوردی سرعتی',
        'subheader': 'بازخورد شخصی‌سازی شده برای تکنیک صعود شما',
        'upload_section': '📤 آپلود داده',
        'upload_video': 'آپلود ویدئو (MP4, MOV, AVI)',
        'upload_pose': 'آپلود فایل پوز (JSON)',
        'or_text': '— یا —',
        'use_sample': '📂 استفاده از داده نمونه',
        'select_lane': 'انتخاب مسیر',
        'left_lane': 'مسیر چپ',
        'right_lane': 'مسیر راست',
        'analyze_button': '🔍 تحلیل عملکرد',
        'analyzing': 'در حال تحلیل عملکرد شما...',
        'results_header': '📊 نتایج تحلیل',
        'overall_score': 'امتیاز کلی',
        'level': 'سطح',
        'strengths': '💪 نقاط قوت',
        'improvements': '⚠️ فرصت‌های بهبود',
        'recommendations': '🎯 توصیه‌های تمرینی',
        'category_scores': '📈 امتیاز دسته‌ها',
        'comparison': '📊 مقایسه با حرفه‌ای‌ها',
        'export_report': '📥 دریافت گزارش',
        'language_selector': 'Language / زبان',
        'no_file': 'لطفاً یک ویدئو یا فایل پوز برای تحلیل آپلود کنید',
        'processing_video': 'در حال پردازش ویدئو... این ممکن است چند دقیقه طول بکشد.',
        'error_processing': 'خطا در پردازش فایل',
        'note_camera': 'توجه: این تحلیل بر اساس زوایای بدن و هماهنگی است. سرعت واقعی صعود به دلیل حرکت دوربین قابل اندازه‌گیری نیست.',
        'coordination': 'هماهنگی اندام‌ها',
        'leg_technique': 'تکنیک پا',
        'arm_technique': 'تکنیک دست',
        'body_position': 'وضعیت بدن',
        'reach': 'دسترسی و کشش',
        'high_priority': 'اولویت بالا',
        'medium_priority': 'اولویت متوسط',
        'training_tips': '📝 نکات تمرینی',
        'about': 'درباره',
        'about_text': 'این ابزار تکنیک سنگنوردی سرعتی را با استفاده از تخمین پوز هوشمند و منطق فازی تحلیل می‌کند.',
        'github_link': 'مشاهده در GitHub',
    }
}


def get_text(key: str, lang: str = 'en') -> str:
    """Get translated text."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Speed Climbing Analysis",
    page_icon="🧗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE
# =============================================================================

if 'language' not in st.session_state:
    st.session_state['language'] = 'en'

if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # Language selector
    st.markdown("### " + get_text('language_selector', st.session_state['language']))
    selected_lang = st.selectbox(
        "Language",
        options=['en', 'fa'],
        format_func=lambda x: '🇬🇧 English' if x == 'en' else '🇮🇷 فارسی',
        key='language_selector',
        label_visibility='collapsed'
    )
    if selected_lang != st.session_state['language']:
        st.session_state['language'] = selected_lang
        st.session_state['analysis_result'] = None
        st.rerun()

    st.markdown("---")

    # About section
    st.markdown(f"### {get_text('about', st.session_state['language'])}")
    st.markdown(get_text('about_text', st.session_state['language']))

    st.markdown("---")

    # GitHub link
    st.markdown(
        f"[🔗 {get_text('github_link', st.session_state['language'])}]"
        "(https://github.com/airano-ir/speed-climbing-performance-analysis)"
    )


# =============================================================================
# MAIN CONTENT
# =============================================================================

lang = st.session_state['language']

# Header
st.title(get_text('header', lang))
st.markdown(f"**{get_text('subheader', lang)}**")
st.markdown("---")


# =============================================================================
# FILE UPLOAD
# =============================================================================

st.subheader(get_text('upload_section', lang))

col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    # Video upload
    uploaded_video = st.file_uploader(
        get_text('upload_video', lang),
        type=['mp4', 'mov', 'avi', 'mkv'],
        key='video_uploader'
    )

with col2:
    st.markdown(f"<div style='text-align: center; padding-top: 30px;'>{get_text('or_text', lang)}</div>",
                unsafe_allow_html=True)

with col3:
    # Pose JSON upload
    uploaded_pose = st.file_uploader(
        get_text('upload_pose', lang),
        type=['json'],
        key='pose_uploader'
    )

# Lane selection
st.markdown("")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    lane = st.radio(
        get_text('select_lane', lang),
        options=['left', 'right'],
        format_func=lambda x: get_text('left_lane' if x == 'left' else 'right_lane', lang),
        horizontal=True
    )

st.markdown("---")


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def load_pose_data(file_content: str) -> Optional[Dict]:
    """Load pose data from JSON content."""
    try:
        data = json.loads(file_content)

        # Validate that this is a pose file, not a feedback/output file
        if 'frames' not in data:
            st.error("Invalid file format: This doesn't appear to be a pose file. "
                     "Pose files must contain 'frames' with keypoint data.")
            if 'performance_scores' in data or 'overall_score' in data:
                st.info("This looks like an analysis output file, not a pose input file. "
                        "Please upload the original pose JSON file (from data/processed/poses/).")
            return None

        if 'metadata' not in data:
            st.warning("Pose file is missing metadata. Using defaults.")
            data['metadata'] = {'fps': 30.0, 'detection_rate_left': 1.0, 'detection_rate_right': 1.0}

        return data
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON file: {e}")
        return None


def process_video_to_poses(video_path: str, progress_bar=None) -> Optional[Dict]:
    """
    Process video and extract poses frame by frame.

    Returns pose data in the format expected by FeatureExtractor.
    """
    import cv2
    from speed_climbing.vision.pose import BlazePoseExtractor

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    extractor = BlazePoseExtractor()
    frames = []
    detection_count = 0

    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_id / fps if fps > 0 else 0
        pose_result = extractor.process_frame(frame, frame_id, timestamp)

        # Build frame data in expected format
        # For single video, we put the athlete in "left" lane
        frame_data = {
            'frame_id': frame_id,
            'timestamp': timestamp,
            'left_climber': None,
            'right_climber': None
        }

        if pose_result.has_detection:
            detection_count += 1
            climber_data = {
                'has_detection': True,
                'overall_confidence': pose_result.overall_confidence,
                'keypoints': {name: kp.to_dict() for name, kp in pose_result.keypoints.items()}
            }
            # Put in left lane by default (user can select)
            frame_data['left_climber'] = climber_data

        frames.append(frame_data)
        frame_id += 1

        # Update progress
        if progress_bar and total_frames > 0:
            progress_bar.progress(frame_id / total_frames)

    cap.release()
    extractor.release()

    detection_rate = detection_count / total_frames if total_frames > 0 else 0

    pose_data = {
        'metadata': {
            'fps': fps,
            'total_frames': total_frames,
            'width': width,
            'height': height,
            'detection_rate_left': detection_rate,
            'detection_rate_right': 0.0  # No right lane for single video
        },
        'frames': frames
    }

    return pose_data


def extract_features_from_poses(pose_data: Dict, lane: str) -> Optional[Dict[str, float]]:
    """Extract features from pose data."""
    try:
        extractor = FeatureExtractor()
        # extract_from_data returns a list of FeatureResult (one per lane)
        results = extractor.extract_from_data(pose_data)

        # Find the result for the requested lane
        for result in results:
            if result.lane == lane:
                # Convert to flat dict for FeedbackGenerator
                return result.to_flat_dict()

        # If requested lane not found, try the other lane or first available
        if results:
            st.warning(f"Lane '{lane}' not found. Using '{results[0].lane}' instead.")
            return results[0].to_flat_dict()

        st.error("No valid lane data found in the pose file.")
        return None
    except Exception as e:
        import traceback
        st.error(f"Feature extraction error: {e}")
        st.code(traceback.format_exc())
        return None


def run_analysis(features: Dict[str, float], language: str) -> Optional[Feedback]:
    """Run analysis and generate feedback."""
    try:
        lang_enum = Language.PERSIAN if language == 'fa' else Language.ENGLISH
        generator = FeedbackGenerator(language=lang_enum)
        feedback = generator.generate(features)
        return feedback
    except Exception as e:
        import traceback
        st.error(f"Analysis error: {e}")
        st.code(traceback.format_exc())
        return None


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_score_gauge(score: float, title: str) -> go.Figure:
    """Create a gauge chart for overall score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ff6b6b'},
                {'range': [40, 60], 'color': '#feca57'},
                {'range': [60, 80], 'color': '#48dbfb'},
                {'range': [80, 100], 'color': '#1dd1a1'},
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_category_radar(category_scores: Dict[str, float], lang: str) -> go.Figure:
    """Create a radar chart for category scores."""
    # Map category names
    category_names = {
        'coordination': get_text('coordination', lang),
        'leg_technique': get_text('leg_technique', lang),
        'arm_technique': get_text('arm_technique', lang),
        'body_position': get_text('body_position', lang),
        'reach': get_text('reach', lang),
    }

    categories = list(category_scores.keys())
    values = list(category_scores.values())

    # Translate category names
    labels = [category_names.get(cat, cat) for cat in categories]

    # Close the radar chart
    labels.append(labels[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill='toself',
        name='Score',
        line_color='#3498db',
        fillcolor='rgba(52, 152, 219, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=350,
        margin=dict(l=60, r=60, t=40, b=40)
    )

    return fig


def create_category_bars(category_details: Dict, lang: str) -> go.Figure:
    """Create a horizontal bar chart for categories."""
    category_names = {
        'coordination': get_text('coordination', lang),
        'leg_technique': get_text('leg_technique', lang),
        'arm_technique': get_text('arm_technique', lang),
        'body_position': get_text('body_position', lang),
        'reach': get_text('reach', lang),
    }

    names = []
    scores = []
    colors = []

    for cat_key, details in category_details.items():
        names.append(category_names.get(cat_key, details['name']))
        scores.append(details['score'])

        # Color based on score
        if details['score'] >= 70:
            colors.append('#1dd1a1')
        elif details['score'] >= 50:
            colors.append('#feca57')
        else:
            colors.append('#ff6b6b')

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition='inside'
    ))

    fig.update_layout(
        xaxis_title="Score",
        yaxis_title="",
        xaxis=dict(range=[0, 100]),
        height=300,
        margin=dict(l=20, r=20, t=20, b=40)
    )

    return fig


# =============================================================================
# ANALYSIS BUTTON AND RESULTS
# =============================================================================

# Analyze button
if st.button(get_text('analyze_button', lang), type="primary", use_container_width=True):

    if uploaded_pose:
        # Use uploaded pose file
        with st.spinner(get_text('analyzing', lang)):
            pose_content = uploaded_pose.read().decode('utf-8')
            pose_data = load_pose_data(pose_content)

            if pose_data:
                features = extract_features_from_poses(pose_data, lane)
                if features:
                    feedback = run_analysis(features, lang)
                    if feedback:
                        st.session_state['analysis_result'] = feedback
            else:
                st.error(get_text('error_processing', lang))

    elif uploaded_video:
        # Process video (requires pose extraction)
        st.info(get_text('processing_video', lang))

        try:
            # Save video to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(uploaded_video.read())
                tmp_path = tmp.name

            # Create progress bar
            progress_bar = st.progress(0, text="Extracting poses...")

            # Process video frame by frame
            pose_data = process_video_to_poses(tmp_path, progress_bar)

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

            if pose_data:
                progress_bar.progress(100, text="Analyzing features...")

                # For uploaded videos, always use 'left' lane (single athlete)
                features = extract_features_from_poses(pose_data, 'left')
                if features:
                    feedback = run_analysis(features, lang)
                    if feedback:
                        st.session_state['analysis_result'] = feedback
                        progress_bar.empty()
                    else:
                        progress_bar.empty()
                        st.error("Failed to generate feedback")
                else:
                    progress_bar.empty()
                    st.error("Failed to extract features from poses")
            else:
                progress_bar.empty()
                st.error("Failed to process video")

        except Exception as e:
            st.error(f"{get_text('error_processing', lang)}: {e}")

    else:
        st.warning(get_text('no_file', lang))


# =============================================================================
# DISPLAY RESULTS
# =============================================================================

if st.session_state['analysis_result']:
    feedback = st.session_state['analysis_result']

    st.markdown("---")
    st.header(get_text('results_header', lang))

    # Overall score
    col1, col2 = st.columns([1, 2])

    with col1:
        if PLOTLY_AVAILABLE:
            gauge = create_score_gauge(
                feedback.overall_score,
                get_text('overall_score', lang)
            )
            st.plotly_chart(gauge, use_container_width=True)
        else:
            st.metric(
                get_text('overall_score', lang),
                f"{feedback.overall_score:.0f}/100"
            )

        st.markdown(f"**{get_text('level', lang)}**: {feedback.overall_level}")

    with col2:
        st.markdown(f"### {get_text('category_scores', lang)}")
        if PLOTLY_AVAILABLE:
            radar = create_category_radar(feedback.category_scores, lang)
            st.plotly_chart(radar, use_container_width=True)
        else:
            bars = create_category_bars(feedback.category_details, lang)
            st.plotly_chart(bars, use_container_width=True) if PLOTLY_AVAILABLE else None

            for cat, score in feedback.category_scores.items():
                st.progress(score / 100, text=f"{cat}: {score:.0f}")

    st.markdown("---")

    # Strengths and Improvements
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(get_text('strengths', lang))
        for s in feedback.strengths:
            st.success(f"✓ {s['text']}")

    with col2:
        st.subheader(get_text('improvements', lang))
        for imp in feedback.improvements:
            priority_text = get_text('high_priority' if imp.get('priority') == 'high' else 'medium_priority', lang)
            if imp.get('priority') == 'high':
                st.error(f"🔴 {imp['text']} ({priority_text})")
            else:
                st.warning(f"🟡 {imp['text']} ({priority_text})")

    st.markdown("---")

    # Recommendations
    st.subheader(get_text('recommendations', lang))
    for i, rec in enumerate(feedback.recommendations, 1):
        st.info(f"{i}. {rec['action']}")

    # Training Tips
    if feedback.training_tips:
        st.subheader(get_text('training_tips', lang))
        for tip in feedback.training_tips:
            st.markdown(f"• {tip}")

    st.markdown("---")

    # Comparison
    st.subheader(get_text('comparison', lang))
    st.markdown(feedback.comparison_text)

    # Note about camera limitations
    st.caption(get_text('note_camera', lang))

    st.markdown("---")

    # Export Report
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Generate text report
        lang_enum = Language.PERSIAN if lang == 'fa' else Language.ENGLISH
        generator = FeedbackGenerator(language=lang_enum)
        report_text = generator.format_report(feedback)

        st.download_button(
            label=get_text('export_report', lang),
            data=report_text.encode('utf-8'),
            file_name=f"climbing_analysis_report_{lang}.txt",
            mime="text/plain",
            use_container_width=True
        )


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    Speed Climbing Performance Analysis v1.0 (Phase 5)<br>
    تحلیل عملکرد سنگنوردی سرعتی نسخه ۱.۰
    </div>
    """,
    unsafe_allow_html=True
)

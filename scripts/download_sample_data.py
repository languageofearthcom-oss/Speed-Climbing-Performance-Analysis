#!/usr/bin/env python3
"""
Speed Climbing Performance Analysis - Sample Data Downloader
دانلود داده‌های نمونه برای تحلیل عملکرد صعود سرعتی

This script downloads sample data for testing and demonstrations.
این اسکریپت داده‌های نمونه برای تست و نمایش را دانلود می‌کند.

Usage / استفاده:
    python scripts/download_sample_data.py
    python scripts/download_sample_data.py --include-video

Note: Video files are optional and larger (~5-10MB each).
نکته: فایل‌های ویدیو اختیاری و حجیم‌تر هستند (~5-10MB هر کدام).
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

# GitHub Release URL for sample data
GITHUB_RELEASE_BASE = "https://github.com/airano-ir/speed-climbing-performance-analysis/releases/download"
SAMPLE_VERSION = "v1.0.0"

# Sample data files
SAMPLE_FILES = {
    "pose_sample.json": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/pose_sample.json",
        "sha256": None,  # Will be set when file is actually uploaded
        "size_mb": 0.5,
        "description": "Sample pose extraction data (JSON)",
        "required": True
    },
    "feedback_sample.json": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/feedback_sample.json",
        "sha256": None,
        "size_mb": 0.01,
        "description": "Sample feedback output",
        "required": True
    }
}

# Optional video samples (larger files)
VIDEO_SAMPLES = {
    "sample_race.mp4": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/sample_race.mp4",
        "sha256": None,
        "size_mb": 5.0,
        "description": "Sample race video clip (5 seconds)",
        "required": False
    }
}


def download_file(url: str, dest_path: Path, expected_sha256: str = None) -> bool:
    """
    Download a file with progress indicator.

    Args:
        url: URL to download from
        dest_path: Local path to save file
        expected_sha256: Optional SHA256 hash to verify

    Returns:
        True if download successful, False otherwise
    """
    try:
        print(f"Downloading: {dest_path.name}")
        print(f"  From: {url}")

        # Download
        urllib.request.urlretrieve(url, dest_path)

        # Verify hash if provided
        if expected_sha256:
            with open(dest_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash != expected_sha256:
                print(f"  WARNING: Hash mismatch!")
                print(f"    Expected: {expected_sha256}")
                print(f"    Got: {file_hash}")
                return False

        print(f"  Done: {dest_path}")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def create_offline_samples(data_dir: Path):
    """
    Create basic sample files offline (no download needed).

    Args:
        data_dir: Directory to create samples in
    """
    # Create a minimal sample feedback file
    sample_feedback = {
        "analysis_info": {
            "version": "1.0.0",
            "language": "en",
            "note": "This is a sample file created offline"
        },
        "performance_scores": {
            "coordination": {"score": 75.0, "rating": "good"},
            "leg_technique": {"score": 70.0, "rating": "good"},
            "arm_technique": {"score": 72.0, "rating": "good"},
            "body_position": {"score": 68.0, "rating": "average"},
            "reach": {"score": 65.0, "rating": "average"}
        },
        "overall_score": 70.0,
        "overall_rating": "good"
    }

    feedback_path = data_dir / "sample_feedback_offline.json"
    with open(feedback_path, 'w') as f:
        json.dump(sample_feedback, f, indent=2)

    print(f"Created offline sample: {feedback_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Download sample data for Speed Climbing Performance Analysis"
    )
    parser.add_argument(
        "--include-video",
        action="store_true",
        help="Also download sample video files (larger download)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Create minimal sample files without downloading"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/samples",
        help="Directory to save downloaded files"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Speed Climbing Performance Analysis - Sample Data")
    print("تحلیل عملکرد صعود سرعتی - داده‌های نمونه")
    print("=" * 60)
    print()

    if args.offline:
        print("Creating offline sample files...")
        create_offline_samples(output_dir)
        print()
        print("Done! Offline samples created.")
        return 0

    # Download required files
    print("Downloading required sample files...")
    success_count = 0
    fail_count = 0

    for filename, info in SAMPLE_FILES.items():
        dest_path = output_dir / filename
        if download_file(info['url'], dest_path, info.get('sha256')):
            success_count += 1
        else:
            fail_count += 1

    # Download optional video files
    if args.include_video:
        print()
        print("Downloading optional video samples...")
        for filename, info in VIDEO_SAMPLES.items():
            dest_path = output_dir / filename
            if download_file(info['url'], dest_path, info.get('sha256')):
                success_count += 1
            else:
                fail_count += 1

    # Summary
    print()
    print("=" * 60)
    print(f"Download complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Location: {output_dir.absolute()}")
    print()

    if fail_count > 0:
        print("Note: Some downloads failed. You can:")
        print("  1. Run again to retry")
        print("  2. Use --offline to create minimal samples")
        print("  3. Download manually from GitHub releases")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

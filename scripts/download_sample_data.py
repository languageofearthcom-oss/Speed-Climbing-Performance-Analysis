#!/usr/bin/env python3
"""
Speed Climbing Performance Analysis - Sample Data Downloader
دانلود داده‌های نمونه برای تحلیل عملکرد صعود سرعتی

This script downloads sample data for testing and demonstrations.
این اسکریپت داده‌های نمونه برای تست و نمایش را دانلود می‌کند.

Usage / استفاده:
    python scripts/download_sample_data.py
    python scripts/download_sample_data.py --include-video
    python scripts/download_sample_data.py --download-races
    python scripts/download_sample_data.py --download-races --race seoul_2024

Note: Video files are optional and larger (~5-10MB each).
نکته: فایل‌های ویدیو اختیاری و حجیم‌تر هستند (~5-10MB هر کدام).
"""

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
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

# Race segments data (extracted pose data from IFSC competitions)
RACE_SEGMENTS = {
    "seoul_2024": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/race_segments_seoul_2024.zip",
        "sha256": None,
        "size_mb": 150,
        "description": "IFSC Seoul 2024 - 31 race segments",
        "races": 31
    },
    "villars_2024": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/race_segments_villars_2024.zip",
        "sha256": None,
        "size_mb": 120,
        "description": "IFSC Villars 2024 - 28 race segments",
        "races": 28
    },
    "chamonix_2024": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/race_segments_chamonix_2024.zip",
        "sha256": None,
        "size_mb": 140,
        "description": "IFSC Chamonix 2024 - 30 race segments",
        "races": 30
    },
    "innsbruck_2024": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/race_segments_innsbruck_2024.zip",
        "sha256": None,
        "size_mb": 180,
        "description": "IFSC Innsbruck 2024 - 35 race segments",
        "races": 35
    },
    "zilina_2025": {
        "url": f"{GITHUB_RELEASE_BASE}/{SAMPLE_VERSION}/race_segments_zilina_2025.zip",
        "sha256": None,
        "size_mb": 160,
        "description": "IFSC Zilina 2025 - 32 race segments",
        "races": 32
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

        # Download with progress
        def report_progress(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, block_num * block_size * 100 // total_size)
                print(f"\r  Progress: {percent}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()  # New line after progress

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

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  ERROR: File not found (404)")
            print(f"  The release may not be published yet.")
            print(f"  Check: https://github.com/airano-ir/speed-climbing-performance-analysis/releases")
        else:
            print(f"  ERROR: HTTP {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """
    Extract a ZIP file.

    Args:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"  Extracting: {zip_path.name}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"  Extracted to: {extract_to}")
        # Optionally remove ZIP after extraction
        # zip_path.unlink()
        return True
    except Exception as e:
        print(f"  ERROR extracting: {e}")
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


def list_available_races():
    """Print list of available race segments."""
    print("\nAvailable Race Segments:")
    print("=" * 60)
    total_size = 0
    total_races = 0
    for name, info in RACE_SEGMENTS.items():
        print(f"  {name}:")
        print(f"    {info['description']}")
        print(f"    Size: ~{info['size_mb']} MB")
        total_size += info['size_mb']
        total_races += info['races']
    print("=" * 60)
    print(f"Total: {total_races} races, ~{total_size} MB")
    print("\nUsage:")
    print("  --download-races          Download all race segments")
    print("  --race <name>             Download specific race (e.g., --race seoul_2024)")


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
        "--download-races",
        action="store_true",
        help="Download race segment data from IFSC competitions (~750MB total)"
    )
    parser.add_argument(
        "--race",
        type=str,
        help="Download specific race segment (e.g., seoul_2024, villars_2024)"
    )
    parser.add_argument(
        "--list-races",
        action="store_true",
        help="List available race segments"
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

    # List races and exit
    if args.list_races:
        list_available_races()
        return 0

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

    success_count = 0
    fail_count = 0

    # Download required files
    print("Downloading required sample files...")
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

    # Download race segments
    if args.download_races or args.race:
        print()
        races_dir = output_dir / "race_segments"
        races_dir.mkdir(parents=True, exist_ok=True)

        races_to_download = RACE_SEGMENTS.items()
        if args.race:
            if args.race not in RACE_SEGMENTS:
                print(f"ERROR: Unknown race '{args.race}'")
                print("Available races:", ", ".join(RACE_SEGMENTS.keys()))
                return 1
            races_to_download = [(args.race, RACE_SEGMENTS[args.race])]
            print(f"Downloading race segment: {args.race}")
        else:
            print("Downloading all race segments (~750MB total)...")

        for name, info in races_to_download:
            zip_path = races_dir / f"{name}.zip"
            if download_file(info['url'], zip_path, info.get('sha256')):
                if extract_zip(zip_path, races_dir / name):
                    success_count += 1
                else:
                    fail_count += 1
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
        print("  4. Check if the release v1.0.0 has been published")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

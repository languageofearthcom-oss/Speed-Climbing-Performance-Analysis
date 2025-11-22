#!/usr/bin/env python3
"""
Threshold Sweep Test
====================
Tests different validation score thresholds to find optimal balance.
"""

import sys
from pathlib import Path
import cv2

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from speed_climbing.vision.holds import HoldDetector
from speed_climbing.vision.calibration import CameraCalibrator


def test_threshold_sweep(video_path: str, route_map_path: str):
    """Test different validation thresholds."""

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("ERROR: Could not read frame")
        return

    detector = HoldDetector(
        route_coordinates_path=route_map_path,
        use_spatial_filtering=False
    )

    calibrator = CameraCalibrator(route_coordinates_path=route_map_path)

    # Detect and calibrate
    initial_holds = detector.detect_holds(frame)
    calibration_result = calibrator.calibrate(frame, initial_holds)

    if not calibration_result:
        print("ERROR: Calibration failed")
        return

    homography = calibration_result.homography_matrix

    # Test different thresholds
    print(f"\n{'='*80}")
    print(f"Threshold Sweep Analysis")
    print(f"{'='*80}\n")
    print(f"Video: {Path(video_path).name}")
    print(f"Initial detections: {len(initial_holds)}\n")

    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    print(f"{'Threshold':<12} {'Validated':<12} {'Removed':<12} {'Rate':<12}")
    print("-" * 48)

    for threshold in thresholds:
        validated = detector.validate_holds(
            initial_holds.copy(),
            homography,
            frame.shape[:2],
            min_validation_score=threshold
        )

        removed = len(initial_holds) - len(validated)
        rate = removed / len(initial_holds) * 100

        print(f"{threshold:<12.1f} {len(validated):<12d} {removed:<12d} {rate:<12.1f}%")

    # Detailed analysis at threshold=0.4 (more permissive)
    print(f"\n{'='*80}")
    print(f"DETAILED: threshold=0.4 (recommended)")
    print(f"{'='*80}\n")

    validated_04 = detector.validate_holds(
        initial_holds.copy(),
        homography,
        frame.shape[:2],
        min_validation_score=0.4
    )

    print(f"Validated holds ({len(validated_04)}):")
    for hold in validated_04:
        match = f"#{hold.hold_num} at {hold.grid_position}" if hold.hold_num else "No match"
        dist = f"{hold.spatial_distance:.2f}m" if hold.spatial_distance is not None else "N/A"

        print(f"  {match:20s} | dist={dist:6s} | score={hold.validation_score:.3f}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Test Threshold Sweep')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--route-map', default='configs/ifsc_route_coordinates.json')

    args = parser.parse_args()

    test_threshold_sweep(args.video, args.route_map)


if __name__ == '__main__':
    main()

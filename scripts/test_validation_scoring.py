#!/usr/bin/env python3
"""
Test Multi-Criteria Hold Validation
====================================
Compares old binary filtering vs new validation scoring approach.
"""

import sys
from pathlib import Path
import cv2
import json
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from speed_climbing.vision.holds import HoldDetector
from speed_climbing.vision.calibration import CameraCalibrator


def test_validation_comparison(video_path: str, route_map_path: str, output_path: str = None):
    """Test validation scoring vs binary filtering."""

    print(f"\n{'='*80}")
    print(f"Multi-Criteria Hold Validation Test")
    print(f"{'='*80}\n")

    # Read frame
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("ERROR: Could not open video")
        return

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("ERROR: Could not read frame")
        return

    h, w = frame.shape[:2]

    # Initialize detector
    detector = HoldDetector(
        route_coordinates_path=route_map_path,
        use_spatial_filtering=False,
        use_climber_masking=False,
        spatial_tolerance_m=0.30
    )

    calibrator = CameraCalibrator(route_coordinates_path=route_map_path)

    # Step 1: Detect holds
    print("STEP 1: Initial hold detection")
    print("-" * 80)
    initial_holds = detector.detect_holds(frame)
    print(f"  Detected: {len(initial_holds)} holds\n")

    for i, hold in enumerate(initial_holds, 1):
        print(f"    {i:2d}. pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f}), "
              f"area={hold.contour_area:5.0f}px, conf={hold.confidence:.3f}")

    # Step 2: Calibration
    print(f"\nSTEP 2: Camera calibration")
    print("-" * 80)
    calibration_result = calibrator.calibrate(frame, initial_holds)

    if not calibration_result or calibration_result.homography_matrix is None:
        print("  ❌ Calibration failed")
        return

    print(f"  ✓ Calibration successful")
    print(f"    Confidence: {calibration_result.confidence:.2f}")
    print(f"    Inliers: {calibration_result.inlier_count}/{calibration_result.total_holds}")

    homography = calibration_result.homography_matrix

    # Step 3: Validation with different thresholds
    print(f"\nSTEP 3: Multi-criteria validation")
    print("-" * 80)

    # Test different validation thresholds
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

    for threshold in thresholds:
        validated = detector.validate_holds(
            initial_holds.copy(),
            homography,
            frame.shape[:2],
            min_validation_score=threshold
        )
        print(f"  Threshold {threshold:.1f}: {len(validated)} holds")

    # Use moderate threshold for detailed output
    print(f"\nDETAILED RESULTS (threshold=0.5)")
    print("-" * 80)

    validated_holds = detector.validate_holds(
        initial_holds.copy(),
        homography,
        frame.shape[:2],
        min_validation_score=0.5
    )

    print(f"\nValidated holds ({len(validated_holds)}):")
    for i, hold in enumerate(validated_holds, 1):
        match_info = f"#{hold.hold_num} at {hold.grid_position}" if hold.hold_num else "No match"
        dist_info = f"{hold.spatial_distance:.2f}m" if hold.spatial_distance is not None else "N/A"

        print(f"  {i:2d}. {match_info:20s} | "
              f"dist={dist_info:6s} | "
              f"score={hold.validation_score:.3f} | "
              f"conf={hold.confidence:.3f} | "
              f"area={hold.contour_area:5.0f}px")

    # Summary
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")

    # Analyze which holds were rejected and why
    rejected_holds = [h for h in initial_holds if h not in validated_holds]

    if rejected_holds:
        print(f"\n❌ Rejected holds ({len(rejected_holds)}):")
        for hold in rejected_holds:
            dist_info = f"{hold.spatial_distance:.2f}m" if hold.spatial_distance is not None else "N/A"
            score_info = f"{hold.validation_score:.3f}" if hold.validation_score is not None else "N/A"

            print(f"  • pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f})")
            print(f"    Spatial distance: {dist_info}")
            print(f"    Validation score: {score_info} (too low)")
            print(f"    Shape confidence: {hold.confidence:.3f}")
            print()

    # Key insights
    print("KEY INSIGHTS:")
    print(f"  - Initial detections: {len(initial_holds)}")
    print(f"  - After validation: {len(validated_holds)}")
    print(f"  - Rejection rate: {(len(initial_holds)-len(validated_holds))/len(initial_holds)*100:.1f}%")

    if validated_holds:
        avg_score = sum(h.validation_score for h in validated_holds) / len(validated_holds)

        holds_with_dist = [h for h in validated_holds if h.spatial_distance is not None]
        if holds_with_dist:
            avg_dist = sum(h.spatial_distance for h in holds_with_dist) / len(holds_with_dist)
            print(f"  - Average validation score: {avg_score:.3f}")
            print(f"  - Average spatial distance: {avg_dist:.2f}m")
        else:
            print(f"  - Average validation score: {avg_score:.3f}")
            print(f"  - Average spatial distance: N/A")

    # Visualization
    if output_path:
        vis = create_validation_viz(frame, initial_holds, validated_holds, detector, homography)
        cv2.imwrite(output_path, vis)
        print(f"\n✓ Saved to: {output_path}")


def create_validation_viz(frame, initial_holds, validated_holds, detector, homography):
    """Create visualization showing validation scores."""
    h, w = frame.shape[:2]

    # Panel 1: All detections with scores
    panel1 = frame.copy()
    for hold in initial_holds:
        x, y = int(hold.pixel_x), int(hold.pixel_y)

        # Color based on validation score
        if hold.validation_score:
            if hold.validation_score >= 0.7:
                color = (0, 255, 0)  # Green - high score
            elif hold.validation_score >= 0.5:
                color = (0, 255, 255)  # Yellow - medium
            else:
                color = (0, 0, 255)  # Red - low score
        else:
            color = (128, 128, 128)  # Gray - no score

        cv2.circle(panel1, (x, y), 8, color, 2)

        # Show score
        if hold.validation_score:
            label = f"{hold.validation_score:.2f}"
            cv2.putText(panel1, label, (x+10, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    cv2.putText(panel1, "All Detections (colored by score)", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(panel1, f"{len(initial_holds)} total", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Panel 2: Only validated holds
    panel2 = frame.copy()
    for i, hold in enumerate(validated_holds, 1):
        x, y = int(hold.pixel_x), int(hold.pixel_y)
        cv2.circle(panel2, (x, y), 10, (0, 255, 0), 2)

        label = f"#{hold.hold_num}" if hold.hold_num else str(i)
        cv2.putText(panel2, label, (x+12, y-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    cv2.putText(panel2, "Validated Holds (score >= 0.5)", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(panel2, f"{len(validated_holds)} validated", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Resize and combine
    target_w = 600
    scale = target_w / w
    panel1 = cv2.resize(panel1, (target_w, int(h * scale)))
    panel2 = cv2.resize(panel2, (target_w, int(h * scale)))

    combined = np.hstack([panel1, panel2])

    return combined


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Test Multi-Criteria Validation')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--route-map', default='configs/ifsc_route_coordinates.json',
                       help='Path to route map JSON')
    parser.add_argument('--output', '-o', help='Output image path')

    args = parser.parse_args()

    test_validation_comparison(args.video, args.route_map, args.output)


if __name__ == '__main__':
    main()

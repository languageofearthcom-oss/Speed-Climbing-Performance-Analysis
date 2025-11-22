#!/usr/bin/env python3
"""
Test Complete Hold Detection Pipeline
======================================
Shows the full pipeline with all improvements:
1. Detection without climber masking (for calibration)
2. Detection with climber masking (for tracking)
3. Spatial filtering
4. Dual-lane awareness
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


def test_complete_pipeline(video_path: str, route_map_path: str, output_path: str = None):
    """Test complete pipeline with all features."""

    print(f"\n{'='*80}")
    print(f"Complete Hold Detection Pipeline Test")
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
        use_spatial_filtering=False,  # We'll apply manually
        use_climber_masking=True,  # Enabled but we control when to use
        spatial_tolerance_m=0.30
    )

    calibrator = CameraCalibrator(route_coordinates_path=route_map_path)

    # ========== STEP 1: Calibration (without climber masking) ==========
    print("STEP 1: Initial hold detection (for calibration)")
    print("-" * 80)
    print("  Strategy: No climber masking to ensure enough holds for RANSAC")

    holds_for_calibration = detector.detect_holds(frame, apply_climber_masking=False)
    print(f"  ✓ Detected: {len(holds_for_calibration)} holds\n")

    for i, hold in enumerate(holds_for_calibration[:10], 1):
        print(f"    {i:2d}. pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f}), "
              f"area={hold.contour_area:5.0f}px, conf={hold.confidence:.3f}")

    # ========== STEP 2: Camera Calibration ==========
    print(f"\nSTEP 2: Camera calibration")
    print("-" * 80)

    calibration_result = calibrator.calibrate(frame, holds_for_calibration)

    if not calibration_result or calibration_result.homography_matrix is None:
        print("  ❌ Calibration failed - cannot proceed")
        return

    print(f"  ✓ Calibration successful")
    print(f"    Confidence: {calibration_result.confidence:.2f}")
    print(f"    Inliers: {calibration_result.inlier_count}/{calibration_result.total_holds}")

    homography = calibration_result.homography_matrix

    # ========== STEP 3: Detection with climber masking ==========
    print(f"\nSTEP 3: Hold detection with climber masking")
    print("-" * 80)
    print("  Strategy: Remove false positives on athlete bodies")

    holds_with_masking = detector.detect_holds(frame, apply_climber_masking=True)
    removed_by_masking = len(holds_for_calibration) - len(holds_with_masking)

    print(f"  ✓ Detected: {len(holds_with_masking)} holds")
    print(f"  ✓ Removed by climber masking: {removed_by_masking} false positives\n")

    for i, hold in enumerate(holds_with_masking[:10], 1):
        print(f"    {i:2d}. pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f}), "
              f"area={hold.contour_area:5.0f}px, conf={hold.confidence:.3f}")

    # ========== STEP 4: Spatial filtering ==========
    print(f"\nSTEP 4: Spatial filtering (match to route map)")
    print("-" * 80)
    print(f"  Strategy: Only keep holds within {detector.spatial_tolerance_m}m of expected positions")

    holds_filtered = detector.filter_by_spatial_grid(
        holds_with_masking,
        homography,
        frame.shape[:2]
    )
    removed_by_spatial = len(holds_with_masking) - len(holds_filtered)

    print(f"  ✓ Valid holds: {len(holds_filtered)}")
    print(f"  ✓ Removed by spatial filtering: {removed_by_spatial} false positives\n")

    for i, hold in enumerate(holds_filtered, 1):
        print(f"    {i:2d}. Hold #{hold.hold_num} at {hold.grid_position} "
              f"(panel {hold.panel}), conf={hold.confidence:.3f}")

    # ========== STEP 5: Summary ==========
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"  Initial detections (for calibration):  {len(holds_for_calibration)}")
    print(f"  After climber masking:                 {len(holds_with_masking)} (-{removed_by_masking})")
    print(f"  After spatial filtering:               {len(holds_filtered)} (-{removed_by_spatial})")
    print(f"  Total false positives removed:         {len(holds_for_calibration) - len(holds_filtered)}")
    print(f"  False positive rate:                   {(len(holds_for_calibration) - len(holds_filtered)) / len(holds_for_calibration) * 100:.1f}%")

    # ========== Visualization ==========
    if output_path or True:
        vis = create_visualization(
            frame,
            holds_for_calibration,
            holds_with_masking,
            holds_filtered,
            detector,
            homography
        )

        if output_path:
            cv2.imwrite(output_path, vis)
            print(f"\n✓ Saved visualization to: {output_path}")
        else:
            cv2.imshow('Complete Pipeline', vis)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


def create_visualization(frame, holds_calib, holds_masked, holds_filtered, detector, homography):
    """Create 3-panel visualization showing pipeline stages."""
    h, w = frame.shape[:2]

    # Panel 1: For calibration (no masking)
    panel1 = frame.copy()
    for i, hold in enumerate(holds_calib[:15], 1):
        x, y = int(hold.pixel_x), int(hold.pixel_y)
        cv2.circle(panel1, (x, y), 8, (0, 0, 255), 2)
        cv2.putText(panel1, str(i), (x+10, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    cv2.putText(panel1, f"Step 1: Calibration", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(panel1, f"{len(holds_calib)} detections", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Panel 2: With climber masking
    panel2 = frame.copy()
    climber_mask = detector.create_climber_mask(frame)
    if climber_mask is not None:
        # Show mask overlay
        mask_overlay = cv2.cvtColor(climber_mask, cv2.COLOR_GRAY2BGR)
        mask_overlay = cv2.applyColorMap(mask_overlay, cv2.COLORMAP_HOT)
        panel2 = cv2.addWeighted(panel2, 0.7, mask_overlay, 0.3, 0)

    for i, hold in enumerate(holds_masked[:15], 1):
        x, y = int(hold.pixel_x), int(hold.pixel_y)
        cv2.circle(panel2, (x, y), 8, (0, 255, 255), 2)
        cv2.putText(panel2, str(i), (x+10, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.putText(panel2, f"Step 2: Climber Masking", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(panel2, f"{len(holds_masked)} detections (-{len(holds_calib)-len(holds_masked)})", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Panel 3: After spatial filtering
    panel3 = frame.copy()
    for i, hold in enumerate(holds_filtered, 1):
        x, y = int(hold.pixel_x), int(hold.pixel_y)
        cv2.circle(panel3, (x, y), 10, (0, 255, 0), 2)
        label = f"#{hold.hold_num}" if hold.hold_num else str(i)
        cv2.putText(panel3, label, (x+12, y-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    cv2.putText(panel3, f"Step 3: Spatial Filtering", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(panel3, f"{len(holds_filtered)} valid holds (-{len(holds_masked)-len(holds_filtered)})", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Resize panels
    target_w = 500
    scale = target_w / w
    panel1 = cv2.resize(panel1, (target_w, int(h * scale)))
    panel2 = cv2.resize(panel2, (target_w, int(h * scale)))
    panel3 = cv2.resize(panel3, (target_w, int(h * scale)))

    # Combine horizontally
    combined = np.hstack([panel1, panel2, panel3])

    return combined


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Test Complete Pipeline')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--route-map', default='configs/ifsc_route_coordinates.json',
                       help='Path to route map JSON')
    parser.add_argument('--output', '-o', help='Output image path')

    args = parser.parse_args()

    test_complete_pipeline(args.video, args.route_map, args.output)


if __name__ == '__main__':
    main()

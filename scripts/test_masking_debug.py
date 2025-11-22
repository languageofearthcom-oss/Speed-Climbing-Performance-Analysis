#!/usr/bin/env python3
"""
Debug climber masking to see what's being filtered
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


def test_masking_debug(video_path: str, route_map_path: str, output_path: str = None):
    """Test climber masking in detail."""

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

    # Test 1: Detection WITHOUT climber masking
    print("\n" + "="*70)
    print("Test 1: Without Climber Masking")
    print("="*70)

    detector_no_mask = HoldDetector(
        route_coordinates_path=route_map_path,
        use_spatial_filtering=False,
        use_climber_masking=False
    )
    holds_no_mask = detector_no_mask.detect_holds(frame)
    print(f"Detected: {len(holds_no_mask)} holds")
    for i, hold in enumerate(holds_no_mask[:10], 1):
        print(f"  {i:2d}. pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f}), "
              f"area={hold.contour_area:5.0f}px, conf={hold.confidence:.3f}")

    # Test 2: Detection WITH climber masking
    print("\n" + "="*70)
    print("Test 2: With Climber Masking")
    print("="*70)

    detector_with_mask = HoldDetector(
        route_coordinates_path=route_map_path,
        use_spatial_filtering=False,
        use_climber_masking=True
    )
    holds_with_mask = detector_with_mask.detect_holds(frame)
    print(f"Detected: {len(holds_with_mask)} holds")
    for i, hold in enumerate(holds_with_mask[:10], 1):
        print(f"  {i:2d}. pos=({hold.pixel_x:6.1f}, {hold.pixel_y:6.1f}), "
              f"area={hold.contour_area:5.0f}px, conf={hold.confidence:.3f}")

    print(f"\n✓ Climber masking removed: {len(holds_no_mask) - len(holds_with_mask)} false positives")

    # Visualization
    vis = np.hstack([
        draw_holds(frame.copy(), holds_no_mask, "Without Masking"),
        draw_holds(frame.copy(), holds_with_mask, "With Masking")
    ])

    # Also show the climber mask
    climber_mask = detector_with_mask.create_climber_mask(frame)
    if climber_mask is not None:
        mask_vis = cv2.cvtColor(climber_mask, cv2.COLOR_GRAY2BGR)
        mask_vis = cv2.resize(mask_vis, (w // 2, h // 2))

        # Resize main vis to match
        vis_resized = cv2.resize(vis, (w, h // 2))

        # Combine
        final = np.vstack([vis_resized, np.hstack([mask_vis, mask_vis])])
    else:
        final = vis
        print("\n⚠️  Climber mask was None (no pose detected)")

    if output_path:
        cv2.imwrite(output_path, final)
        print(f"\nSaved to: {output_path}")
    else:
        cv2.imshow('Masking Debug', final)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def draw_holds(frame, holds, title):
    """Draw holds on frame."""
    for i, hold in enumerate(holds[:10], 1):
        x, y = int(hold.pixel_x), int(hold.pixel_y)
        cv2.circle(frame, (x, y), 8, (0, 0, 255), 2)
        cv2.putText(frame, str(i), (x+10, y-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    cv2.putText(frame, title, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"{len(holds)} detections", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return frame


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Debug climber masking')
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--route-map', default='configs/ifsc_route_coordinates.json',
                       help='Path to route map JSON')
    parser.add_argument('--output', '-o', help='Output image path')

    args = parser.parse_args()

    test_masking_debug(args.video, args.route_map, args.output)


if __name__ == '__main__':
    main()

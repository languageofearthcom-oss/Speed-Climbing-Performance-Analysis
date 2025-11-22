"""
Detect IFSC red holds in video frames using color-based detection.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

import cv2
import numpy as np

from speed_climbing.core.settings import DEFAULT_PROCESSING_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class DetectedHold:
    """Represents a detected hold in a video frame."""
    hold_num: Optional[int]  # Matched to IFSC route map, None if unmatched
    pixel_x: float
    pixel_y: float
    confidence: float  # 0.0 to 1.0
    contour_area: float
    panel: Optional[str] = None  # e.g., 'DX1', 'SN3'
    grid_position: Optional[str] = None  # e.g., 'F4', 'M8'


class HoldDetector:
    """Detect red IFSC holds in video frames using HSV color thresholding."""

    def __init__(
        self,
        route_coordinates_path: Optional[str] = None,
        min_area: int = 500,  # Increased to filter small noise (typical hold: 1000-10000px)
        max_area: int = 30000,  # Reduced to avoid large false regions
        min_confidence: float = 0.4,  # Increased from default to reduce false positives
        use_adaptive_hsv: bool = True,  # New: adaptive HSV based on lighting
        use_spatial_filtering: bool = True,  # New: filter by expected grid positions
        spatial_tolerance_m: float = 0.30,  # Tolerance for spatial filtering (meters) - increased to reduce false negatives
        use_climber_masking: bool = False  # New: mask out climber body (disabled by default as climbers stand in front of wall)
    ):
        self.min_area = min_area
        self.max_area = max_area
        self.min_confidence = min_confidence
        self.use_adaptive_hsv = use_adaptive_hsv
        self.use_spatial_filtering = use_spatial_filtering
        self.spatial_tolerance_m = spatial_tolerance_m
        self.use_climber_masking = use_climber_masking
        self.route_map = None

        # Initialize pose detector for climber masking (lazy loading)
        self._pose_detector = None

        if route_coordinates_path:
            self._load_route_coordinates(route_coordinates_path)

        # HSV range for red holds (More restrictive for fewer false positives)
        # Range 1: 0-12 (Pure red, tightened from 0-15)
        self.hsv_lower_red1 = np.array([0, 100, 100])  # Increased saturation/value for purer red
        self.hsv_upper_red1 = np.array([12, 255, 255])

        # Range 2: 168-180 (Red wrap-around, tightened from 165-180)
        self.hsv_lower_red2 = np.array([168, 100, 100])  # Increased saturation/value
        self.hsv_upper_red2 = np.array([180, 255, 255])

    def _load_route_coordinates(self, path: str):
        """Load IFSC route coordinates from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.route_map = json.load(f)
            logger.info(f"Loaded route map with {len(self.route_map['holds'])} holds")
        except Exception as e:
            logger.error(f"Failed to load route map from {path}: {e}")
            self.route_map = None

    def _get_pose_detector(self):
        """Lazy load MediaPipe pose detector."""
        if self._pose_detector is None:
            try:
                import mediapipe as mp
                self._pose_detector = mp.solutions.pose.Pose(
                    static_image_mode=True,
                    min_detection_confidence=0.3,
                    min_tracking_confidence=0.3
                )
            except ImportError:
                logger.warning("MediaPipe not available, climber masking disabled")
                self._pose_detector = False  # Mark as unavailable
        return self._pose_detector if self._pose_detector else None

    def create_climber_mask(
        self,
        frame: np.ndarray,
        expansion_radius: int = 40  # Moderate expansion to avoid covering holds
    ) -> Optional[np.ndarray]:
        """
        Create a binary mask covering climber(s) bodies using pose detection.

        Attempts to detect BOTH climbers (left and right lanes) by processing
        the frame twice - once for each half.

        Args:
            frame: Input BGR frame
            expansion_radius: Pixels to expand around detected body parts

        Returns:
            Binary mask (0=background, 255=climber) or None if detection fails
        """
        pose_detector = self._get_pose_detector()
        if pose_detector is None:
            return None

        try:
            h, w = frame.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            mid_x = w // 2

            # Try to detect climbers in both halves of the frame
            # This helps detect both left and right lane climbers
            regions = [
                (0, 0, w, h, "full"),  # Full frame (primary detection)
                (0, 0, mid_x + w//4, h, "left"),  # Left lane focused
                (mid_x - w//4, 0, w, h, "right"),  # Right lane focused
            ]

            detected_any = False

            for x1, y1, x2, y2, region_name in regions:
                # Extract region
                region = frame[y1:y2, x1:x2]

                # Convert to RGB for MediaPipe
                rgb_region = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
                results = pose_detector.process(rgb_region)

                if not results.pose_landmarks:
                    continue

                # Get landmark positions
                landmarks = results.pose_landmarks.landmark
                points = []

                for lm in landmarks:
                    # Adjust coordinates to full frame
                    x = int(lm.x * (x2 - x1)) + x1
                    y = int(lm.y * (y2 - y1)) + y1

                    # Only include visible landmarks
                    if 0 <= x < w and 0 <= y < h and lm.visibility > 0.3:
                        points.append((x, y))

                if len(points) < 5:  # Need at least 5 visible landmarks
                    continue

                # Create convex hull around body points
                points_array = np.array(points, dtype=np.int32)
                hull = cv2.convexHull(points_array)

                # Draw filled polygon on mask
                cv2.fillConvexPoly(mask, hull, 255)
                detected_any = True

                logger.debug(f"Detected climber in {region_name} region with {len(points)} landmarks")

            if not detected_any:
                return None

            # Expand mask to cover more area around bodies
            if expansion_radius > 0:
                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (expansion_radius * 2, expansion_radius * 2)
                )
                mask = cv2.dilate(mask, kernel, iterations=1)

            return mask

        except Exception as e:
            logger.debug(f"Failed to create climber mask: {e}")
            return None

    def detect_holds(
        self,
        frame: np.ndarray,
        lane: Optional[str] = None,
        return_mask: bool = False,  # New: option to return mask for debugging
        apply_climber_masking: Optional[bool] = None  # Override use_climber_masking for this call
    ) -> List[DetectedHold]:
        """
        Detect holds in a single video frame using blob/region detection.

        Args:
            frame: Input BGR frame
            lane: Optional lane filter ('left' or 'right')
            return_mask: If True, return (holds, mask) instead of just holds
            apply_climber_masking: Override for climber masking (None = use default)

        Returns:
            List of DetectedHold objects, or tuple (holds, mask) if return_mask=True
        """
        if frame is None or frame.size == 0:
            return [] if not return_mask else ([], None)

        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create mask for red color with expanded range
        mask1 = cv2.inRange(hsv, self.hsv_lower_red1, self.hsv_upper_red1)
        mask2 = cv2.inRange(hsv, self.hsv_lower_red2, self.hsv_upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # Gentler morphological operations to preserve blob shape
        kernel_small = np.ones((2, 2), np.uint8)
        kernel_medium = np.ones((5, 5), np.uint8)

        # Remove noise (small artifacts)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=1)

        # Fill small holes within blobs
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_medium, iterations=1)

        # Optional: Dilate slightly to merge nearby regions
        mask = cv2.dilate(mask, kernel_small, iterations=1)

        # Apply climber masking to remove false detections on athlete's body
        # Use override if provided, otherwise use default setting
        should_mask_climber = apply_climber_masking if apply_climber_masking is not None else self.use_climber_masking

        if should_mask_climber:
            climber_mask = self.create_climber_mask(frame)
            if climber_mask is not None:
                # Remove regions that overlap with climber
                # Invert climber mask (we want to keep areas NOT on climber)
                mask = cv2.bitwise_and(mask, cv2.bitwise_not(climber_mask))
                logger.debug("Applied climber masking to filter out body detections")

        # Find contours (regions of red)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_holds = []
        frame_height, frame_width = frame.shape[:2]
        mid_x = frame_width / 2

        for contour in contours:
            area = cv2.contourArea(contour)

            # More lenient area filtering
            if area < self.min_area or area > self.max_area:
                continue

            # Get moments for centroid
            M = cv2.moments(contour)
            if M['m00'] == 0:
                continue

            cx = M['m10'] / M['m00']
            cy = M['m01'] / M['m00']

            # Lane filtering
            if lane == 'left' and cx > mid_x:
                continue
            if lane == 'right' and cx < mid_x:
                continue

            # Improved confidence calculation based on blob properties
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            # Bounding box for aspect ratio
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h > 0 else 0

            # Circularity (1.0 = perfect circle)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            circularity = min(circularity, 1.0)

            # Extent (how much of bounding box is filled)
            extent = area / (w * h) if (w * h) > 0 else 0

            # Size score (prefer medium-sized blobs)
            # Typical hold blob: 1000-10000 pixels at typical camera distance
            ideal_size = 3000
            size_score = 1.0 - min(abs(area - ideal_size) / ideal_size, 1.0)
            size_score = max(0.1, size_score)  # Stricter minimum

            # Aspect ratio score (prefer roughly square blobs, but tolerate some variation)
            aspect_score = 1.0 - min(abs(aspect_ratio - 1.0), 1.0)
            aspect_score = max(0.2, aspect_score)  # Stricter minimum

            # Combined confidence
            # Weighted: circularity and extent matter most for holds
            confidence = (
                circularity * 0.35 +  # Holds tend to be round/circular
                extent * 0.35 +       # Holds should fill their bounding box well
                size_score * 0.2 +    # Size should be reasonable
                aspect_score * 0.1    # Aspect ratio less critical
            )

            # Stricter threshold to reduce false positives
            if confidence < self.min_confidence:
                continue

            detected_holds.append(DetectedHold(
                hold_num=None,
                pixel_x=cx,
                pixel_y=cy,
                confidence=confidence,
                contour_area=area
            ))

        detected_holds.sort(key=lambda h: h.confidence, reverse=True)

        if return_mask:
            return detected_holds, mask

        return detected_holds

    def filter_by_spatial_grid(
        self,
        detected_holds: List[DetectedHold],
        homography: Optional[np.ndarray],
        frame_shape: Tuple[int, int],
        lane: Optional[str] = None
    ) -> List[DetectedHold]:
        """
        Filter detected holds by comparing to expected grid positions from route map.

        This method can be called independently and will perform spatial filtering
        regardless of the use_spatial_filtering flag (which only controls automatic
        filtering in detect_holds).

        Args:
            detected_holds: List of initially detected holds
            homography: Homography matrix for pixel->world coordinate transform
            frame_shape: (height, width) of frame
            lane: 'left' or 'right' lane (filters route map by panel)

        Returns:
            Filtered list of holds that match expected positions
        """
        # Only check for required dependencies (not the use_spatial_filtering flag)
        if not self.route_map or homography is None:
            return detected_holds

        # Get expected hold positions from route map
        route_holds = self.route_map.get('holds', [])
        if not route_holds:
            return detected_holds

        # Filter route map by lane if specified
        if lane:
            lane_prefix = 'SN' if lane == 'left' else 'DX'
            route_holds = [h for h in route_holds if h.get('panel', '').startswith(lane_prefix)]

        # Extract expected world positions
        expected_positions = np.array([
            [h['wall_x_m'], h['wall_y_m']] for h in route_holds
        ], dtype=np.float32)

        # Transform detected holds to world coordinates
        filtered_holds = []
        height, width = frame_shape

        for hold in detected_holds:
            # Convert to pixel coordinates
            pixel_point = np.array([[hold.pixel_x, hold.pixel_y]], dtype=np.float32)

            # Transform to world coordinates
            try:
                world_point = cv2.perspectiveTransform(
                    pixel_point.reshape(-1, 1, 2),
                    homography
                )
                world_x, world_y = world_point[0][0]

                # Find closest expected position
                distances = np.sqrt(
                    (expected_positions[:, 0] - world_x) ** 2 +
                    (expected_positions[:, 1] - world_y) ** 2
                )
                min_distance = np.min(distances)
                closest_idx = np.argmin(distances)

                # Check if within tolerance
                if min_distance <= self.spatial_tolerance_m:
                    # Match found! Update hold info
                    matched_hold_info = route_holds[closest_idx]
                    hold.hold_num = matched_hold_info.get('hold_num')
                    hold.panel = matched_hold_info.get('panel')
                    hold.grid_position = matched_hold_info.get('grid_position')

                    # Boost confidence for spatially validated holds
                    hold.confidence = min(hold.confidence * 1.2, 1.0)

                    filtered_holds.append(hold)

            except Exception as e:
                # If transformation fails, skip this hold
                logger.debug(f"Failed to transform hold at ({hold.pixel_x}, {hold.pixel_y}): {e}")
                continue

        logger.info(f"Spatial filtering: {len(detected_holds)} -> {len(filtered_holds)} holds "
                   f"(removed {len(detected_holds) - len(filtered_holds)} false positives)")

        return filtered_holds

    def visualize_detections(
        self,
        frame: np.ndarray,
        detected_holds: List[DetectedHold],
        show_labels: bool = True
    ) -> np.ndarray:
        """Visualize detected holds on the frame."""
        output = frame.copy()

        for hold in detected_holds:
            x, y = int(hold.pixel_x), int(hold.pixel_y)
            color_value = int(255 * hold.confidence)
            color = (0, color_value, 255 - color_value)  # BGR

            cv2.circle(output, (x, y), 10, color, 2)

            if show_labels:
                label = f"{hold.confidence:.2f}"
                if hold.hold_num:
                    label = f"#{hold.hold_num} " + label
                
                cv2.putText(
                    output, label, (x + 15, y - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
                )

        return output

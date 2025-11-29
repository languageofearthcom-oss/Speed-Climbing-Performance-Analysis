"""
Athlete Count Detection for Speed Climbing Videos.

Detects whether a video contains one or two athletes based on
pose detection patterns in the left and right lanes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class AthleteDetectionResult:
    """Result of athlete count detection."""
    athlete_count: int  # 1 or 2
    primary_lane: str  # 'left', 'right', or 'both'
    left_detection_rate: float  # 0.0 to 1.0
    right_detection_rate: float  # 0.0 to 1.0
    confidence: float  # Detection confidence
    recommendation: str  # User-friendly recommendation

    @property
    def is_single_athlete(self) -> bool:
        return self.athlete_count == 1

    @property
    def is_dual_athlete(self) -> bool:
        return self.athlete_count == 2


class AthleteCountDetector:
    """
    Detect the number of athletes in a speed climbing video.

    Uses pose detection rates in left/right lanes to determine
    if the video contains one or two athletes.

    Thresholds:
    - If both lanes have >50% detection rate: 2 athletes
    - If only one lane has >30% detection rate: 1 athlete
    - Otherwise: unclear, default to analyzing the better lane
    """

    def __init__(
        self,
        dual_athlete_threshold: float = 0.40,
        single_athlete_threshold: float = 0.25,
        min_difference_ratio: float = 2.0
    ):
        """
        Args:
            dual_athlete_threshold: Min detection rate for both lanes to be "dual"
            single_athlete_threshold: Min detection rate for a lane to be "valid"
            min_difference_ratio: Min ratio between lanes for "single" classification
        """
        self.dual_athlete_threshold = dual_athlete_threshold
        self.single_athlete_threshold = single_athlete_threshold
        self.min_difference_ratio = min_difference_ratio

    def detect_from_pose_data(self, pose_data: Dict) -> AthleteDetectionResult:
        """
        Detect athlete count from pose data dictionary.

        Args:
            pose_data: Dictionary with 'metadata' and 'frames' keys

        Returns:
            AthleteDetectionResult with detection details
        """
        metadata = pose_data.get('metadata', {})
        frames = pose_data.get('frames', [])

        # Try to get detection rates from metadata first
        left_rate = metadata.get('detection_rate_left', None)
        right_rate = metadata.get('detection_rate_right', None)

        # If not in metadata, calculate from frames
        if left_rate is None or right_rate is None:
            left_rate, right_rate = self._calculate_detection_rates(frames)

        return self._analyze_detection_rates(left_rate, right_rate)

    def detect_from_frames(self, frames: List[Dict]) -> AthleteDetectionResult:
        """
        Detect athlete count from frame list.

        Args:
            frames: List of frame dictionaries with left_climber/right_climber

        Returns:
            AthleteDetectionResult with detection details
        """
        left_rate, right_rate = self._calculate_detection_rates(frames)
        return self._analyze_detection_rates(left_rate, right_rate)

    def _calculate_detection_rates(
        self,
        frames: List[Dict]
    ) -> Tuple[float, float]:
        """Calculate detection rates for left and right lanes."""
        if not frames:
            return 0.0, 0.0

        left_detections = 0
        right_detections = 0
        total_frames = len(frames)

        for frame in frames:
            left_climber = frame.get('left_climber')
            right_climber = frame.get('right_climber')

            if left_climber and left_climber.get('has_detection', False):
                left_detections += 1

            if right_climber and right_climber.get('has_detection', False):
                right_detections += 1

        left_rate = left_detections / total_frames if total_frames > 0 else 0.0
        right_rate = right_detections / total_frames if total_frames > 0 else 0.0

        return left_rate, right_rate

    def _analyze_detection_rates(
        self,
        left_rate: float,
        right_rate: float
    ) -> AthleteDetectionResult:
        """Analyze detection rates to determine athlete count."""

        # Case 1: Both lanes have good detection -> 2 athletes
        if (left_rate >= self.dual_athlete_threshold and
            right_rate >= self.dual_athlete_threshold):

            # Check if they're relatively balanced
            ratio = max(left_rate, right_rate) / (min(left_rate, right_rate) + 1e-6)

            if ratio < self.min_difference_ratio:
                return AthleteDetectionResult(
                    athlete_count=2,
                    primary_lane='both',
                    left_detection_rate=left_rate,
                    right_detection_rate=right_rate,
                    confidence=min(left_rate, right_rate),
                    recommendation="Two athletes detected. Select the lane you want to analyze."
                )

        # Case 2: Only one lane has significant detection -> 1 athlete
        max_rate = max(left_rate, right_rate)
        min_rate = min(left_rate, right_rate)

        if max_rate >= self.single_athlete_threshold:
            # Determine which lane is primary
            if left_rate > right_rate:
                primary_lane = 'left'
            else:
                primary_lane = 'right'

            # Check confidence based on difference
            if min_rate < self.single_athlete_threshold:
                # Clear single athlete
                confidence = max_rate
                athlete_count = 1
                recommendation = f"Single athlete detected in {primary_lane} lane."
            else:
                # Both have detection but one is dominant
                ratio = max_rate / (min_rate + 1e-6)
                if ratio >= self.min_difference_ratio:
                    confidence = max_rate * (1 - min_rate / max_rate)
                    athlete_count = 1
                    recommendation = f"Likely single athlete in {primary_lane} lane (other lane has noise)."
                else:
                    # Unclear, treat as dual
                    confidence = min(left_rate, right_rate) * 0.7
                    athlete_count = 2
                    primary_lane = 'both'
                    recommendation = "Two athletes detected. Select the lane you want to analyze."

            return AthleteDetectionResult(
                athlete_count=athlete_count,
                primary_lane=primary_lane,
                left_detection_rate=left_rate,
                right_detection_rate=right_rate,
                confidence=confidence,
                recommendation=recommendation
            )

        # Case 3: No clear detection in either lane
        return AthleteDetectionResult(
            athlete_count=0,
            primary_lane='unknown',
            left_detection_rate=left_rate,
            right_detection_rate=right_rate,
            confidence=0.0,
            recommendation="No clear athlete detection. Check video quality or upload a different file."
        )

    def get_recommended_lane(self, pose_data: Dict) -> str:
        """
        Get the recommended lane to analyze based on detection quality.

        Args:
            pose_data: Pose data dictionary

        Returns:
            'left' or 'right' - the lane with better detection
        """
        result = self.detect_from_pose_data(pose_data)

        if result.primary_lane == 'both':
            # For dual athlete, pick the one with slightly better detection
            if result.left_detection_rate >= result.right_detection_rate:
                return 'left'
            else:
                return 'right'
        elif result.primary_lane in ['left', 'right']:
            return result.primary_lane
        else:
            # Default to left if unclear
            return 'left'


def detect_athlete_count(pose_data: Dict) -> AthleteDetectionResult:
    """
    Convenience function to detect athlete count from pose data.

    Args:
        pose_data: Dictionary with 'metadata' and 'frames'

    Returns:
        AthleteDetectionResult
    """
    detector = AthleteCountDetector()
    return detector.detect_from_pose_data(pose_data)


def get_valid_lanes(pose_data: Dict, min_detection_rate: float = 0.25) -> List[str]:
    """
    Get list of lanes with valid detection data.

    Args:
        pose_data: Pose data dictionary
        min_detection_rate: Minimum detection rate to be considered valid

    Returns:
        List of valid lane names ('left', 'right', or both)
    """
    detector = AthleteCountDetector(single_athlete_threshold=min_detection_rate)
    result = detector.detect_from_pose_data(pose_data)

    valid_lanes = []
    if result.left_detection_rate >= min_detection_rate:
        valid_lanes.append('left')
    if result.right_detection_rate >= min_detection_rate:
        valid_lanes.append('right')

    return valid_lanes

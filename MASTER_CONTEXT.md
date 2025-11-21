# MASTER CONTEXT: Speed Climbing Performance Analysis

## Project Overview
**Goal**: Build an automated video analysis system for speed climbing that tracks athletes, maps their position to the official IFSC wall (15m), and calculates performance metrics (velocity, splits, etc.).

**Current Status**: **Refactoring Complete & Testing (Phase 2.6)**
All core components have been migrated to the `speed_climbing` package. The full pipeline has been verified on a test video.

## Architecture (New)
The project is being migrated to a domain-driven structure:

### `speed_climbing` Package
*   **`core`**: Configuration and standards.
    *   `settings.py`: IFSC standards, default config.
*   **`vision`**: Computer Vision components.
    *   `holds.py`: `HoldDetector` (HSV-based).
    *   `lanes.py`: `DualLaneDetector` (Boundary detection).
    *   `pose.py`: `BlazePoseExtractor` (MediaPipe wrapper).
    *   `calibration.py`: `CameraCalibrator`, `PeriodicCalibrator` (Homography).
*   **`processing`**: Pipeline logic.
    *   `tracking.py`: `WorldCoordinateTracker` (Pixel -> Meter).
    *   `dropout.py`: `DropoutHandler` (Error recovery).
    *   `pipeline.py`: `GlobalMapVideoProcessor` (Orchestrator).
*   **`analysis`**: Data aggregation.
    *   `time_series.py`: `TimeSeriesBuilder`.

## Key Workflows
1.  **Global Map Registration**:
    *   Detect red holds.
    *   Match to IFSC route map (`configs/ifsc_route_coordinates.json`).
    *   Compute Homography (RANSAC).
    *   Transform Athlete COM (Center of Mass) to Wall Coordinates (Meters).

## Recent Updates
*   **2025-11-20**:
    *   Completed migration of `TimeSeriesBuilder`, `DropoutHandler`, `WorldCoordinateTracker`, and `GlobalMapVideoProcessor`.
    *   Verified full pipeline with `scripts/run_new_pipeline.py`.
    *   Successful end-to-end test on `race001` (14.39m detected distance).
    *   **Cleanup**: Removed legacy `src/` directory.
    *   **Batch Processing**: Added `scripts/batch_process_races.py` and documentation.

*   **2025-11-21**:
    *   **Major Hold Detection Improvements**:
        *   Implemented stricter spatial filtering (6cm tolerance vs. 15cm).
        *   Added greedy matching algorithm with uniqueness constraint (each expected hold matches ≤1 detection).
        *   Fixed circular reasoning bug where all calibration inputs were accepted as valid.
        *   Added ROI masking support (`create_wall_roi_mask()`) to exclude scoreboard/floor/ads.
        *   Added climber masking support (`create_climber_mask_from_pose()`) to exclude detections on athlete.
        *   **Result**: 40% false positive reduction (5 → 3 holds in test case).

## Known Issues / Focus Areas
*   **Hold Detection**: ~~Sensitivity to lighting/angle~~ **IMPROVED** - Spatial filtering now effectively removes false positives.
    *   Remaining issues: Some edge cases with non-race scenes (ads, replays).
    *   Mitigation: ROI masking, climber masking, stricter tolerance (6cm).
*   **Calibration**: Needs robust RANSAC to handle partial wall visibility.
*   **Physical Validation**: Initial prototype showed some height discrepancies, but full pipeline produced reasonable total distance. Needs fine-tuning.

## Next Steps
1.  Test improved hold detection on batch processing runs.
2.  Integrate ROI and climber masking into main pipeline (`pipeline.py`).
3.  Run batch processing on more races using `scripts/batch_process_races.py`.
4.  Analyze batch results to identify remaining failure modes.
5.  Implement "Calibration Quality" visualization.

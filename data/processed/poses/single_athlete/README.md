# Single-Athlete Pose Time-Series (PhD ML Phase 3 input)

**Added**: 2026-04-30
**Purpose**: Provide pose keypoint time-series for downstream supervised models in `phd-ml/phase3-cnn` (1D-CNN over temporal landmarks).

---

## What's here

- **114 JSON files** (`Speed_finals_<comp>_race###_pose.json`)
- **152 MB total** across 5 competitions
- **MANIFEST.csv** — index of every file with race_id, frame counts, success rate, inferred lane, fps, resolution

```
single_athlete/
├── MANIFEST.csv
├── README.md
├── poses_chamonix_2024/    29 races
├── poses_innsbruck_2024/   29 races
├── poses_seoul_2024/       29 races
├── poses_villars_2024/     19 races
└── poses_zilina_2025/       8 races
```

---

## File schema

Single-athlete extraction (33 MediaPipe BlazePose landmarks per frame, normalized to image dimensions).

```jsonc
{
  "race_id": "Speed_finals_Seoul_2024_race001",
  "competition": "seoul_2024",
  "frames": [
    {
      "frame_number": 46,
      "timestamp": 1.533,
      "landmarks": [
        {"x": 0.802, "y": 0.426, "z": 0.076, "visibility": 0.9996},
        // ... 33 BlazePose landmarks total
      ]
    }
    // ... typically ~150–250 frames per race (race window only)
  ],
  "total_frames": 200,
  "extracted_frames": 199,
  "missing_frames": 1,
  "success_rate": 99.5,
  "extraction_date": "2025-11-17T13:47:10",
  "start_frame": 45,
  "finish_frame": 244,
  "fps": 30.0,
  "frame_width": 1280,
  "frame_height": 720
}
```

---

## ⚠️ Important caveats — read before use

### 1. NOT dual-lane — single athlete per race

Source videos are dual-athlete (two parallel speed-climbing lanes). **Each pose JSON contains only ONE of the two climbers' landmarks**, not both. There is no `lane` field, no `left_climber` / `right_climber` separation, and only 33 landmarks per frame (not 66).

Inferred lane distribution (from mean x-coordinate of visible landmarks across the first 50 frames):

| Lane (inferred) | Count |
|-----------------|-------|
| left  (mean_x < 0.45) | 64 |
| right (mean_x > 0.55) | 39 |
| center (0.45 ≤ x ≤ 0.55) — ambiguous | 11 |
| **total** | **114** |

The "center" group likely reflects races where the camera follows a single climber or the extraction picked landmarks spanning the divider. The lane in `MANIFEST.csv` is **inferred, not authoritative**.

### 2. Format differs from `data/processed/poses/samples/`

The 10 files under `data/processed/poses/samples/*_poses.json` (plural suffix) use a **different schema** that includes both lanes:

```jsonc
// samples/*_poses.json (dual-lane reference format)
{
  "metadata": { ... },
  "frames": [
    { "frame_id": 0, "timestamp": 0.0,
      "left_climber": {"keypoints": [...], ...},
      "right_climber": {"keypoints": [...], ...} }
  ]
}
```

These two formats are **not interchangeable**. Loaders should branch on filename suffix or top-level keys.

### 3. Coverage is incomplete (114 / 188 races = 61 %)

| Competition | Found | Expected | Missing |
|-------------|-------|----------|---------|
| chamonix_2024  | 29 | 32 | 3 (races 10, 13, 24) |
| innsbruck_2024 | 29 | 32 | 3 (races 1, 4, 11) |
| seoul_2024     | 29 | 31 | 2 (races 22, 23) — race 15 already removed upstream |
| villars_2024   | 19 | 24 | 5 (races 2, 13, 15, 19, 23) |
| zilina_2025    |  8 | 69 | 61 |
| **total**      | **114** | **188** | **74** |

The large Zilina gap is consistent with the slippery-wall issue documented in `MASTER_CONTEXT.md` (many failed climbs).

### 4. Quality is high overall

- mean `success_rate` = 97.0 %
- median = 99.4 %
- 109 / 114 files (95.6 %) have `success_rate ≥ 80 %`
- 99 / 114 files (86.8 %) have `success_rate ≥ 95 %`
- min observed: 64.7 %

For Phase 3 training, applying the same `success_rate ≥ 80 %` filter the project uses elsewhere would yield **109 usable time-series**, not 246. The "246" figure from `data/ml_dataset/all_features.csv` came from dual-lane × races; it does not apply here.

---

## How to load

```python
import json
from pathlib import Path

def load_pose(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)

def to_array(pose: dict):
    """Return (T, 33, 4) array of [x, y, z, visibility]."""
    import numpy as np
    return np.array([[ [lm['x'], lm['y'], lm['z'], lm['visibility']]
                       for lm in frame['landmarks']]
                     for frame in pose['frames']], dtype=np.float32)
```

---

## What's still missing for Phase 3

1. **Second climber per race** — to get the full dual-lane dataset, `scripts/batch/extract_poses.py` (already in this branch) needs to be re-run on the 188 race MP4s using the dual-lane detector, producing the full `*_poses.json` schema.
2. **74 missing races** — same script, on the races listed above.
3. **Authoritative lane labels** — re-run with `dual_lane_detector.py` so each frame carries `left_climber` / `right_climber` directly.

These files are committed as a starting point for Phase 3 exploration; they are not the final dataset.

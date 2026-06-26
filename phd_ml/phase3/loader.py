"""Load Phase-1 labels and pose JSONs, build (N, T, C) tensors.

Two pose JSON schemas exist in the repo (see
data/processed/poses/single_athlete/README.md for the difference):

- Single-athlete:  {frames: [{frame_number, timestamp, landmarks: [33×{x,y,z,visibility}]}]}
- Dual-lane:       {metadata, frames: [{frame_id, left_climber, right_climber}]}

This loader detects the schema per file and emits a (T, 33, 3) tensor of
(x, y, z) for one climber per file. Where dual-lane is available, the
caller can request both lanes; the default behaviour matches the single-
athlete extraction we have today.

The label join is by `video_id` after stripping the `_pose`/`_poses`
suffix; rows in the labeled CSV that have no matching pose JSON are
recorded in `intersect_report.csv` and dropped silently from training.
"""
from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from . import config


# ---------------------------------------------------------------------------
# BlazePose landmark order
# ---------------------------------------------------------------------------
# Canonical name → index map used by the dual-lane schema, which keys
# keypoints by anatomical name rather than position. The single-athlete
# schema uses a positional list and does not need this mapping.
BLAZEPOSE_LANDMARK_ORDER: tuple[str, ...] = (
    "nose",
    "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear",
    "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_pinky", "right_pinky",
    "left_index", "right_index",
    "left_thumb", "right_thumb",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
)


# ---------------------------------------------------------------------------
# Filename / race_id helpers
# ---------------------------------------------------------------------------

_POSE_SUFFIX_RE = re.compile(r"_poses?$")


def race_id_from_path(path: Path) -> str:
    """Convert a pose JSON filename to the canonical race_id."""
    return _POSE_SUFFIX_RE.sub("", path.stem)


def race_id_from_video_id(video_id: str) -> str:
    return _POSE_SUFFIX_RE.sub("", video_id)


def competition_from_race_id(race_id: str) -> str:
    """Return competition tag, e.g. Chamonix_2024 from canonical race_id."""
    parts = race_id.split("_")
    return "_".join(parts[2:4]) if len(parts) >= 4 else race_id


# ---------------------------------------------------------------------------
# Schema detection + per-file extraction
# ---------------------------------------------------------------------------

def _is_single_athlete_schema(payload: dict) -> bool:
    if not payload.get("frames"):
        return False
    return "landmarks" in payload["frames"][0]


def _extract_single_athlete(payload: dict) -> np.ndarray:
    """Return (T, 33, 3) array of (x, y, z) for the single-athlete schema."""
    frames = payload["frames"]
    arr = np.zeros((len(frames), config.N_LANDMARKS, config.CHANNELS_PER_LANDMARK),
                   dtype=np.float32)
    for t, frame in enumerate(frames):
        for j, lm in enumerate(frame["landmarks"][: config.N_LANDMARKS]):
            if lm.get("visibility", 1.0) < config.VISIBILITY_THRESHOLD:
                continue   # leave as zero; mask is implicit
            arr[t, j, 0] = lm["x"]
            arr[t, j, 1] = lm["y"]
            arr[t, j, 2] = lm.get("z", 0.0)
    return arr


def _extract_dual_lane(payload: dict, lane: str) -> np.ndarray:
    """Return (T, 33, 3) for either 'left_climber' or 'right_climber'.

    Dual-lane sample files key keypoints by anatomical name, not position,
    so we map names back to positions via BLAZEPOSE_LANDMARK_ORDER.
    """
    if lane not in {"left_climber", "right_climber"}:
        raise ValueError(f"unknown lane {lane!r}")
    frames = payload["frames"]
    arr = np.zeros((len(frames), config.N_LANDMARKS, config.CHANNELS_PER_LANDMARK),
                   dtype=np.float32)
    for t, frame in enumerate(frames):
        climber = frame.get(lane) or {}
        kpts = climber.get("keypoints") or {}
        if isinstance(kpts, dict):
            for j, name in enumerate(BLAZEPOSE_LANDMARK_ORDER):
                lm = kpts.get(name)
                if not lm or lm.get("visibility", 1.0) < config.VISIBILITY_THRESHOLD:
                    continue
                arr[t, j, 0] = lm.get("x", 0.0)
                arr[t, j, 1] = lm.get("y", 0.0)
                arr[t, j, 2] = lm.get("z", 0.0)
        elif isinstance(kpts, list):
            for j, lm in enumerate(kpts[: config.N_LANDMARKS]):
                if lm.get("visibility", 1.0) < config.VISIBILITY_THRESHOLD:
                    continue
                arr[t, j, 0] = lm.get("x", 0.0)
                arr[t, j, 1] = lm.get("y", 0.0)
                arr[t, j, 2] = lm.get("z", 0.0)
    return arr


def load_pose_array(path: Path, lane: str | None = None) -> np.ndarray:
    """Load a pose JSON and return (T, 33, 3) regardless of schema.

    For dual-lane files, `lane` must be "left" or "right" so the tensor
    matches the Phase-1 lane-level label row.
    """
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if _is_single_athlete_schema(payload):
        return _extract_single_athlete(payload)
    if lane not in {"left", "right"}:
        raise ValueError("dual-lane pose requires lane='left' or lane='right'")
    return _extract_dual_lane(payload, f"{lane}_climber")


# ---------------------------------------------------------------------------
# Temporal normalisation
# ---------------------------------------------------------------------------

def resample_to_length(arr: np.ndarray, target: int) -> np.ndarray:
    """Linear-interpolation resample (T, J, C) → (target, J, C).

    Speed climbs have variable lengths (mean ~6.5s on the 15m wall).
    Resampling to a uniform length lets the 1D-CNN see a fixed temporal
    receptive field. Linear interpolation is the conservative choice; for
    final reporting consider DTW-based alignment.
    """
    t_orig = arr.shape[0]
    if t_orig == target:
        return arr
    if t_orig < 2:
        # Degenerate input — pad with zeros.
        out = np.zeros((target, *arr.shape[1:]), dtype=arr.dtype)
        out[:t_orig] = arr
        return out
    src = np.linspace(0.0, 1.0, t_orig)
    dst = np.linspace(0.0, 1.0, target)
    out = np.zeros((target, *arr.shape[1:]), dtype=arr.dtype)
    for j in range(arr.shape[1]):
        for c in range(arr.shape[2]):
            out[:, j, c] = np.interp(dst, src, arr[:, j, c])
    return out


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------

@dataclass
class PoseDataset:
    X: np.ndarray            # (N, T, 33*3) — channels-last for downstream conv
    y: np.ndarray            # (N,) binary {0, 1}, 1 = POSITIVE_CLASS (minority)
    sample_ids: list[str]    # race_id:lane keys in row order
    phase1_indices: list[int] # original labeled_dataset.csv row indices for Phase-2 joins
    classes: list[str]
    intersect_report: pd.DataFrame


def _discover_dual_pose_files() -> dict[str, Path]:
    """Build {race_id: path} for dual-lane sample pose files."""
    by_race: dict[str, Path] = {}
    if config.POSE_DIR_DUAL_SAMPLES.exists():
        for p in config.POSE_DIR_DUAL_SAMPLES.glob("*.json"):
            by_race[race_id_from_path(p)] = p
    return by_race


def _discover_single_pose_files() -> dict[str, tuple[Path, str]]:
    """Build {race_id: (path, inferred_lane)} from MANIFEST.csv.

    Single-athlete pose files contain one climber only. The Phase-1 labels are
    lane-level rows, so using a single-athlete pose for both left and right
    lanes would duplicate the tensor with potentially wrong labels. We accept
    only rows whose label lane matches `athlete_lane_inferred`.
    """
    by_race: dict[str, tuple[Path, str]] = {}
    manifest = config.POSE_DIR_SINGLE / "MANIFEST.csv"
    if manifest.exists():
        mf = pd.read_csv(manifest)
        for _, row in mf.iterrows():
            path = config.PROJECT_ROOT / str(row["file_path"])
            by_race[str(row["race_id"])] = (path, str(row["athlete_lane_inferred"]))
        return by_race

    # Fallback for development checkouts without a manifest. Lane is unknown,
    # so these files will be dropped as `single_lane_unknown` downstream.
    if config.POSE_DIR_SINGLE.exists():
        for p in config.POSE_DIR_SINGLE.rglob("*_pose.json"):
            by_race[race_id_from_path(p)] = (p, "unknown")
    return by_race


def build_dataset(target_length: int = config.TARGET_SEQUENCE_LENGTH) -> PoseDataset:
    """Intersect labeled CSV with on-disk pose JSONs and return a ready-to-train PoseDataset.

    Writes an `intersect_report.csv` that records which rows survived and why.
    """
    if not config.PHASE1_LABELED.exists():
        raise FileNotFoundError(
            f"Phase-1 labeled dataset not found at {config.PHASE1_LABELED}. "
            "Run `python -m phd_ml.phase1.run_pipeline` first."
        )

    df = pd.read_csv(config.PHASE1_LABELED)
    if config.TARGET_COLUMN not in df.columns:
        raise ValueError(f"missing target column {config.TARGET_COLUMN!r}")

    dual_pose_index = _discover_dual_pose_files()
    single_pose_index = _discover_single_pose_files()

    rows: list[dict] = []
    X_list: list[np.ndarray] = []
    y_list: list[int] = []
    sample_ids: list[str] = []
    phase1_indices: list[int] = []

    classes = sorted(df[config.TARGET_COLUMN].unique().tolist(),
                     key=lambda c: c == config.POSITIVE_CLASS)
    label_to_int = {classes[0]: 0, classes[1]: 1}

    for phase1_index, row in df.iterrows():
        video_id = str(row["video_id"])
        race_id = race_id_from_video_id(video_id)
        lane = str(row.get("lane", "")).lower()
        label_str = row[config.TARGET_COLUMN]

        if lane not in {"left", "right"}:
            rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                         "lane": lane, "label": label_str, "status": "invalid_lane",
                         "pose_path": None, "pose_schema": None})
            continue

        path: Path | None = None
        schema: str | None = None
        inferred_lane: str | None = None
        if race_id in dual_pose_index:
            path = dual_pose_index[race_id]
            schema = "dual_lane"
        elif race_id in single_pose_index:
            path, inferred_lane = single_pose_index[race_id]
            schema = "single_athlete"
            if inferred_lane not in {"left", "right"}:
                rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                             "lane": lane, "label": label_str,
                             "status": f"single_lane_uncertain:{inferred_lane}",
                             "pose_path": str(path), "pose_schema": schema})
                continue
            if inferred_lane != lane:
                rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                             "lane": lane, "label": label_str,
                             "status": f"single_lane_mismatch:{inferred_lane}",
                             "pose_path": str(path), "pose_schema": schema})
                continue
        else:
            rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                         "lane": lane, "label": label_str,
                         "status": "missing_pose", "pose_path": None,
                         "pose_schema": None})
            continue

        try:
            arr = load_pose_array(path, lane=lane)
        except Exception as exc:
            rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                         "lane": lane, "label": label_str,
                         "status": f"load_error:{exc}", "pose_path": str(path),
                         "pose_schema": schema})
            continue

        if arr.shape[0] < 2:
            rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                         "lane": lane, "label": label_str,
                         "status": "too_few_frames", "pose_path": str(path),
                         "pose_schema": schema})
            continue

        arr = resample_to_length(arr, target_length)
        X_list.append(arr.reshape(target_length, -1))   # flatten (J,C) → channels
        y_list.append(label_to_int[label_str])
        sample_ids.append(f"{race_id}:{lane}")
        phase1_indices.append(int(phase1_index))
        rows.append({"phase1_index": int(phase1_index), "race_id": race_id,
                     "lane": lane, "label": label_str, "status": "ok",
                     "pose_path": str(path), "pose_schema": schema})

    intersect_report = pd.DataFrame(rows)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    intersect_report.to_csv(config.INTERSECT_REPORT, index=False)

    if not X_list:
        raise RuntimeError("no usable samples after intersect — check pose paths")

    X = np.stack(X_list, axis=0).astype(np.float32)   # (N, T, 99)
    y = np.asarray(y_list, dtype=np.int64)

    minority = int((y == 1).sum())
    if minority < config.CV_FOLDS:
        warnings.warn(
            f"only {minority} minority-class samples after intersect — "
            f"StratifiedKFold({config.CV_FOLDS}) will not produce a positive "
            "instance in every fold. Consider reducing CV_FOLDS or running "
            "subject_aware splitting.",
            stacklevel=2,
        )

    print(
        f"[loader] retained {X.shape[0]} samples of {len(df)} labeled rows. "
        f"shape X={X.shape}, y={y.shape}. "
        f"class balance: {classes[0]}={int((y==0).sum())}, "
        f"{classes[1]}={int((y==1).sum())}."
    )

    return PoseDataset(
        X=X, y=y, sample_ids=sample_ids, phase1_indices=phase1_indices, classes=classes,
        intersect_report=intersect_report,
    )


# ---------------------------------------------------------------------------
# Split strategies
# ---------------------------------------------------------------------------

def _athlete_from_race_id(race_id: str) -> str:
    """Heuristic athlete identifier (placeholder — replace with project metadata).

    The race_id pattern is `Speed_finals_<Competition>_<Year>_race<NNN>` which
    contains no athlete name. For a real subject-aware split, the loader needs
    the athlete column from data/race_segments/*_results.json (one race file
    per race). This stub returns the competition tag so callers see a working
    grouping during scaffold testing — REPLACE before any reported result.
    """
    return competition_from_race_id(race_id)


def _warn_if_fold_is_single_class(ds: PoseDataset, splits: list[tuple[np.ndarray, np.ndarray]]) -> None:
    for i, (_, val_idx) in enumerate(splits):
        y_val = ds.y[val_idx]
        if len(np.unique(y_val)) < 2:
            warnings.warn(
                f"fold {i} validation set contains one class only "
                f"(advanced={int((y_val == 0).sum())}, beginner={int((y_val == 1).sum())}). "
                "ROC-AUC and PR-AUC will be undefined for this fold.",
                stacklevel=2,
            )


def iter_splits(ds: PoseDataset) -> Iterable[tuple[np.ndarray, np.ndarray]]:
    """Yield (train_idx, val_idx) per fold according to config.SPLIT_STRATEGY."""
    from sklearn.model_selection import StratifiedKFold, GroupKFold

    if config.SPLIT_STRATEGY == "stratified":
        warnings.warn(
            "SPLIT_STRATEGY='stratified' — random fold CV mirrors Phase 2 for "
            "paired comparison but cannot distinguish memorisation from "
            "learning under the tautology caveat. Use 'competition_aware' as a "
            "diagnostic stress test, and reserve true subject-aware claims for "
            "a future metadata join with athlete identifiers.",
            stacklevel=2,
        )
        skf = StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True,
                              random_state=config.RANDOM_STATE)
        splits = list(skf.split(ds.X, ds.y))
        _warn_if_fold_is_single_class(ds, splits)
        yield from splits
        return

    if config.SPLIT_STRATEGY == "competition_aware":
        groups = np.array([competition_from_race_id(s) for s in ds.sample_ids])
        n_groups = len(np.unique(groups))
        n_splits = min(config.CV_FOLDS, n_groups)
        if n_splits < config.CV_FOLDS:
            warnings.warn(
                f"competition_aware split has only {n_groups} groups; "
                f"using n_splits={n_splits} instead of CV_FOLDS={config.CV_FOLDS}.",
                stacklevel=2,
            )
        warnings.warn(
            "SPLIT_STRATEGY='competition_aware' is a competition holdout, not a "
            "true subject-aware split. The current repository does not contain "
            "athlete identifiers, so this is a diagnostic generalisation stress test.",
            stacklevel=2,
        )
        gkf = GroupKFold(n_splits=n_splits)
        splits = list(gkf.split(ds.X, ds.y, groups=groups))
        _warn_if_fold_is_single_class(ds, splits)
        yield from splits
        return

    if config.SPLIT_STRATEGY == "subject_aware":
        groups = np.array([_athlete_from_race_id(s) for s in ds.sample_ids])
        gkf = GroupKFold(n_splits=config.CV_FOLDS)
        splits = list(gkf.split(ds.X, ds.y, groups=groups))
        _warn_if_fold_is_single_class(ds, splits)
        yield from splits
        return

    raise ValueError(f"unknown SPLIT_STRATEGY={config.SPLIT_STRATEGY!r}")

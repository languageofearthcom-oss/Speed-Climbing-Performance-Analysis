"""Time-series augmentation for pose sequences.

Three augmentations are applied stochastically during training:

1. Gaussian noise — simulates BlazePose landmark jitter.
2. Time warping — linear stretch / compress along the temporal axis.
3. Mirroring — swaps left/right body landmarks (anatomical reflection).

SMOTE-style synthetic minority interpolation is intentionally NOT used on
time-series: interpolating two unrelated climbs in pose space produces
kinematically implausible sequences.
"""
from __future__ import annotations

import numpy as np

from . import config


# MediaPipe BlazePose left/right landmark pairs (33-landmark layout).
# Anatomical mirroring swaps the indices in each pair.
LEFT_RIGHT_PAIRS: list[tuple[int, int]] = [
    (1, 4), (2, 5), (3, 6), (7, 8), (9, 10),       # face
    (11, 12), (13, 14), (15, 16),                  # shoulders, elbows, wrists
    (17, 18), (19, 20), (21, 22),                  # finger landmarks
    (23, 24), (25, 26), (27, 28), (29, 30), (31, 32),  # hips, knees, ankles, feet
]


def add_gaussian_noise(arr: np.ndarray, std: float | None = None,
                      rng: np.random.Generator | None = None) -> np.ndarray:
    """Add zero-mean Gaussian noise in normalised landmark units."""
    std = config.AUG_GAUSSIAN_NOISE_STD if std is None else std
    rng = np.random.default_rng() if rng is None else rng
    return arr + rng.normal(0.0, std, size=arr.shape).astype(arr.dtype)


def time_warp(arr: np.ndarray, ratio: float | None = None,
              rng: np.random.Generator | None = None) -> np.ndarray:
    """Linearly stretch or compress along the time axis, then back to original T.

    `arr` shape is (T, C). The output is also (T, C) — we resample the
    warped sequence back to the original length, which is what the rest of
    the pipeline expects.
    """
    ratio = config.AUG_TIME_WARP_RATIO if ratio is None else ratio
    rng = np.random.default_rng() if rng is None else rng
    T = arr.shape[0]
    scale = 1.0 + rng.uniform(-ratio, ratio)
    src = np.linspace(0.0, 1.0, T)
    # Build a warped sample grid in [0,1] then re-uniform.
    warped = np.clip(src * scale, 0.0, 1.0)
    dst = np.linspace(0.0, 1.0, T)
    out = np.empty_like(arr)
    for c in range(arr.shape[1]):
        out[:, c] = np.interp(dst, warped, arr[:, c])
    return out


def mirror_landmarks(arr: np.ndarray, target_length: int = config.TARGET_SEQUENCE_LENGTH,
                     n_landmarks: int = config.N_LANDMARKS,
                     channels_per_landmark: int = config.CHANNELS_PER_LANDMARK) -> np.ndarray:
    """Swap left/right landmark indices and flip x-coordinate.

    Expects (T, n_landmarks * channels_per_landmark) layout consistent with
    loader.build_dataset. We reshape, swap pair indices on the landmark
    axis, flip the x channel about 0.5 (BlazePose x is normalised to image
    width in [0,1]), then flatten back.
    """
    T, F = arr.shape
    assert F == n_landmarks * channels_per_landmark, (
        f"mirror_landmarks expects F={n_landmarks * channels_per_landmark}, got {F}"
    )
    reshaped = arr.reshape(T, n_landmarks, channels_per_landmark).copy()
    for a, b in LEFT_RIGHT_PAIRS:
        if a < n_landmarks and b < n_landmarks:
            reshaped[:, [a, b]] = reshaped[:, [b, a]]
    # Flip x about the centre line.
    reshaped[..., 0] = 1.0 - reshaped[..., 0]
    return reshaped.reshape(T, F)


def augment_one(arr: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    """Apply the full augmentation pipeline to a single (T, F) sample.

    Each component fires stochastically — noise always, time-warp always,
    mirror with probability `AUG_MIRROR_PROBABILITY`.
    """
    rng = np.random.default_rng() if rng is None else rng
    out = add_gaussian_noise(arr, rng=rng)
    out = time_warp(out, rng=rng)
    if rng.random() < config.AUG_MIRROR_PROBABILITY:
        out = mirror_landmarks(out)
    return out


def augment_batch(X: np.ndarray, multiplicity: int | None = None,
                  rng: np.random.Generator | None = None
                  ) -> tuple[np.ndarray, np.ndarray]:
    """Expand each row of X to `multiplicity` augmented copies (plus the original).

    Returns (X_aug, source_indices) so the caller can re-broadcast labels.
    """
    multiplicity = config.AUG_MULTIPLICITY if multiplicity is None else multiplicity
    rng = np.random.default_rng() if rng is None else rng
    N = X.shape[0]
    out: list[np.ndarray] = []
    src_idx: list[int] = []
    for i in range(N):
        out.append(X[i])
        src_idx.append(i)
        for _ in range(multiplicity):
            out.append(augment_one(X[i], rng=rng))
            src_idx.append(i)
    return np.stack(out, axis=0), np.asarray(src_idx, dtype=np.int64)

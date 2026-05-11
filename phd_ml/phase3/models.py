"""1D-CNN architectures for pose time-series classification.

The default architecture is deliberately under 100k parameters — the
training set is only 246 samples (or fewer after pose intersect), so any
capacity beyond that overfits before learning anything useful. A future
study with a larger pose corpus should swap in ST-GCN (skeleton graph
convolution); for now the 1D-CNN is the parameter-budget-appropriate
choice.

Input shape: (B, T, F) where F = 33 landmarks × 3 (x,y,z) = 99 channels.
The model transposes to (B, F, T) internally for `nn.Conv1d`.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from . import config


class PoseCNN(nn.Module):
    """Two- or three-layer 1D-CNN with global average pooling.

    Parameters
    ----------
    in_channels : int
        Number of input channels per time step. Default 99 (33 landmarks ×
        3 spatial dims).
    n_classes : int
        Output classes. Default 2 for the binary beginner/advanced task.
    """

    def __init__(
        self,
        in_channels: int = config.N_LANDMARKS * config.CHANNELS_PER_LANDMARK,
        n_classes: int = 2,
        conv_channels: tuple[int, ...] = config.CONV_CHANNELS,
        kernels: tuple[int, ...] = config.CONV_KERNELS,
        dropout: float = config.DROPOUT,
        dense_hidden: int = config.DENSE_HIDDEN,
    ):
        super().__init__()
        assert len(conv_channels) == len(kernels)
        layers: list[nn.Module] = []
        prev = in_channels
        for c, k in zip(conv_channels, kernels):
            layers.extend([
                nn.Conv1d(prev, c, kernel_size=k, padding=k // 2),
                nn.BatchNorm1d(c),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            ])
            prev = c
        self.conv = nn.Sequential(*layers)
        self.gap = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(prev, dense_hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(dense_hidden, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F) → (B, F, T) for Conv1d.
        x = x.transpose(1, 2)
        h = self.conv(x)
        h = self.gap(h)
        return self.head(h)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_model() -> nn.Module:
    """Default factory used by run_pipeline."""
    return PoseCNN()

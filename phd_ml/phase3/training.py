"""Training loop with stratified / subject-aware CV and early stopping.

This file implements one fold's worth of training. The orchestrator
(run_pipeline.py) iterates over folds emitted by loader.iter_splits().
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from . import augmentation, config, models


@dataclass
class FoldResult:
    fold: int
    train_idx: np.ndarray
    val_idx: np.ndarray
    sample_ids_val: list[str]
    y_val: np.ndarray
    y_pred: np.ndarray
    y_prob: np.ndarray
    epochs_trained: int
    best_val_loss: float
    train_loss_history: list[float] = field(default_factory=list)
    val_loss_history: list[float] = field(default_factory=list)


def _device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _seed_everything(seed: int) -> None:
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if config.TORCH_DETERMINISTIC:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def _class_weights(y: np.ndarray) -> torch.Tensor:
    if config.CLASS_WEIGHT_STRATEGY == "none":
        return torch.ones(2, dtype=torch.float32)
    counts = np.bincount(y, minlength=2).astype(np.float32)
    inv = counts.sum() / np.maximum(counts, 1)
    return torch.tensor(inv / inv.mean(), dtype=torch.float32)


def _build_loaders(X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray, y_val: np.ndarray,
                   rng: np.random.Generator) -> tuple[DataLoader, DataLoader]:
    # Augment only the training fold.
    X_train_aug, src = augmentation.augment_batch(X_train, rng=rng)
    y_train_aug = y_train[src]

    train_ds = TensorDataset(
        torch.from_numpy(X_train_aug),
        torch.from_numpy(y_train_aug),
    )
    val_ds = TensorDataset(
        torch.from_numpy(X_val),
        torch.from_numpy(y_val),
    )
    train_loader = DataLoader(train_ds, batch_size=config.BATCH_SIZE, shuffle=True,
                              drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=config.BATCH_SIZE, shuffle=False)
    return train_loader, val_loader


def train_one_fold(fold: int, X: np.ndarray, y: np.ndarray, sample_ids: list[str],
                   train_idx: np.ndarray, val_idx: np.ndarray) -> FoldResult:
    _seed_everything(config.RANDOM_STATE + fold)
    rng = np.random.default_rng(config.RANDOM_STATE + fold)
    device = _device()

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]

    train_loader, val_loader = _build_loaders(X_train, y_train, X_val, y_val, rng)

    model = models.build_model().to(device)
    weights = _class_weights(y_train).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimiser = torch.optim.AdamW(model.parameters(),
                                  lr=config.LEARNING_RATE,
                                  weight_decay=config.WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimiser, T_max=config.EPOCHS) if config.LR_SCHEDULE == "cosine" else None

    best_val_loss = float("inf")
    best_state: dict | None = None
    patience = 0
    train_hist: list[float] = []
    val_hist: list[float] = []
    epochs_used = 0

    for epoch in range(config.EPOCHS):
        epochs_used = epoch + 1
        # ---- train ------------------------------------------------------
        model.train()
        epoch_loss = 0.0
        n_train = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimiser.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), config.GRADIENT_CLIP)
            optimiser.step()
            epoch_loss += float(loss.item()) * xb.size(0)
            n_train += xb.size(0)
        train_loss = epoch_loss / max(n_train, 1)
        train_hist.append(train_loss)

        # ---- val --------------------------------------------------------
        model.eval()
        val_loss = 0.0
        n_val = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device)
                logits = model(xb)
                loss = criterion(logits, yb)
                val_loss += float(loss.item()) * xb.size(0)
                n_val += xb.size(0)
        val_loss = val_loss / max(n_val, 1)
        val_hist.append(val_loss)

        if scheduler is not None:
            scheduler.step()

        # ---- early stopping --------------------------------------------
        if val_loss + 1e-6 < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= config.EARLY_STOPPING_PATIENCE:
                break

    # Restore best checkpoint, then predict.
    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(X_val).to(device))
        probs = torch.softmax(logits, dim=1).cpu().numpy()
    y_pred = probs.argmax(axis=1).astype(np.int64)
    y_prob_pos = probs[:, 1].astype(np.float32)

    return FoldResult(
        fold=fold,
        train_idx=train_idx, val_idx=val_idx,
        sample_ids_val=[sample_ids[i] for i in val_idx],
        y_val=y_val, y_pred=y_pred, y_prob=y_prob_pos,
        epochs_trained=epochs_used,
        best_val_loss=best_val_loss,
        train_loss_history=train_hist,
        val_loss_history=val_hist,
    )

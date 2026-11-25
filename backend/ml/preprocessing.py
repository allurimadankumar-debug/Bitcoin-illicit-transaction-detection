"""Feature assembly, temporal splitting and imbalance handling helpers."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.model_selection import train_test_split

from .dataset import TransactionDataset
from .graph_features import compute_graph_features


@dataclass
class FeatureBundle:
    matrix: np.ndarray
    names: list[str]
    graph_feature_count: int
    base_feature_count: int


def build_feature_bundle(
    dataset: TransactionDataset,
    *,
    include_graph_features: bool = True,
) -> FeatureBundle:
    """Combine base features with leakage-aware graph features."""
    matrix = dataset.feature_matrix.copy()
    matrix[~np.isfinite(matrix)] = np.nan
    names = list(dataset.feature_names)
    base_count = matrix.shape[1]

    graph_count = 0
    if include_graph_features:
        graph_matrix, graph_names = compute_graph_features(dataset)
        matrix = np.hstack([matrix, graph_matrix]).astype(np.float32)
        names.extend(graph_names)
        graph_count = len(graph_names)

    return FeatureBundle(
        matrix=matrix,
        names=names,
        graph_feature_count=graph_count,
        base_feature_count=base_count,
    )


@dataclass
class TemporalSplit:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    unlabeled: np.ndarray
    train_end_time: float
    validation_end_time: float

    def as_dict(self) -> dict[str, list[int]]:
        return {
            "train": self.train.tolist(),
            "validation": self.validation.tolist(),
            "test": self.test.tolist(),
            "unlabeled": self.unlabeled.tolist(),
        }


def temporal_split(
    time_steps: np.ndarray,
    labels: np.ndarray,
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> TemporalSplit:
    """Split labelled records by time, never shuffling future into the past.

    Splits are computed over distinct labelled time steps. When there are too
    few time steps for three disjoint periods, a deterministic fallback keeps
    the earliest records for training and the latest records for testing.
    """
    time_steps = np.asarray(time_steps)
    labels = np.asarray(labels, dtype=float)
    labeled_positions = np.flatnonzero(~np.isnan(labels))
    unlabeled_positions = np.flatnonzero(np.isnan(labels))
    if labeled_positions.size == 0:
        raise ValueError("No labelled transactions are available for supervised training.")

    labeled_times = time_steps[labeled_positions]
    unique_times = np.unique(labeled_times)
    if unique_times.size < 3:
        ordered = labeled_positions[np.argsort(labeled_times, kind="stable")]
        n = len(ordered)
        train = ordered[: max(1, int(n * 0.7))]
        validation = ordered[max(1, int(n * 0.7)) : max(2, int(n * 0.85))]
        test = ordered[max(2, int(n * 0.85)) :]
        if test.size == 0:  # pragma: no cover - tiny datasets only
            test = ordered[-1:]
        return TemporalSplit(
            train=train,
            validation=validation,
            test=test,
            unlabeled=unlabeled_positions,
            train_end_time=float(labeled_times[train[-1]]),
            validation_end_time=float(labeled_times[validation[-1]]) if validation.size else float(labeled_times[train[-1]]),
        )

    n_periods = len(unique_times)
    train_cut = max(1, int(n_periods * train_fraction))
    validation_cut = min(n_periods - 1, train_cut + max(1, int(n_periods * validation_fraction)))
    train_times = set(unique_times[:train_cut])
    validation_times = set(unique_times[train_cut:validation_cut])

    train = labeled_positions[np.isin(labeled_times, list(train_times))]
    validation = labeled_positions[np.isin(labeled_times, list(validation_times))]
    test = labeled_positions[labeled_times >= unique_times[validation_cut]]

    # Every split must contain rows. Borrow a single time step if needed.
    if validation.size == 0 and train.size > 1:
        moved_time = unique_times[train_cut - 1]
        validation = train[labeled_times[train] == moved_time]
        train = train[labeled_times[train] != moved_time]
    if test.size == 0:
        moved_time = unique_times[validation_cut - 1]
        test = validation[labeled_times[validation] == moved_time]
        validation = validation[labeled_times[validation] != moved_time]

    return TemporalSplit(
        train=train,
        validation=validation,
        test=test,
        unlabeled=unlabeled_positions,
        train_end_time=float(unique_times[train_cut - 1]),
        validation_end_time=float(unique_times[validation_cut - 1]),
    )


def compute_class_weights(labels: np.ndarray) -> dict[int, float]:
    """Balanced class weights for the illicit (1) / licit (0) target."""
    labels = np.asarray(labels, dtype=int)
    counts = np.bincount(labels, minlength=2)
    total = counts.sum()
    weights = {}
    for cls in (0, 1):
        count = counts[cls]
        weights[cls] = float(total / (2.0 * count)) if count > 0 else 1.0
    return weights


def stratified_holdout_indices(
    labels: np.ndarray, *, test_size: float = 0.2, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """Only used for internal diagnostics, never for temporal model selection."""
    clean = np.asarray(labels, dtype=int)
    return train_test_split(
        np.arange(len(clean)), test_size=test_size, random_state=seed, stratify=clean
    )

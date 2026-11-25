from __future__ import annotations

import numpy as np
import pytest

from ml.graph_features import GRAPH_FEATURE_NAMES, compute_graph_features
from ml.preprocessing import build_feature_bundle, compute_class_weights, temporal_split


def test_temporal_split_is_chronological(demo_dataset) -> None:
    labels = demo_dataset.transactions["label"].to_numpy(dtype=float)
    times = demo_dataset.transactions["time_step"].to_numpy(dtype=float)
    split = temporal_split(times, labels, train_fraction=0.7, validation_fraction=0.15)
    assert len(split.train) > 0 and len(split.validation) > 0 and len(split.test) > 0
    assert times[split.train].max() <= times[split.validation].max() <= times[split.test].max()
    assert np.isnan(labels[split.train]).sum() == 0
    assert np.isnan(labels[split.test]).sum() == 0


def test_class_weights_favor_minority() -> None:
    weights = compute_class_weights(np.array([0, 0, 0, 0, 1]))
    assert weights[1] > weights[0]


def test_bundle_includes_graph_features(demo_dataset) -> None:
    bundle = build_feature_bundle(demo_dataset)
    assert bundle.graph_feature_count == len(GRAPH_FEATURE_NAMES)
    assert bundle.matrix.shape == (demo_dataset.size, bundle.base_feature_count + len(GRAPH_FEATURE_NAMES))
    assert bundle.matrix.shape[1] == len(bundle.names)


def test_graph_features_are_non_negative(demo_dataset) -> None:
    features, names = compute_graph_features(demo_dataset)
    assert names == GRAPH_FEATURE_NAMES
    assert np.isfinite(features).all()
    assert (features[:, 0:3] >= 0).all()


def test_temporal_split_rejects_unlabeled_only() -> None:
    with pytest.raises(ValueError, match="No labelled"):
        temporal_split(np.arange(5), np.full(5, np.nan))

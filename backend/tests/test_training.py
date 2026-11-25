from __future__ import annotations

import json

import pytest

from app.core.config import get_settings
from ml.train import METRICS_FILE, MODEL_FILE, train


@pytest.mark.slow
def test_training_creates_artifacts(demo_dataset, settings) -> None:
    report = train(demo_dataset, settings=settings, calibrate=False)
    assert report["best_model"] in report["models"]
    test_metrics = report["test_metrics"]
    assert {"precision", "recall", "f1", "roc_auc", "pr_auc", "confusion_matrix"} <= set(test_metrics)
    assert (settings.models_path / MODEL_FILE).exists()
    metrics_file = settings.models_path / METRICS_FILE
    assert metrics_file.exists()
    payload = json.loads(metrics_file.read_text(encoding="utf-8"))
    assert payload["best_model"] == report["best_model"]
    assert payload["dataset"]["is_synthetic"] is True

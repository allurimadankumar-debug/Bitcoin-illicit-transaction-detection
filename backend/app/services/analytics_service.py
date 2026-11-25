from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import get_settings
from app.schemas.analytics import (
    ModelMetricsResponse,
    RiskBucket,
    RiskDistributionResponse,
    TemporalPoint,
    TemporalResponse,
)
from ml.predict import METRICS_FILE, get_predictor

from .data import get_dataset, get_risk_scores


def temporal_analysis(metric: str = "illicit_count") -> TemporalResponse:
    dataset = get_dataset()
    grouped: dict[int, Counter] = {}
    for _, row in dataset.transactions.iterrows():
        step = int(row["time_step"])
        counter = grouped.setdefault(step, Counter())
        counter["total"] += 1
        label = "unknown" if row["label"] != row["label"] else ("illicit" if int(row["label"]) == 1 else "licit")
        counter[label] += 1

    points = []
    for step in sorted(grouped):
        counter = grouped[step]
        total = counter["total"]
        illicit = counter["illicit"]
        points.append(
            TemporalPoint(
                time_step=step,
                total=total,
                illicit=illicit,
                licit=counter["licit"],
                unknown=counter["unknown"],
                illicit_rate=round(illicit / total, 6) if total else 0.0,
            )
        )
    return TemporalResponse(points=points, metric=metric, is_synthetic=dataset.is_synthetic)


def risk_distribution(bins: int = 10) -> RiskDistributionResponse:
    scores = get_risk_scores()
    dataset = get_dataset()
    bins = max(2, min(int(bins), 50))
    buckets = []
    unrated = 0
    if scores is None:
        unrated = dataset.size
        for index in range(bins):
            lower = index / bins
            upper = (index + 1) / bins
            buckets.append(RiskBucket(bucket=f"{lower:.2f}-{upper:.2f}", count=0))
    else:
        unrated = int((~np.isfinite(scores)).sum())
        counts, edges = np.histogram(scores[np.isfinite(scores)], bins=bins, range=(0.0, 1.0))
        buckets = [
            RiskBucket(bucket=f"{edges[i]:.2f}-{edges[i + 1]:.2f}", count=int(counts[i]))
            for i in range(bins)
        ]
    return RiskDistributionResponse(
        bins=bins,
        buckets=buckets,
        unrated=unrated,
        is_synthetic=dataset.is_synthetic,
    )


def model_metrics() -> ModelMetricsResponse:
    path: Path = get_settings().models_path / METRICS_FILE
    status = get_predictor().status()
    if not path.exists():
        return ModelMetricsResponse(
            available=False,
            message=status.get("message")
            or "Metrics are unavailable until a model is trained.",
        )
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover
        return ModelMetricsResponse(available=False, message="Metrics file is unreadable.")
    return ModelMetricsResponse(
        available=True,
        best_model=payload.get("best_model"),
        models=payload.get("models", {}),
        test_metrics=payload.get("test_metrics"),
        split=payload.get("split", {}),
        dataset=payload.get("dataset", {}),
        message=None if status["trained"] else "Metrics exist but the model artifact is missing.",
    )

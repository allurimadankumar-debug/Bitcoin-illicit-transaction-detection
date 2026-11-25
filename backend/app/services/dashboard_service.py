from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Prediction
from app.schemas.analytics import DashboardSummary
from ml.predict import METRICS_FILE, get_predictor

from .data import (
    configured_source,
    get_dataset,
    get_risk_scores,
    high_risk_threshold,
)
from .settings_service import get_setting


def _read_metrics() -> dict[str, Any] | None:
    path: Path = get_settings().models_path / METRICS_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):  # pragma: no cover
        return None


def get_dashboard_summary() -> DashboardSummary:
    dataset = get_dataset()
    scores = get_risk_scores()
    threshold = high_risk_threshold()
    high_risk = int((scores >= threshold).sum()) if scores is not None else 0
    metrics = _read_metrics()
    predictor_status = get_predictor().status()

    try:
        with SessionLocal() as db:
            prediction_count = int(db.query(Prediction).count())
    except Exception:  # pragma: no cover - database may be unavailable in tests
        prediction_count = 0

    best_pr_auc = best_recall = best_f1 = None
    if metrics:
        comparison = metrics.get("models", {})
        best_name = metrics.get("best_model")
        if best_name and best_name in comparison:
            best_pr_auc = comparison[best_name].get("pr_auc")
            best_recall = comparison[best_name].get("recall")
            best_f1 = comparison[best_name].get("f1")

    note = None
    if dataset.is_synthetic:
        note = (
            "DEMO MODE: all transactions, labels and metrics are synthetic and "
            "are not real Bitcoin blockchain observations."
        )
    elif not predictor_status["trained"]:
        note = "No trained model yet. Run `python backend/ml/train.py --source elliptic`."

    return DashboardSummary(
        total_transactions=dataset.size,
        labeled_transactions=int(dataset.labeled_mask.sum()),
        illicit_transactions=dataset.illicit_count,
        licit_transactions=dataset.licit_count,
        unknown_transactions=dataset.unknown_count,
        high_risk_transactions=high_risk,
        dataset_source=configured_source(),
        is_synthetic=dataset.is_synthetic,
        model_trained=predictor_status["trained"],
        model_name=predictor_status.get("model_name"),
        best_pr_auc=best_pr_auc,
        best_recall=best_recall,
        best_f1=best_f1,
        test_metrics=metrics.get("test_metrics") if metrics else None,
        prediction_history_count=prediction_count,
        last_trained_at=predictor_status.get("trained_at"),
        note=note,
    )


__all__ = ["get_dashboard_summary", "get_setting"]

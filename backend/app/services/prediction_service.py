"""Prediction orchestration with database history and batch CSV parsing."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.core.logging import log_event, mask_tx_id
from app.core.tx_validation import normalize_tx_id
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models import AnalysisHistory, Prediction
from app.schemas.prediction import BatchPredictionResponse, PredictionResponse
from ml.predict import get_predictor

from .data import (
    get_bundle,
    get_dataset,
    label_name,
    related_transactions,
    resolve_transaction,
)

ID_COLUMN_NAMES = {"txid", "tx_id", "transaction_id", "transactionid", "id", "tx"}


def parse_transaction_csv(content: str, *, max_rows: int = 5000) -> list[str]:
    """Extract transaction IDs from a CSV using a header-agnostic first column."""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)[: max_rows + 1]
    if not rows:
        return []
    header = [cell.strip().lower() for cell in rows[0]]
    start = 1 if any(name in ID_COLUMN_NAMES for name in header) else 0
    ids = []
    for row in rows[start:]:
        if not row or not row[0].strip():
            continue
        ids.append(normalize_tx_id(row[0].strip()))
        if len(ids) >= max_rows:
            break
    return ids


def _to_response(raw: dict[str, Any], *, related_count: int = 0) -> PredictionResponse:
    return PredictionResponse(
        transaction_id=raw["transaction_id"],
        predicted_class=raw["predicted_class"],
        risk_score=raw.get("risk_score"),
        confidence=float(raw.get("confidence") or 0.0),
        model_name=raw["model_name"],
        explanation=raw.get("explanation", []),
        warning=raw["warning"],
        ground_truth_label=raw.get("ground_truth_label", "unknown"),
        explanation_method=raw.get("explanation_method"),
        explanation_note=raw.get("explanation_note"),
        model_source=raw.get("model_source"),
        calibration=raw.get("calibration"),
        note=raw.get("note"),
        is_synthetic_data=bool(get_dataset().is_synthetic),
        is_synthetic_model_data=bool(raw.get("is_synthetic_model_data")),
        related_count=related_count,
    )


def _persist(result: PredictionResponse, *, source: str, batch_size: int = 1) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                Prediction(
                    tx_id=result.transaction_id,
                    predicted_class=result.predicted_class,
                    risk_score=result.risk_score,
                    confidence=result.confidence,
                    model_name=result.model_name,
                    explanation_json=json.dumps(result.explanation, default=str),
                    source=source,
                    batch_size=batch_size,
                )
            )
            db.add(
                AnalysisHistory(
                    action="predict",
                    tx_id=result.transaction_id,
                    details_json=json.dumps(
                        {
                            "predicted_class": result.predicted_class,
                            "model_name": result.model_name,
                            "is_synthetic": result.is_synthetic_data,
                        }
                    ),
                )
            )
            db.commit()
    except Exception as exc:  # pragma: no cover - history must not break predictions
        from app.core.logging import logger

        logger.warning("Could not persist prediction history: %s", exc)


def predict_transaction(
    tx_id: str,
    *,
    threshold: float | None = None,
    source: str = "single",
    persist: bool = True,
) -> tuple[PredictionResponse, bool]:
    """Return (response, found_in_dataset)."""
    resolved = resolve_transaction(tx_id)
    effective_threshold = threshold if threshold is not None else 0.5
    predictor = get_predictor()

    if resolved is None:
        raw = predictor.predict(
            transaction_id=normalize_tx_id(tx_id),
            matrix=np_empty_row(),
            feature_names=[],
            ground_truth="unknown",
            threshold=effective_threshold,
            include_explanation=False,
        )
        raw["note"] = (
            "Transaction is not present in the loaded dataset. Historical Elliptic IDs "
            "are not Bitcoin hashes; use the Web3 page for a live explorer lookup."
        )
        result = _to_response(raw)
        if persist:
            _persist(result, source=source)
        return result, False

    dataset = get_dataset()
    bundle = get_bundle()
    row = dataset.row_for(resolved)
    assert row is not None
    ground_truth = label_name(row["label"])
    raw = predictor.predict(
        transaction_id=resolved,
        matrix=bundle.matrix[int(row["feature_index"])],
        feature_names=bundle.names,
        ground_truth=ground_truth,
        threshold=effective_threshold,
    )
    raw["note"] = (
        "Synthetic demo data: predictions are for UI/testing only."
        if dataset.is_synthetic
        else None
    )
    result = _to_response(raw, related_count=len(related_transactions(resolved)))
    if persist:
        _persist(result, source=source)
    log_event("prediction", tx_id=mask_tx_id(resolved), result=result.predicted_class)
    return result, True


def np_empty_row():
    import numpy as np

    return np.zeros((1, 0), dtype=float)


def predict_batch(
    *,
    transaction_ids: list[str],
    csv_content: str | None = None,
    threshold: float | None = None,
) -> BatchPredictionResponse:
    ids = list(transaction_ids)
    if csv_content:
        ids.extend(parse_transaction_csv(csv_content))
    # Preserve order but remove duplicates.
    seen: set[str] = set()
    ids = [item for item in ids if not (item in seen or seen.add(item))]  # type: ignore[func-returns-value]

    results: list[PredictionResponse] = []
    errors: list[dict[str, str]] = []
    for tx_id in ids:
        try:
            result, found = predict_transaction(
                tx_id, threshold=threshold, source="batch", persist=False
            )
            if not found:
                errors.append({"transaction_id": tx_id, "error": "Not found in loaded dataset"})
            else:
                results.append(result)
                _persist(result, source="batch", batch_size=len(ids))
        except Exception as exc:  # pragma: no cover
            errors.append({"transaction_id": tx_id, "error": str(exc)})
    return BatchPredictionResponse(
        results=results,
        total=len(ids),
        succeeded=len(results),
        failed=len(errors),
        errors=errors,
    )


def record_history(action: str, tx_id: str | None = None, details: dict[str, Any] | None = None) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                AnalysisHistory(
                    action=action,
                    tx_id=tx_id,
                    details_json=json.dumps(details or {}, default=str),
                )
            )
            db.commit()
    except Exception:  # pragma: no cover
        pass

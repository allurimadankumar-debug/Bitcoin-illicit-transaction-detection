from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import get_settings
from app.core.logging import mask_tx_id
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import TransactionDetail, TransactionSummary
from ml.predict import get_predictor

from .data import (
    get_bundle,
    get_dataset,
    get_graph,
    get_risk_scores,
    high_risk_threshold,
    label_name,
    related_transactions,
    resolve_transaction,
    risk_status,
    transaction_features,
)
from .settings_service import get_setting

SORTABLE = {"transaction_id", "time_step", "risk_score", "label", "status"}


def _risk_predicted(score: float | None, threshold: float = 0.5) -> str:
    if score is None:
        return "unknown"
    return "illicit" if score >= threshold else "licit"


def _summaries() -> list[dict[str, Any]]:
    dataset = get_dataset()
    scores = get_risk_scores()
    graph = get_graph()
    threshold = high_risk_threshold()
    rows = []
    for position, (_, record) in enumerate(dataset.transactions.iterrows()):
        tx_id = str(record["tx_id"])
        score = float(scores[position]) if scores is not None else None
        rows.append(
            {
                "transaction_id": tx_id,
                "masked_transaction_id": mask_tx_id(tx_id),
                "time_step": int(record["time_step"]),
                "ground_truth_label": label_name(record["label"]),
                "predicted_class": _risk_predicted(score),
                "risk_score": round(score, 4) if score is not None else None,
                "status": (
                    "high-risk"
                    if score is not None and score >= threshold
                    else ("elevated" if score is not None and score >= 0.4 else "low-risk")
                )
                if score is not None
                else "unrated",
                "is_synthetic": dataset.is_synthetic,
                "in_degree": int(graph.in_degree(tx_id)) if tx_id in graph else 0,
                "out_degree": int(graph.out_degree(tx_id)) if tx_id in graph else 0,
            }
        )
    return rows


def list_transactions(
    *,
    search: str | None = None,
    label: str = "all",
    risk: str = "all",
    sort_by: str = "time_step",
    order: str = "desc",
    page: int = 1,
    page_size: int = 12,
    mask: bool | None = None,
) -> PaginatedResponse[TransactionSummary]:
    rows = _summaries()
    if search:
        query = search.lower()
        rows = [
            row
            for row in rows
            if query in row["transaction_id"].lower()
            or query == str(row["time_step"])
            or query in row["status"]
        ]
    if label != "all":
        if label.startswith("predicted_"):
            rows = [row for row in rows if row["predicted_class"] == label.replace("predicted_", "")]
        else:
            rows = [row for row in rows if row["ground_truth_label"] == label]
    if risk != "all":
        rows = [row for row in rows if row["status"] == risk]

    sort_by = sort_by if sort_by in SORTABLE else "time_step"
    reverse = order.lower() != "asc"
    rows.sort(
        key=lambda row: (
            row[sort_by] is None,
            row[sort_by] if row[sort_by] is not None else "",
        ),
        reverse=reverse,
    )

    total = len(rows)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    visible = rows[start : start + page_size]
    mask_ids = bool(get_setting("mask_ids_by_default", False)) if mask is None else mask
    if mask_ids:
        for row in visible:
            row["transaction_id"] = row["masked_transaction_id"]
    return PaginatedResponse(
        items=[TransactionSummary(**row) for row in visible],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def transaction_detail(tx_id: str) -> tuple[TransactionDetail, bool]:
    resolved = resolve_transaction(tx_id)
    if resolved is None:
        return (
            TransactionDetail(
                transaction_id=tx_id,
                masked_transaction_id=mask_tx_id(tx_id),
                dataset_source="not_found",
                is_synthetic=get_dataset().is_synthetic,
                time_step=0,
                ground_truth_label="unknown",
                predicted_class="unknown",
                note="Transaction not found in the loaded dataset.",
            ),
            False,
        )
    dataset = get_dataset()
    bundle = get_bundle()
    row = dataset.row_for(resolved)
    assert row is not None
    features, graph_features = transaction_features(resolved)
    related = related_transactions(resolved)
    score = (
        float(get_risk_scores()[int(row["feature_index"])])
        if get_risk_scores() is not None
        else None
    )
    predicted = _risk_predicted(score)
    predictor = get_predictor()
    explanation = []
    if predictor.available:
        raw = predictor.predict(
            transaction_id=resolved,
            matrix=bundle.matrix[int(row["feature_index"])],
            feature_names=bundle.names,
            ground_truth=label_name(row["label"]),
            include_explanation=True,
        )
        explanation = raw.get("explanation", [])

    indicators = []
    if score is not None and score >= high_risk_threshold():
        indicators.append("High illicit risk score from the trained model")
    if graph_features.get("graph_out_count", 0) >= 4:
        indicators.append("Elevated outgoing transaction count")
    if graph_features.get("graph_neighbor_illicit_ratio", 0) >= 0.5:
        indicators.append("Several known illicit neighbors in the local graph")
    if row["label"] != row["label"]:
        indicators.append("Ground-truth label is unknown (unlabeled transaction)")

    return (
        TransactionDetail(
            transaction_id=resolved,
            masked_transaction_id=mask_tx_id(resolved),
            dataset_source=dataset.source,
            is_synthetic=dataset.is_synthetic,
            time_step=int(row["time_step"]),
            ground_truth_label=label_name(row["label"]),
            predicted_class=predicted,
            risk_score=round(score, 4) if score is not None else None,
            confidence=round(max(score, 1 - score), 4) if score is not None else 0.0,
            model_name=str(predictor.status().get("model_name") or "untrained"),
            features=features[:40],
            graph_features=graph_features,
            related=related,
            related_count=len(related),
            risk_indicators=indicators,
            note=(
                "Synthetic demo transaction; not real blockchain data."
                if dataset.is_synthetic
                else None
            ),
        ),
        True,
    )


def explanation_for(tx_id: str) -> dict[str, Any]:
    resolved = resolve_transaction(tx_id)
    if resolved is None:
        return {"transaction_id": tx_id, "items": [], "message": "Transaction not found"}
    predictor = get_predictor()
    if not predictor.available:
        return {
            "transaction_id": resolved,
            "items": [],
            "message": predictor.status().get("message"),
        }
    dataset = get_dataset()
    bundle = get_bundle()
    row = dataset.row_for(resolved)
    assert row is not None
    raw = predictor.predict(
        transaction_id=resolved,
        matrix=bundle.matrix[int(row["feature_index"])],
        feature_names=bundle.names,
        ground_truth=label_name(row["label"]),
    )
    return {
        "transaction_id": resolved,
        "items": raw.get("explanation", []),
        "method": raw.get("explanation_method"),
        "note": raw.get("explanation_note"),
        "model_name": raw.get("model_name"),
        "risk_score": raw.get("risk_score"),
        "warning": "Explanations describe model behaviour, not proof of criminal intent.",
        "is_synthetic": dataset.is_synthetic,
    }

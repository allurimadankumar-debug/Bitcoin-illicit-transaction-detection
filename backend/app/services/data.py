"""Cached dataset, feature, graph and risk-score access used by all routes."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import networkx as nx
import numpy as np

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.core.tx_validation import normalize_tx_id
from ml.dataset import TransactionDataset, load_dataset
from ml.graph_features import GRAPH_FEATURE_NAMES, build_temporal_graph
from ml.predict import get_predictor
from ml.preprocessing import FeatureBundle, build_feature_bundle

from .settings_service import get_setting

HIGH_RISK_DEFAULT = 0.65


@lru_cache(maxsize=2)
def _cached_dataset(source: str) -> TransactionDataset:
    return load_dataset(source=source, settings=get_settings())


@lru_cache(maxsize=2)
def _cached_bundle(source: str) -> FeatureBundle:
    return build_feature_bundle(_cached_dataset(source))


@lru_cache(maxsize=2)
def _cached_graph(source: str) -> nx.DiGraph:
    return build_temporal_graph(_cached_dataset(source))


@lru_cache(maxsize=2)
def _cached_risk_scores(source: str) -> np.ndarray | None:
    dataset = _cached_dataset(source)
    bundle = _cached_bundle(source)
    predictor = get_predictor()
    scores = predictor.score_matrix(bundle.matrix, bundle.names)
    if scores is not None:
        logger.info("Computed risk scores for %d %s transactions", len(scores), source)
    return scores


def configured_source(settings: Settings | None = None) -> str:
    config = settings or get_settings()
    requested = config.dataset_source
    if requested != "auto":
        return requested
    return "demo" if _cached_dataset("auto").is_synthetic else "elliptic"


def get_dataset(settings: Settings | None = None) -> TransactionDataset:
    return _cached_dataset(configured_source(settings))


def get_bundle(settings: Settings | None = None) -> FeatureBundle:
    return _cached_bundle(configured_source(settings))


def get_graph(settings: Settings | None = None) -> nx.DiGraph:
    return _cached_graph(configured_source(settings))


def get_risk_scores(settings: Settings | None = None) -> np.ndarray | None:
    return _cached_risk_scores(configured_source(settings))


def refresh_caches() -> None:
    """Call after training so risk scores are recomputed against the new model."""
    get_predictor().reload()
    _cached_risk_scores.cache_clear()
    _cached_bundle.cache_clear()
    _cached_graph.cache_clear()


def high_risk_threshold() -> float:
    value = get_setting("high_risk_threshold", HIGH_RISK_DEFAULT)
    try:
        return float(value)
    except (TypeError, ValueError):  # pragma: no cover
        return HIGH_RISK_DEFAULT


def resolve_transaction(tx_id: str, settings: Settings | None = None) -> str | None:
    requested = normalize_tx_id(tx_id)
    dataset = get_dataset(settings)
    if requested in set(dataset.transactions["tx_id"]):
        return requested
    # Case-insensitive fallback for dataset identifiers.
    for candidate in dataset.transactions["tx_id"]:
        if str(candidate).lower() == requested.lower():
            return str(candidate)
    return None


def label_name(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "unknown"
    return "illicit" if int(value) == 1 else "licit"


def risk_score_for(tx_id: str, settings: Settings | None = None) -> float | None:
    dataset = get_dataset(settings)
    scores = get_risk_scores(settings)
    row = dataset.row_for(tx_id)
    if row is None or scores is None:
        return None
    return float(scores[int(row["feature_index"])])


def risk_status(tx_id: str, settings: Settings | None = None) -> str:
    dataset = get_dataset(settings)
    row = dataset.row_for(tx_id)
    if row is None:
        return "unavailable"
    score = risk_score_for(tx_id, settings)
    if score is None:
        return "unrated"
    if score >= high_risk_threshold():
        return "high-risk"
    if score >= 0.4:
        return "elevated"
    return "low-risk"


def transaction_features(tx_id: str, settings: Settings | None = None) -> tuple[list[dict[str, Any]], dict[str, float]]:
    dataset = get_dataset(settings)
    bundle = get_bundle(settings)
    row = dataset.row_for(tx_id)
    if row is None:
        return [], {}
    vector = bundle.matrix[int(row["feature_index"])]
    features = []
    graph_features: dict[str, float] = {}
    for name, value in zip(bundle.names, vector, strict=True):
        numeric = float(value)
        if name in GRAPH_FEATURE_NAMES:
            graph_features[name] = round(numeric, 6)
        if not np.isfinite(numeric):
            continue
        features.append(
            {
                "name": name,
                "value": round(numeric, 6),
                "category": "graph" if name in GRAPH_FEATURE_NAMES else "base",
            }
        )
    return features, graph_features


def related_transactions(tx_id: str, settings: Settings | None = None) -> list[dict[str, Any]]:
    graph = get_graph(settings)
    if tx_id not in graph:
        return []
    dataset = get_dataset(settings)
    results = []
    for direction, neighbors in (
        ("incoming", list(graph.predecessors(tx_id))),
        ("outgoing", list(graph.successors(tx_id))),
    ):
        for neighbor in neighbors[:20]:
            row = dataset.row_for(str(neighbor))
            results.append(
                {
                    "transaction_id": str(neighbor),
                    "direction": direction,
                    "ground_truth_label": label_name(None if row is None else row["label"]),
                    "risk_score": risk_score_for(str(neighbor), settings),
                }
            )
    return results

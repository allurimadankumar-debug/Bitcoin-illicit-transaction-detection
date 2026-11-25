"""Inference wrapper around the persisted model artifact."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np

from app.core.config import Settings, get_settings
from app.core.logging import logger

from .explain import explain_prediction
from .train import METRICS_FILE, MODEL_FILE

WARNING_TEXT = "Model prediction is not proof of criminal activity"


class ModelNotTrainedError(RuntimeError):
    """Raised when no persisted model artifact is available."""


def _probability(model: Any, X: np.ndarray) -> float:
    probabilities = model.predict_proba(X)
    classes = list(getattr(model, "classes_", []))
    if 1 in classes:
        return float(probabilities[0, classes.index(1)])
    return float(probabilities[0, -1])


class Predictor:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.path: Path = self.settings.models_path / MODEL_FILE
        self._bundle: Mapping[str, Any] | None = None

    @property
    def available(self) -> bool:
        return self.path.exists()

    def load(self) -> Mapping[str, Any]:
        if self._bundle is None:
            if not self.available:
                raise ModelNotTrainedError(
                    "No trained model found. Run `python backend/ml/train.py --source demo` "
                    "(or provide the Elliptic CSVs and run with --source elliptic)."
                )
            self._bundle = joblib.load(self.path)
            logger.info("Loaded model %s from %s", self._bundle.get("model_name"), self.path.name)
        return self._bundle

    def reload(self) -> None:
        self._bundle = None

    def status(self) -> dict[str, Any]:
        if not self.available:
            return {
                "trained": False,
                "model_name": None,
                "trained_at": None,
                "message": (
                    "Model not trained. Run `python backend/ml/train.py --source demo` "
                    "to train a demonstration model."
                ),
            }
        bundle = self.load()
        return {
            "trained": True,
            "model_name": bundle.get("model_name"),
            "trained_at": bundle.get("trained_at"),
            "calibration": bundle.get("calibration"),
            "dataset_source": bundle.get("dataset_source"),
            "is_synthetic": bundle.get("is_synthetic", False),
            "message": None,
        }

    def align_features(
        self,
        matrix: np.ndarray,
        feature_names: Sequence[str],
    ) -> tuple[np.ndarray, list[str], int]:
        """Reorder a feature matrix to match the persisted model's schema."""
        bundle = self.load()
        expected_names = list(bundle.get("feature_names", []))
        values = np.asarray(matrix, dtype=float)
        if values.ndim == 1:
            values = values.reshape(1, -1)
        aligned = np.zeros((values.shape[0], len(expected_names)), dtype=float)
        source_index = {name: index for index, name in enumerate(feature_names)}
        missing = 0
        for index, name in enumerate(expected_names):
            source_position = source_index.get(name)
            if source_position is None or source_position >= values.shape[1]:
                missing += 1
            else:
                aligned[:, index] = values[:, source_position]
        return aligned, expected_names, missing

    def score_matrix(
        self,
        matrix: np.ndarray,
        feature_names: Sequence[str],
        batch_size: int = 4096,
    ) -> np.ndarray | None:
        """Score many rows without computing explanations. None if untrained."""
        if not self.available:
            return None
        aligned, _, _ = self.align_features(matrix, feature_names)
        model = self.load()["model"]
        outputs = []
        for start in range(0, aligned.shape[0], batch_size):
            chunk = aligned[start : start + batch_size]
            probabilities = model.predict_proba(chunk)
            classes = list(getattr(model, "classes_", []))
            index = classes.index(1) if 1 in classes else -1
            outputs.append(probabilities[:, index])
        return np.concatenate(outputs) if outputs else np.array([], dtype=float)

    def predict(
        self,
        *,
        transaction_id: str,
        matrix: np.ndarray,
        feature_names: Sequence[str],
        ground_truth: str = "unknown",
        threshold: float = 0.5,
        include_explanation: bool = True,
    ) -> dict[str, Any]:
        """Predict one transaction; never invent a score when no model exists."""
        base: dict[str, Any] = {
            "transaction_id": transaction_id,
            "predicted_class": "unknown",
            "risk_score": None,
            "confidence": 0.0,
            "model_name": "untrained",
            "explanation": [],
            "warning": WARNING_TEXT,
            "ground_truth_label": ground_truth,
            "threshold": threshold,
            "model_source": None,
            "calibration": None,
            "explanation_method": None,
        }
        if not self.available:
            base["note"] = self.status()["message"]
            return base

        bundle = self.load()
        expected_names = list(bundle.get("feature_names", []))
        values = np.asarray(matrix, dtype=float).reshape(1, -1)
        aligned = np.zeros((1, len(expected_names)), dtype=float)
        source_index = {name: index for index, name in enumerate(feature_names)}
        missing = 0
        for index, name in enumerate(expected_names):
            source_position = source_index.get(name)
            if source_position is None or source_position >= values.shape[1]:
                missing += 1
            else:
                aligned[0, index] = values[0, source_position]

        probability = _probability(bundle["model"], aligned)
        predicted_class = "illicit" if probability >= threshold else "licit"
        explanation_payload: dict[str, Any] = {"items": [], "method": "unavailable"}
        if include_explanation:
            explanation_payload = explain_prediction(
                bundle,
                aligned[0],
                expected_names,
                importance_path=self.settings.models_path / "feature_importance.json",
            )

        base.update(
            {
                "predicted_class": predicted_class,
                "risk_score": round(probability, 6),
                "confidence": round(float(max(probability, 1.0 - probability)), 6),
                "model_name": str(bundle.get("model_name", "unknown")),
                "explanation": explanation_payload.get("items", []),
                "warning": WARNING_TEXT,
                "model_source": bundle.get("dataset_source"),
                "calibration": bundle.get("calibration"),
                "explanation_method": explanation_payload.get("method"),
                "explanation_note": explanation_payload.get("note"),
                "missing_features": missing,
                "is_synthetic_model_data": bool(bundle.get("is_synthetic", False)),
            }
        )
        return base


@lru_cache
def get_predictor(settings: Settings | None = None) -> Predictor:
    return Predictor(settings)


def metrics_available() -> bool:
    return (get_settings().models_path / METRICS_FILE).exists()

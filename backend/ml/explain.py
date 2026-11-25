"""Model explanations: SHAP when available, honest global-importance fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


def _base_estimator(model: Any) -> Any:
    if hasattr(model, "calibrated_classifiers_") and model.calibrated_classifiers_:
        candidate = getattr(model.calibrated_classifiers_[0], "estimator", None)
        if candidate is not None:
            return candidate
    return model


def _final_classifier(model: Any) -> Any:
    base = _base_estimator(model)
    if hasattr(base, "named_steps"):
        return base.named_steps["classifier"]
    return base


def explain_prediction(
    model_bundle: Mapping[str, Any],
    feature_values: np.ndarray,
    feature_names: Sequence[str],
    *,
    top_k: int = 6,
    importance_path: Path | None = None,
) -> dict[str, Any]:
    """Explain one prediction using SHAP or saved global feature importance."""
    values = np.asarray(feature_values, dtype=float).reshape(1, -1)
    frame = np.asarray(feature_values, dtype=float)
    result: dict[str, Any] = {
        "method": "unavailable",
        "items": [],
        "note": "Explanation could not be computed for this model.",
    }

    try:
        import shap  # type: ignore

        classifier = _final_classifier(model_bundle["model"])
        explainer = None
        tree_names = (
            "RandomForestClassifier",
            "HistGradientBoostingClassifier",
            "XGBClassifier",
            "DecisionTreeClassifier",
        )
        if type(classifier).__name__ in tree_names or hasattr(classifier, "estimators_"):
            explainer = shap.TreeExplainer(classifier)
            shap_values = explainer.shap_values(values, check_additivity=False)
        else:
            shap_values = None

        if explainer is not None and shap_values is not None:
            array = np.asarray(shap_values)
            if array.ndim == 3:
                # Tree ensembles can return one matrix per class.
                classes = list(getattr(classifier, "classes_", [0, 1]))
                illicit_index = classes.index(1) if 1 in classes else -1
                contributions = array[0, :, illicit_index]
            elif array.ndim == 2:
                contributions = array[0]
            else:
                contributions = array.reshape(-1)
            if contributions.shape[0] == len(feature_names):
                order = np.argsort(np.abs(contributions))[::-1][:top_k]
                result = {
                    "method": "shap_tree",
                    "items": [
                        {
                            "feature": feature_names[int(index)],
                            "value": round(float(frame[int(index)]), 6),
                            "impact": round(float(contributions[int(index)]), 6),
                            "direction": "increases_risk"
                            if contributions[int(index)] > 0
                            else "decreases_risk",
                        }
                        for index in order
                    ],
                    "note": "SHAP values describe this model's contribution to the score.",
                }
                return result
    except Exception as exc:  # pragma: no cover - SHAP is optional and version-sensitive
        result["note"] = f"SHAP unavailable ({type(exc).__name__}); using saved importance."

    if importance_path and importance_path.exists():
        try:
            payload = json.loads(importance_path.read_text(encoding="utf-8"))
            importance_by_feature = {
                item["feature"]: float(item["importance"])
                for item in payload.get("features", [])
            }
            order = sorted(
                feature_names,
                key=lambda name: abs(importance_by_feature.get(name, 0.0)),
                reverse=True,
            )[:top_k]
            result = {
                "method": "global_feature_importance",
                "items": [
                    {
                        "feature": name,
                        "value": round(float(feature_names_index(feature_names, name, frame)), 6),
                        "impact": round(importance_by_feature.get(name, 0.0), 6),
                        "direction": "global_influence",
                    }
                    for name in order
                ],
                "note": (
                    "Global feature importance shows what the model learned overall; "
                    "it is not a per-transaction SHAP attribution."
                ),
            }
        except Exception:  # pragma: no cover - corrupt artifact must not crash prediction
            pass
    return result


def feature_names_index(names: Sequence[str], name: str, values: np.ndarray) -> float:
    try:
        return float(values[list(names).index(name)])
    except (ValueError, IndexError):  # pragma: no cover
        return 0.0

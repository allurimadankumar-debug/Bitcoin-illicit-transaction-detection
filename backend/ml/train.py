"""Reproducible temporal training pipeline for illicit transaction detection."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np

# Allow `python backend/ml/train.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.logging import logger  # noqa: E402

from ml.dataset import (  # noqa: E402
    DatasetFormatError,
    DatasetNotFoundError,
    TransactionDataset,
    load_dataset,
)
from ml.evaluate import compute_metrics, save_evaluation_report, select_best_model  # noqa: E402
from ml.preprocessing import (  # noqa: E402
    FeatureBundle,
    build_feature_bundle,
    compute_class_weights,
    temporal_split,
)

MODEL_FILE = "model_bundle.joblib"
METRICS_FILE = "model_metrics.json"
IMPORTANCE_FILE = "feature_importance.json"


def _sklearn_pipeline(estimator: Any, *, scale: bool = False) -> Any:
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True))
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", estimator))
    return Pipeline(steps)


def build_model(
    name: str,
    *,
    class_weights: dict[int, float],
    random_state: int = 42,
) -> Any:
    """Construct one candidate model pipeline."""
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    if name == "logistic_regression":
        return _sklearn_pipeline(
            LogisticRegression(
                class_weight="balanced",
                max_iter=2500,
                C=0.6,
                random_state=random_state,
                solver="lbfgs",
            ),
            scale=True,
        )
    if name == "random_forest":
        return _sklearn_pipeline(
            RandomForestClassifier(
                n_estimators=140,
                max_depth=12,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                n_jobs=-1,
                random_state=random_state,
            )
        )
    if name == "hist_gradient_boosting":
        return _sklearn_pipeline(
            HistGradientBoostingClassifier(
                max_iter=180,
                learning_rate=0.07,
                max_leaf_nodes=15,
                l2_regularization=0.5,
                random_state=random_state,
            )
        )
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ValueError("XGBoost is not installed; use hist_gradient_boosting") from exc
        return _sklearn_pipeline(
            XGBClassifier(
                n_estimators=160,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.85,
                colsample_bytree=0.85,
                scale_pos_weight=class_weights.get(1, 1.0),
                eval_metric="logloss",
                n_jobs=-1,
                random_state=random_state,
            )
        )
    raise ValueError(f"Unknown model: {name}")


def candidate_model_names() -> list[str]:
    names = ["logistic_regression", "random_forest", "hist_gradient_boosting"]
    try:
        import xgboost  # noqa: F401

        names.append("xgboost")
    except ImportError:
        pass
    return names


def _fit_with_weights(model: Any, X: np.ndarray, y: np.ndarray, weights: np.ndarray) -> Any:
    """Fit a pipeline, applying sample weights only where the model supports it."""
    classifier = model.named_steps.get("classifier") if hasattr(model, "named_steps") else model
    accepts_weights = "HistGradientBoosting" in type(classifier).__name__ or "XGB" in type(
        classifier
    ).__name__
    if accepts_weights:
        try:
            return model.fit(X, y, classifier__sample_weight=weights)
        except (TypeError, ValueError):  # pragma: no cover - version differences
            pass
    return model.fit(X, y)


def _probability(model: Any, X: np.ndarray) -> np.ndarray:
    probabilities = model.predict_proba(X)
    classes = list(getattr(model, "classes_", []))
    if 1 in classes:
        return probabilities[:, classes.index(1)]
    # Calibrated estimators expose classes_ too; this is a defensive fallback.
    return probabilities[:, -1]


def extract_feature_importance(
    model: Any,
    feature_names: list[str],
    X_sample: np.ndarray,
    y_sample: np.ndarray,
) -> list[dict[str, Any]]:
    """Prefer native importances; fall back to permutation importance."""
    base = model
    if hasattr(model, "calibrated_classifiers_") and model.calibrated_classifiers_:
        candidate = getattr(model.calibrated_classifiers_[0], "estimator", None)
        if candidate is not None:
            base = candidate
    classifier = base.named_steps.get("classifier") if hasattr(base, "named_steps") else base

    values: np.ndarray | None = None
    if hasattr(classifier, "feature_importances_"):
        values = np.asarray(classifier.feature_importances_, dtype=float)
    elif hasattr(classifier, "coef_"):
        values = np.abs(np.asarray(classifier.coef_, dtype=float)).ravel()

    if values is None or len(values) != len(feature_names):
        from sklearn.inspection import permutation_importance

        result = permutation_importance(
            model,
            X_sample,
            y_sample,
            n_repeats=3,
            random_state=42,
            scoring="average_precision",
            n_jobs=1,
        )
        values = np.asarray(result.importances_mean, dtype=float)

    order = np.argsort(values)[::-1]
    return [
        {
            "feature": feature_names[index],
            "importance": float(values[index]),
            "rank": position + 1,
        }
        for position, index in enumerate(order)
    ]


def train(
    dataset: TransactionDataset,
    *,
    settings: Settings | None = None,
    include_graph_features: bool = True,
    calibrate: bool | None = None,
    oversampling: bool | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Train, compare and persist models. Returns the evaluation report.

    ``model_name`` optionally forces a specific trained candidate as the
    deployed model. When omitted, selection is fully automatic and uses
    validation PR-AUC, recall, then F1.
    """
    config = settings or get_settings()
    config.ensure_directories()
    should_calibrate = config.calibrate_model if calibrate is None else calibrate
    use_oversampling = config.use_oversampling if oversampling is None else oversampling

    bundle: FeatureBundle = build_feature_bundle(
        dataset, include_graph_features=include_graph_features
    )
    X = bundle.matrix
    y = dataset.transactions["label"].to_numpy(dtype=float)
    times = dataset.transactions["time_step"].to_numpy(dtype=float)
    split = temporal_split(
        times,
        y,
        train_fraction=config.train_fraction,
        validation_fraction=config.validation_fraction,
    )
    if min(len(split.train), len(split.validation), len(split.test)) < 2:
        raise ValueError(
            "Not enough labelled transactions across time periods to train and evaluate. "
            "Increase DEMO_TRANSACTIONS or provide the Elliptic dataset."
        )

    y_train = y[split.train].astype(int)
    y_validation = y[split.validation].astype(int)
    weights = compute_class_weights(y_train)
    weight_vector = np.array([weights[label] for label in y_train], dtype=float)
    X_train, X_validation = X[split.train], X[split.validation]

    if use_oversampling:
        try:
            from imblearn.over_sampling import RandomOverSampler

            sampler = RandomOverSampler(random_state=config.random_state)
            X_train, y_train = sampler.fit_resample(X_train, y_train)
            weight_vector = np.ones(len(y_train), dtype=float)
            logger.info("Applied random oversampling to the training fold only")
        except ImportError:  # pragma: no cover - optional dependency
            logger.warning("imbalanced-learn unavailable; using class weights instead")

    comparison: dict[str, dict[str, Any]] = {}
    fitted: dict[str, Any] = {}
    for name in candidate_model_names():
        try:
            model = build_model(
                name,
                class_weights=weights,
                random_state=config.random_state,
            )
            _fit_with_weights(model, X_train, y_train, weight_vector)
            validation_probability = _probability(model, X_validation)
            validation_prediction = (validation_probability >= 0.5).astype(int)
            comparison[name] = compute_metrics(
                y_validation, validation_prediction, validation_probability
            )
            fitted[name] = model
            logger.info(
                "Trained %s | val PR-AUC=%.3f recall=%.3f",
                name,
                comparison[name]["pr_auc"] or 0.0,
                comparison[name]["recall"],
            )
        except Exception as exc:  # pragma: no cover - one model must not stop the rest
            logger.warning("Skipping %s: %s", name, exc)

    if not comparison:
        raise RuntimeError("No candidate model could be trained.")

    # Model selection uses validation only. The test split stays untouched.
    # An explicit model may be requested for a reproducible demonstration;
    # the full comparison is still trained and reported honestly.
    if model_name and model_name != "auto":
        if model_name not in comparison:
            raise RuntimeError(
                f"Requested model '{model_name}' was not trained successfully. "
                f"Available models: {', '.join(sorted(comparison))}"
            )
        best_name = model_name
        selection_rule = (
            f"explicit model choice: {model_name}; full validation comparison retained"
        )
    else:
        best_name = select_best_model(comparison)
        selection_rule = "highest validation illicit PR-AUC, then recall, then F1"

    final_train = np.concatenate([split.train, split.validation])
    y_final = y[final_train].astype(int)
    final_weights = np.array(
        [compute_class_weights(y_final)[label] for label in y_final], dtype=float
    )
    X_final = X[final_train]
    if use_oversampling:
        sampler = RandomOverSampler(random_state=config.random_state)
        X_final, y_final = sampler.fit_resample(X_final, y_final)
        final_weights = np.ones(len(y_final), dtype=float)

    final_model = build_model(
        best_name, class_weights=weights, random_state=config.random_state
    )
    _fit_with_weights(final_model, X_final, y_final, final_weights)

    calibration_method = "none"
    if should_calibrate and len(y_final) >= 40 and len(np.unique(y_final)) == 2:
        try:
            from sklearn.calibration import CalibratedClassifierCV

            calibrated = CalibratedClassifierCV(
                estimator=final_model, method="sigmoid", cv=3
            )
            calibrated.fit(X_final, y_final)
            final_model = calibrated
            calibration_method = "sigmoid (3-fold, fitted on train+validation)"
        except Exception as exc:  # pragma: no cover - graceful fallback
            logger.warning("Calibration failed, using raw probabilities: %s", exc)

    X_test, y_test = X[split.test], y[split.test].astype(int)
    test_probability = _probability(final_model, X_test)
    test_prediction = (test_probability >= 0.5).astype(int)
    test_metrics = compute_metrics(y_test, test_prediction, test_probability)

    report = save_evaluation_report(
        config.reports_path,
        comparison=comparison,
        best_model=best_name,
        split_info={
            "method": "chronological (train < validation < test)",
            "train_rows": int(len(split.train)),
            "validation_rows": int(len(split.validation)),
            "test_rows": int(len(split.test)),
            "train_end_time": split.train_end_time,
            "validation_end_time": split.validation_end_time,
            "test_start_time": float(np.max(times[split.train]) + 1),
            "unlabeled_rows": int(len(split.unlabeled)),
            "oversampling": bool(use_oversampling),
            "calibration": calibration_method,
            "selection_basis": f"{selection_rule}; test metrics reported separately",
        },
        dataset_info={
            "source": dataset.source,
            "is_synthetic": dataset.is_synthetic,
            "transactions": dataset.size,
            "labeled": int(dataset.labeled_mask.sum()),
            "illicit": dataset.illicit_count,
            "licit": dataset.licit_count,
            "unknown": dataset.unknown_count,
            "base_features": bundle.base_feature_count,
            "graph_features": bundle.graph_feature_count,
        },
        selection_rule=selection_rule,
    )
    report["test_metrics"] = test_metrics
    (config.reports_path / "model_comparison.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )

    importance = extract_feature_importance(
        final_model, bundle.names, X_test[:200], y_test[:200]
    )
    bundle_artifact = {
        "model": final_model,
        "feature_names": bundle.names,
        "model_name": best_name,
        "calibration": calibration_method,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_source": dataset.source,
        "is_synthetic": dataset.is_synthetic,
        "feature_count": len(bundle.names),
        "test_metrics": test_metrics,
        "validation_comparison": comparison,
        "sklearn_version": _sklearn_version(),
    }
    joblib.dump(bundle_artifact, config.models_path / MODEL_FILE)
    (config.models_path / METRICS_FILE).write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    (config.models_path / IMPORTANCE_FILE).write_text(
        json.dumps(
            {
                "method": "native_importances_or_permutation",
                "features": importance,
                "model_name": best_name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(
        "Saved %s (%s) | test PR-AUC=%.3f recall=%.3f",
        MODEL_FILE,
        best_name,
        test_metrics["pr_auc"] or 0.0,
        test_metrics["recall"],
    )
    return report


def _sklearn_version() -> str:
    import sklearn

    return sklearn.__version__


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["auto", "elliptic", "demo"], default="auto")
    parser.add_argument(
        "--model",
        choices=["auto", "random_forest", "logistic_regression", "hist_gradient_boosting", "xgboost"],
        default="auto",
        help="Force a specific candidate as the deployed model; default selects by validation PR-AUC",
    )
    parser.add_argument("--no-graph", action="store_true")
    parser.add_argument("--no-calibrate", action="store_true")
    parser.add_argument("--oversampling", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    try:
        dataset = load_dataset(source=args.source, settings=settings)
        report = train(
            dataset,
            settings=settings,
            include_graph_features=not args.no_graph,
            calibrate=False if args.no_calibrate else None,
            oversampling=True if args.oversampling else None,
            model_name=None if args.model == "auto" else args.model,
        )
        print(f"Deployed model: {report['best_model']} ({report['selection_rule']})")
    except (DatasetNotFoundError, DatasetFormatError) as exc:
        raise SystemExit(f"Dataset error: {exc}") from exc
    except RuntimeError as exc:
        raise SystemExit(f"Training error: {exc}") from exc


if __name__ == "__main__":
    main()

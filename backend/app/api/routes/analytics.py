from fastapi import APIRouter, HTTPException, Query

from app.schemas.analytics import (
    ModelMetricsResponse,
    RiskDistributionResponse,
    TemporalResponse,
)
from app.services.analytics_service import (
    model_metrics,
    risk_distribution,
    temporal_analysis,
)

router = APIRouter(tags=["analytics"])


@router.get("/models/metrics", response_model=ModelMetricsResponse)
def get_model_metrics() -> ModelMetricsResponse:
    return model_metrics()


@router.get("/analytics/temporal", response_model=TemporalResponse)
def get_temporal(
    metric: str = Query("illicit_count", pattern="^(illicit_count|illicit_rate|volume)$"),
) -> TemporalResponse:
    return temporal_analysis(metric)


@router.get("/analytics/risk-distribution", response_model=RiskDistributionResponse)
def get_risk_distribution(
    bins: int = Query(10, ge=2, le=50),
) -> RiskDistributionResponse:
    return risk_distribution(bins)


@router.post("/models/train")
def train_model(
    source: str = Query("demo", pattern="^(auto|demo|elliptic)$"),
    model: str = Query(
        "auto",
        pattern="^(auto|random_forest|logistic_regression|hist_gradient_boosting|xgboost)$",
    ),
) -> dict:
    """Retrain the final model and refresh cached risk scores."""
    from app.core.config import get_settings
    from app.services.data import refresh_caches
    from ml.dataset import DatasetFormatError, DatasetNotFoundError, load_dataset
    from ml.train import train

    settings = get_settings()
    try:
        dataset = load_dataset(source=source, settings=settings)
        report = train(
            dataset,
            settings=settings,
            model_name=None if model == "auto" else model,
        )
    except (DatasetNotFoundError, DatasetFormatError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    refresh_caches()
    return {
        "status": "trained",
        "model_name": report.get("best_model"),
        "selection_rule": report.get("selection_rule"),
        "dataset_source": dataset.source,
        "is_synthetic": dataset.is_synthetic,
        "test_metrics": report.get("test_metrics", {}),
    }

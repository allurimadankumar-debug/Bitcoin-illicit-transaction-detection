from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse
from app.services.data import configured_source, get_dataset
from ml.predict import get_predictor

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    dataset = get_dataset()
    return HealthResponse(
        status="ok",
        version=get_settings().app_version,
        dataset_source=configured_source(),
        is_synthetic=dataset.is_synthetic,
        model_trained=get_predictor().available,
        timestamp=datetime.now(timezone.utc),
    )

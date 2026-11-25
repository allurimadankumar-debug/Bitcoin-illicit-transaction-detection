"""FastAPI application entry point."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import PROJECT_ROOT, get_settings, settings
from app.core.logging import log_event, logger
from app.db.session import SessionLocal, init_db
from app.models import ModelMetrics
from ml.predict import METRICS_FILE, get_predictor


def seed_model_metrics() -> None:
    path = settings.models_path / METRICS_FILE
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        with SessionLocal() as db:
            if db.query(ModelMetrics).count() > 0:
                return
            for name, metrics in payload.get("models", {}).items():
                db.add(
                    ModelMetrics(
                        model_name=name,
                        dataset_source=payload.get("dataset", {}).get("source", "unknown"),
                        split="temporal",
                        metrics_json=json.dumps(metrics),
                    )
                )
            db.commit()
    except Exception as exc:  # pragma: no cover - startup must remain resilient
        logger.warning("Could not seed model metrics: %s", exc)


def maybe_auto_train() -> None:
    """Train a small, clearly synthetic model so demo mode works immediately."""
    if get_predictor().available or not settings.auto_train_demo:
        return
    try:
        from ml.dataset import load_dataset
        from ml.train import train

        dataset = load_dataset(source="auto", settings=settings)
        if not dataset.is_synthetic:
            logger.info(
                "Real Elliptic data detected without a model. Skipping automatic training; "
                "run `python backend/ml/train.py --source elliptic`."
            )
            return
        logger.info("No model found; training a Random Forest demo model on synthetic data")
        train(dataset, settings=settings, model_name="random_forest")
        log_event("auto_train_complete", source=dataset.source)
    except Exception as exc:  # pragma: no cover
        logger.warning("Automatic demo training failed: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.ensure_directories()
    init_db()
    maybe_auto_train()
    seed_model_metrics()
    log_event("startup", version=settings.app_version, source=settings.dataset_source)
    yield
    log_event("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Academic decision-support API for machine-learning analysis of illicit "
        "Bitcoin transaction patterns. Predictions are not proof of criminal activity."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "detail": [
                {"location": item.get("loc"), "message": item.get("msg")}
                for item in exc.errors()
            ],
            "status_code": 422,
        },
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred. Check server logs.",
            "status_code": 500,
        },
    )


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "warning": "Academic decision support only; predictions are not proof of criminal activity.",
    }


# Serve the built frontend when present (production containers).
dist_dir: Path = PROJECT_ROOT / "frontend" / "dist"
if dist_dir.exists():  # pragma: no cover - only in production builds
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")


def get_app_settings():  # pragma: no cover - convenience for scripts
    return get_settings()

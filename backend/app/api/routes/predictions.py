from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.prediction_service import predict_batch, predict_transaction

router = APIRouter(prefix="/predict", tags=["predictions"])


@router.post("", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    result, found = predict_transaction(
        request.transaction_id, threshold=request.threshold
    )
    if not found:
        raise HTTPException(status_code=404, detail=result.note or "Transaction not found")
    return result


@router.post("/batch", response_model=BatchPredictionResponse)
def predict_batch_json(request: BatchPredictionRequest) -> BatchPredictionResponse:
    return predict_batch(
        transaction_ids=request.transaction_ids,
        csv_content=request.csv_content,
        threshold=request.threshold,
    )


@router.post("/batch/upload", response_model=BatchPredictionResponse)
async def predict_batch_upload(
    file: UploadFile = File(...),
    transaction_ids: str = Form(""),
    threshold: float = Form(0.5),
) -> BatchPredictionResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    content = (await file.read()).decode("utf-8-sig", errors="replace")
    ids = [item.strip() for item in transaction_ids.replace("\n", ",").split(",") if item.strip()]
    return predict_batch(
        transaction_ids=ids,
        csv_content=content,
        threshold=min(1.0, max(0.0, threshold)),
    )

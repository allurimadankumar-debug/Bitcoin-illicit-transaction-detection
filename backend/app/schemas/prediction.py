from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.tx_validation import validate_tx_id

WARNING = "Model prediction is not proof of criminal activity"


class ExplanationItem(BaseModel):
    feature: str
    value: float
    impact: float
    direction: str


class PredictionRequest(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=128)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("transaction_id")
    @classmethod
    def _validate(cls, value: str) -> str:
        try:
            return validate_tx_id(value)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc


class PredictionResponse(BaseModel):
    transaction_id: str
    predicted_class: str = Field(pattern="^(licit|illicit|unknown)$")
    risk_score: float | None = None
    confidence: float = 0.0
    model_name: str
    explanation: list[ExplanationItem] = Field(default_factory=list)
    warning: str = WARNING
    ground_truth_label: str = "unknown"
    explanation_method: str | None = None
    explanation_note: str | None = None
    model_source: str | None = None
    calibration: str | None = None
    note: str | None = None
    is_synthetic_data: bool = False
    is_synthetic_model_data: bool = False
    related_count: int = 0


class BatchPredictionRequest(BaseModel):
    transaction_ids: list[str] = Field(default_factory=list, max_length=5000)
    csv_content: str | None = Field(default=None, max_length=5_000_000)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("transaction_ids")
    @classmethod
    def _validate(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            try:
                cleaned.append(validate_tx_id(value))
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
        return cleaned


class BatchPredictionResponse(BaseModel):
    results: list[PredictionResponse]
    total: int
    succeeded: int
    failed: int
    errors: list[dict[str, str]] = Field(default_factory=list)
    warning: str = WARNING

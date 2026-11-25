from __future__ import annotations

from pydantic import BaseModel, Field

from .common import PaginatedResponse


class TransactionSummary(BaseModel):
    transaction_id: str
    masked_transaction_id: str
    time_step: int
    ground_truth_label: str
    predicted_class: str
    risk_score: float | None = None
    status: str
    is_synthetic: bool
    in_degree: int = 0
    out_degree: int = 0


TransactionPage = PaginatedResponse[TransactionSummary]


class FeatureValue(BaseModel):
    name: str
    value: float
    category: str = "base"


class RelatedTransaction(BaseModel):
    transaction_id: str
    direction: str
    ground_truth_label: str
    risk_score: float | None = None


class TransactionDetail(BaseModel):
    transaction_id: str
    masked_transaction_id: str
    dataset_source: str
    is_synthetic: bool
    time_step: int
    ground_truth_label: str
    predicted_class: str
    risk_score: float | None = None
    confidence: float = 0.0
    model_name: str = "untrained"
    warning: str = "Model prediction is not proof of criminal activity"
    features: list[FeatureValue] = Field(default_factory=list)
    graph_features: dict[str, float] = Field(default_factory=dict)
    related: list[RelatedTransaction] = Field(default_factory=list)
    related_count: int = 0
    risk_indicators: list[str] = Field(default_factory=list)
    note: str | None = None

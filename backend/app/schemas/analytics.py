from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_transactions: int
    labeled_transactions: int
    illicit_transactions: int
    licit_transactions: int
    unknown_transactions: int
    high_risk_transactions: int
    dataset_source: str
    is_synthetic: bool
    model_trained: bool
    model_name: str | None = None
    best_pr_auc: float | None = None
    best_recall: float | None = None
    best_f1: float | None = None
    test_metrics: dict[str, Any] | None = None
    prediction_history_count: int = 0
    last_trained_at: str | None = None
    note: str | None = None


class TemporalPoint(BaseModel):
    time_step: int
    total: int
    illicit: int
    licit: int
    unknown: int
    illicit_rate: float


class TemporalResponse(BaseModel):
    points: list[TemporalPoint]
    metric: str
    is_synthetic: bool


class RiskBucket(BaseModel):
    bucket: str
    count: int


class RiskDistributionResponse(BaseModel):
    bins: int
    buckets: list[RiskBucket]
    unrated: int
    is_synthetic: bool


class ModelMetricsResponse(BaseModel):
    available: bool
    best_model: str | None = None
    models: dict[str, dict[str, Any]] = Field(default_factory=dict)
    test_metrics: dict[str, Any] | None = None
    split: dict[str, Any] = Field(default_factory=dict)
    dataset: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None

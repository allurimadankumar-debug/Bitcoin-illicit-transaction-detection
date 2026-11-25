from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str
    version: str
    dataset_source: str
    is_synthetic: bool
    model_trained: bool
    timestamp: datetime


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None


class APIErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, le=100_000)
    page_size: int = Field(default=12, ge=1, le=200)

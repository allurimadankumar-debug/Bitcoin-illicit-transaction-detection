from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SettingsResponse(BaseModel):
    explorer_base_url: str
    enable_live_lookup: bool
    mask_ids_by_default: bool
    dataset_source: str
    version: str
    keys_required: list[str] = Field(default_factory=list)
    overrides: dict[str, Any] = Field(default_factory=dict)
    note: str


class SettingsUpdateRequest(BaseModel):
    mask_ids_by_default: bool | None = None
    explorer_base_url: str | None = Field(default=None, max_length=300)
    enable_live_lookup: bool | None = None
    table_page_size: int | None = Field(default=None, ge=5, le=100)
    high_risk_threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("explorer_base_url")
    @classmethod
    def _safe_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("Explorer URL must use HTTPS (or localhost for development)")
        return value.rstrip("/")

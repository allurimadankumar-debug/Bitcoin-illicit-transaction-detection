"""Central application configuration.

All paths are resolved from the project root so the app behaves the same
whether it is started from the repository root or from ``backend/``.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives at <root>/backend/app/core/config.py.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = PROJECT_ROOT / "backend"


def _resolve(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Bitcoin Illicit Transaction Detection"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///./data/app.db"
    data_dir: str = "./data"
    models_dir: str = "./models"
    reports_dir: str = "./reports"

    dataset_source: Literal["auto", "elliptic", "demo"] = "auto"
    demo_transactions: int = 360
    demo_time_steps: int = 40

    auto_train_demo: bool = True
    calibrate_model: bool = True
    random_state: int = 42
    train_fraction: float = 0.70
    validation_fraction: float = 0.15
    use_oversampling: bool = False

    mask_ids_by_default: bool = False
    enable_live_lookup: bool = False
    live_lookup_timeout: int = 8
    explorer_base_url: str = "https://blockstream.info/tx"
    explorer_api_base_url: str = "https://blockstream.info/api"

    @field_validator("train_fraction", "validation_fraction")
    @classmethod
    def _valid_fraction(cls, value: float) -> float:
        if not 0.0 < value < 1.0:
            raise ValueError("split fractions must be between 0 and 1")
        return value

    @property
    def data_path(self) -> Path:
        return _resolve(self.data_dir)

    @property
    def raw_data_path(self) -> Path:
        return self.data_path / "raw"

    @property
    def processed_data_path(self) -> Path:
        return self.data_path / "processed"

    @property
    def demo_data_path(self) -> Path:
        return self.processed_data_path / "demo"

    @property
    def models_path(self) -> Path:
        return _resolve(self.models_dir)

    @property
    def reports_path(self) -> Path:
        return _resolve(self.reports_dir)

    @property
    def sqlite_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            return self.data_path / "app.db"
        raw = self.database_url.replace("sqlite:///", "", 1)
        return _resolve(raw)

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            return f"sqlite:///{self.sqlite_path.as_posix()}"
        return self.database_url

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_directories(self) -> None:
        for path in (
            self.data_path,
            self.raw_data_path,
            self.processed_data_path,
            self.demo_data_path,
            self.models_path,
            self.reports_path,
            self.sqlite_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Read-only public configuration for the frontend settings page. Secrets such
# as API keys are deliberately never included.
PUBLIC_CONFIG = {
    "explorer_base_url": settings.explorer_base_url,
    "enable_live_lookup": settings.enable_live_lookup,
    "dataset_source": settings.dataset_source,
    "privacy_mode": settings.mask_ids_by_default,
    "version": settings.app_version,
    "keys_required": [],
}


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

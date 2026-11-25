"""Pytest configuration: isolated storage and deterministic demo data."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="bitcoin_detection_tests_"))
os.environ["DATA_DIR"] = str(_TMP / "data")
os.environ["MODELS_DIR"] = str(_TMP / "models")
os.environ["REPORTS_DIR"] = str(_TMP / "reports")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP / 'test.db'}"
os.environ["AUTO_TRAIN_DEMO"] = "true"
os.environ["CALIBRATE_MODEL"] = "false"
os.environ["DEMO_TRANSACTIONS"] = "180"
os.environ["DEMO_TIME_STEPS"] = "30"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def settings():
    from app.core.config import get_settings

    return get_settings()


@pytest.fixture(scope="session")
def demo_dataset(settings):
    from ml.dataset import load_dataset

    return load_dataset(source="demo", settings=settings)

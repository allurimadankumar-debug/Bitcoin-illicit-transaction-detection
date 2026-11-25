from __future__ import annotations

from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models import AnalysisHistory, AppSetting, Prediction, Transaction
from app.services.settings_service import get_setting, update_settings


def test_database_tables_roundtrip() -> None:
    with SessionLocal() as db:
        db.add(
            Transaction(
                id="TEST00000001",
                dataset_source="demo_synthetic",
                is_synthetic=1,
                time_step=1,
                label="unknown",
                feature_json="{}",
                graph_json="{}",
            )
        )
        db.commit()
        stored = db.get(Transaction, "TEST00000001")
        assert stored is not None and stored.is_synthetic == 1

        db.add(
            Prediction(
                tx_id="TEST00000001",
                predicted_class="illicit",
                risk_score=0.8,
                confidence=0.8,
                model_name="test_model",
                explanation_json="[]",
                source="single",
            )
        )
        db.add(
            AnalysisHistory(
                action="test", tx_id="TEST00000001", details_json="{}", created_at=utcnow()
            )
        )
        db.commit()
        assert db.query(Prediction).filter_by(tx_id="TEST00000001").count() == 1
        assert db.query(AnalysisHistory).filter_by(action="test").count() >= 1


def test_settings_are_persisted() -> None:
    update_settings({"table_page_size": 17})
    assert get_setting("table_page_size") == 17
    update_settings({"table_page_size": 12})


def test_secret_keys_are_never_stored() -> None:
    update_settings({"api_key": "super-secret", "private_key": "nope"})
    with SessionLocal() as db:
        assert db.get(AppSetting, "api_key") is None
        assert db.get(AppSetting, "private_key") is None

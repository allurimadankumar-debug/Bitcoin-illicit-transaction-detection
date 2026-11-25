"""Database-backed user preferences (never stores credentials)."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import PUBLIC_CONFIG, get_settings
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models import AppSetting

DEFAULTS: dict[str, Any] = {
    "mask_ids_by_default": PUBLIC_CONFIG["privacy_mode"],
    "explorer_base_url": PUBLIC_CONFIG["explorer_base_url"],
    "enable_live_lookup": PUBLIC_CONFIG["enable_live_lookup"],
    "table_page_size": 12,
    "high_risk_threshold": 0.65,
}

OVERRIDABLE_KEYS = set(DEFAULTS)


def get_setting(key: str, default: Any = None) -> Any:
    if key not in OVERRIDABLE_KEYS:
        return default
    try:
        with SessionLocal() as db:
            record = db.get(AppSetting, key)
            if record is None:
                return DEFAULTS.get(key, default)
            return json.loads(record.value_json)
    except SQLAlchemyError:
        return DEFAULTS.get(key, default)


def all_settings() -> dict[str, Any]:
    values = dict(DEFAULTS)
    try:
        with SessionLocal() as db:
            for record in db.query(AppSetting).all():
                if record.key in OVERRIDABLE_KEYS:
                    values[record.key] = json.loads(record.value_json)
    except SQLAlchemyError:
        pass
    return values


def update_settings(updates: dict[str, Any]) -> dict[str, Any]:
    clean = {key: value for key, value in updates.items() if value is not None and key in OVERRIDABLE_KEYS}
    try:
        with SessionLocal() as db:
            for key, value in clean.items():
                record = db.get(AppSetting, key)
                if record is None:
                    record = AppSetting(key=key, value_json="{}", updated_at=utcnow())
                    db.add(record)
                record.value_json = json.dumps(value)
                record.updated_at = utcnow()
            db.commit()
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Could not save settings: {exc}") from exc
    return all_settings()

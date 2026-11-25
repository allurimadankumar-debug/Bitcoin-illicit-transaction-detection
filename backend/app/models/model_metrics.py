from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ModelMetrics(Base, TimestampMixin):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_source: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    split: Mapped[str] = mapped_column(String(64), default="temporal", nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)

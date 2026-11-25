from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_tx_id", "tx_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tx_id: Mapped[str] = mapped_column(String(128), nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    explanation_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source: Mapped[str] = mapped_column(String(24), default="single", nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

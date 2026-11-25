from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_time_step", "time_step"),
        Index("ix_transactions_label", "label"),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dataset_source: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    is_synthetic: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    label: Mapped[str] = mapped_column(String(16), default="unknown", nullable=False)
    feature_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    graph_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    last_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_predicted_class: Mapped[str | None] = mapped_column(String(16), nullable=True)

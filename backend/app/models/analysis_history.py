from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AnalysisHistory(Base, TimestampMixin):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

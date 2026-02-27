from __future__ import annotations

from sqlalchemy import Integer, String, Float, text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base


class RiskAssessment(Base):
    """
    Versioned risk scoring output.
    scope_type/scope_id lets us score:
      - sample
      - location
      - zone (later)
    explanation_json keeps transparent auditability (why the score happened).
    """
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)  # "sample" | "location" | "zone"
    scope_id: Mapped[int] = mapped_column(Integer, nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    tier: Mapped[str] = mapped_column(String(16), nullable=False)  # green/yellow/orange/red

    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="rule_v1")
    explanation_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    computed_at: Mapped[str] = mapped_column(server_default=text("now()"))


Index("ix_risk_scope", RiskAssessment.scope_type, RiskAssessment.scope_id)
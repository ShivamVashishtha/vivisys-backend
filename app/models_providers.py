# app/models_providers.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class PatientProviderSelection(Base):
    __tablename__ = "patient_provider_selections"
    __table_args__ = (
        UniqueConstraint("patient_id", name="uq_patient_provider_selection_patient"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), index=True, nullable=False)

    provider_npi: Mapped[str] = mapped_column(String, index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String, nullable=False)
    provider_phone: Mapped[str | None] = mapped_column(String, nullable=True)

    taxonomy_desc: Mapped[str | None] = mapped_column(String, nullable=True)

    # Optional location context (handy later)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

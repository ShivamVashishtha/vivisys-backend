from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .db import Base


class PatientProviderSelection(Base):
    __tablename__ = "patient_provider_selections"

    id = Column(Integer, primary_key=True, index=True)

    # assumes you already have patients.id as the patient PK
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    # provider fields
    npi = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    taxonomy_desc = Column(String, nullable=True)
    telephone_number = Column(String, nullable=True)

    # address snapshot (optional but useful)
    line1 = Column(String, nullable=True)
    line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Optional relationship (only if your models.py defines Patient)
    patient = relationship("Patient", backref="provider_selection", uselist=False)

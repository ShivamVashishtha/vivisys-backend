from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .db import Base

class PatientHospitalSelection(Base):
    __tablename__ = "patient_hospital_selection"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True, unique=True)

    # CMS/NPPES fields
    hospital_npi = Column(String, nullable=False, index=True)
    hospital_name = Column(String, nullable=False)
    hospital_phone = Column(String, nullable=True)

    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    taxonomy_desc = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_id", name="uq_patient_hospital_selection_patient_id"),
    )

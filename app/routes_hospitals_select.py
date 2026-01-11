from __future__ import annotations

from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
import uuid

from .db import get_db
from .models_hospitals import PatientHospitalSelection

# Use your existing auth dependency that returns current user
# (adjust import name if yours differs)
from .routes_auth import get_current_user  # must exist in your project
from .crud import get_patient_by_user_id  # must exist in your project

router = APIRouter(prefix="/patients/me", tags=["hospitals"])


class HospitalSelectionIn(BaseModel):
    npi: str = Field(..., min_length=5)
    name: str = Field(..., min_length=2)
    telephone_number: Optional[str] = None

    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    taxonomy_desc: Optional[str] = None


class HospitalSelectionOut(BaseModel):
    hospital_npi: str
    hospital_name: str
    hospital_phone: Optional[str] = None

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    taxonomy_desc: Optional[str] = None


@router.get("/hospital", response_model=Optional[HospitalSelectionOut])
def get_my_selected_hospital(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        return None

    row = db.query(PatientHospitalSelection).filter(PatientHospitalSelection.patient_id == patient.id).first()
    if not row:
        return None

    return HospitalSelectionOut(
        hospital_npi=row.hospital_npi,
        hospital_name=row.hospital_name,
        hospital_phone=row.hospital_phone,
        address_line1=row.address_line1,
        address_line2=row.address_line2,
        city=row.city,
        state=row.state,
        postal_code=row.postal_code,
        taxonomy_desc=row.taxonomy_desc,
    )


@router.post("/hospital", response_model=HospitalSelectionOut)
def set_my_selected_hospital(
    payload: HospitalSelectionIn,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        raise HTTPException(status_code=400, detail="Patient profile not found. Please self-register first.")

    row = db.query(PatientHospitalSelection).filter(PatientHospitalSelection.patient_id == patient.id).first()

    if not row:
        row = PatientHospitalSelection(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            hospital_npi=payload.npi,
            hospital_name=payload.name,
            hospital_phone=payload.telephone_number,
            address_line1=payload.line1,
            address_line2=payload.line2,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            taxonomy_desc=payload.taxonomy_desc,
        )
        db.add(row)
    else:
        row.hospital_npi = payload.npi
        row.hospital_name = payload.name
        row.hospital_phone = payload.telephone_number
        row.address_line1 = payload.line1
        row.address_line2 = payload.line2
        row.city = payload.city
        row.state = payload.state
        row.postal_code = payload.postal_code
        row.taxonomy_desc = payload.taxonomy_desc

    db.commit()
    db.refresh(row)

    return HospitalSelectionOut(
        hospital_npi=row.hospital_npi,
        hospital_name=row.hospital_name,
        hospital_phone=row.hospital_phone,
        address_line1=row.address_line1,
        address_line2=row.address_line2,
        city=row.city,
        state=row.state,
        postal_code=row.postal_code,
        taxonomy_desc=row.taxonomy_desc,
    )

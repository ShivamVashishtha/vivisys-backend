# app/routes_providers_select.py
from __future__ import annotations

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from .db import get_db
from .deps import get_current_user
from .crud import get_patient_by_user_id
from .models_providers import PatientProviderSelection

router = APIRouter(prefix="/patients/me", tags=["providers"])


class ProviderSelectionIn(BaseModel):
    npi: str = Field(..., min_length=5)
    name: str = Field(..., min_length=2)

    telephone_number: Optional[str] = None
    taxonomy_desc: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class ProviderSelectionOut(BaseModel):
    provider_npi: str
    provider_name: str
    provider_phone: Optional[str] = None
    taxonomy_desc: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


@router.get("/provider", response_model=Optional[ProviderSelectionOut])
def get_my_selected_provider(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        return None

    row = (
        db.query(PatientProviderSelection)
        .filter(PatientProviderSelection.patient_id == patient.id)
        .first()
    )
    if not row:
        return None

    return ProviderSelectionOut(
        provider_npi=row.provider_npi,
        provider_name=row.provider_name,
        provider_phone=row.provider_phone,
        taxonomy_desc=row.taxonomy_desc,
        city=row.city,
        state=row.state,
        postal_code=row.postal_code,
    )


@router.post("/provider", response_model=ProviderSelectionOut)
def set_my_selected_provider(
    payload: ProviderSelectionIn,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        raise HTTPException(status_code=400, detail="Patient profile not found. Please self-register first.")

    row = (
        db.query(PatientProviderSelection)
        .filter(PatientProviderSelection.patient_id == patient.id)
        .first()
    )

    if not row:
        row = PatientProviderSelection(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            provider_npi=payload.npi,
            provider_name=payload.name,
            provider_phone=payload.telephone_number,
            taxonomy_desc=payload.taxonomy_desc,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
        )
        db.add(row)
    else:
        row.provider_npi = payload.npi
        row.provider_name = payload.name
        row.provider_phone = payload.telephone_number
        row.taxonomy_desc = payload.taxonomy_desc
        row.city = payload.city
        row.state = payload.state
        row.postal_code = payload.postal_code

    db.commit()
    db.refresh(row)

    return ProviderSelectionOut(
        provider_npi=row.provider_npi,
        provider_name=row.provider_name,
        provider_phone=row.provider_phone,
        taxonomy_desc=row.taxonomy_desc,
        city=row.city,
        state=row.state,
        postal_code=row.postal_code,
    )


@router.delete("/provider")
def clear_my_selected_provider(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        return {"status": "ok"}

    row = (
        db.query(PatientProviderSelection)
        .filter(PatientProviderSelection.patient_id == patient.id)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()

    return {"status": "ok"}

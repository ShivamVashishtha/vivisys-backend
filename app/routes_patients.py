from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .deps import get_current_user
from .models import RecordPointer
from .schemas import CreatePatientIn, PatientOut, CreatePointerIn
from . import crud
from datetime import date as date_type
from .schemas import PatientSelfRegisterIn
from .models import Patient, generate_public_patient_id



router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut)
def create_patient(
    _: CreatePatientIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if user.role != "guardian":
        raise HTTPException(status_code=403, detail="Only guardians can create patients")
    p = crud.create_patient(db, user.id)
    return PatientOut(id=p.id, public_id=p.public_id, guardian_user_id=p.guardian_user_id, created_at=p.created_at)


@router.post("/self/register", response_model=PatientOut)
def self_register_patient(
    data: PatientSelfRegisterIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patient users can self-register")

    # Age check
    from datetime import date as d
    today = d.today()
    dob = data.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 18:
        raise HTTPException(status_code=403, detail="Must be 18+ for self access")

    existing = crud.get_patient_by_user_id(db, user.id)
    if existing:
        return PatientOut(
            id=existing.id,
            public_id=existing.public_id,
            guardian_user_id=existing.guardian_user_id or "",
            created_at=existing.created_at,
        )

    # Create new patient profile linked to this user
    for _ in range(10):
        public_id = generate_public_patient_id()
        if not db.query(Patient).filter(Patient.public_id == public_id).first():
            p = Patient(
                public_id=public_id,
                guardian_user_id=None,
                user_id=user.id,
                date_of_birth=dob,
            )
            db.add(p)
            db.commit()
            db.refresh(p)

            crud.log(db, actor_user_id=user.id, patient_id=p.id, action="PATIENT_SELF_REGISTER",
                     details=f"public_id={p.public_id}")
            return PatientOut(id=p.id, public_id=p.public_id, guardian_user_id="", created_at=p.created_at)

    raise HTTPException(status_code=500, detail="Failed to generate public patient id")


@router.post("/{patient_identifier}/pointers")
def add_pointer(
    patient_identifier: str,
    data: CreatePointerIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # For MVP: allow guardian to register pointers. In real life, issuer/hospital would.
    p = crud.get_patient_by_identifier(db, patient_identifier)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    if user.role != "guardian" or p.guardian_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    pointer = RecordPointer(
        patient_id=p.id,
        record_type=data.record_type,
        fhir_base_url=data.fhir_base_url,
        fhir_resource_type=data.fhir_resource_type,
        fhir_resource_id=data.fhir_resource_id,
        issuer=data.issuer,
    )
    crud.add_pointer(db, p.id, pointer)
    crud.log(db, actor_user_id=user.id, patient_id=p.id, action="POINTER_ADD",
             details=f"{data.record_type}:{data.fhir_resource_type}/{data.fhir_resource_id}")
    return {"status": "ok", "pointer_id": pointer.id, "patient_id": p.id, "patient_public_id": p.public_id}

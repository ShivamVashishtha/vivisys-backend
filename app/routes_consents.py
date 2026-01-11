# app/routes_consents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .db import get_db
from .deps import get_current_user
from .schemas import ConsentIn, ConsentOut, ConsentListOut
from . import crud
from .models import Patient

router = APIRouter(prefix="/consents", tags=["consents"])

ALLOWED_SCOPES = {"immunizations", "allergies", "conditions", "all"}


def _ensure_patient_owner(db: Session, user, patient_identifier: str) -> Patient:
    """
    Guardian: must own patient via guardian_user_id
    Patient: must be linked via user_id
    """
    p = crud.get_patient_by_identifier(db, patient_identifier)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    if user.role == "guardian":
        if p.guardian_user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        return p

    if user.role == "patient":
        if p.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        return p

    raise HTTPException(status_code=403, detail="Not allowed")


@router.post("/patients/{patient_identifier}")
def grant_consent(
    patient_identifier: str,
    data: ConsentIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Guardian or Patient can grant consent for their patient/self
    p = _ensure_patient_owner(db, user, patient_identifier)

    grantee = crud.get_user_by_email(db, data.grantee_email)
    if not grantee or grantee.role != "doctor":
        raise HTTPException(status_code=400, detail="Grantee must be an existing doctor user")

    now = datetime.now(timezone.utc)
    expires_at = data.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise HTTPException(status_code=400, detail="expires_at must be in the future")

    scope = crud.normalize_scope(data.scope)

    # ✅ allow "all"
    if scope not in ALLOWED_SCOPES:
        raise HTTPException(status_code=400, detail="Invalid scope")

    c = crud.grant_consent(db, p.id, grantee.id, scope, expires_at)

    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="CONSENT_GRANT",
        details=f"to={grantee.email} scope={scope} exp={expires_at.isoformat()} patient_public_id={p.public_id}",
    )

    return {"status": "ok", "consent_id": c.id, "patient_id": p.id, "patient_public_id": p.public_id}


@router.get("/patients/{patient_identifier}", response_model=ConsentListOut)
def list_patient_consents(
    patient_identifier: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Guardian/patient can list for owned patient
    p = _ensure_patient_owner(db, user, patient_identifier)

    rows = crud.list_consents_for_patient(db, p.id)
    consents = [
        ConsentOut(
            id=c.id,
            patient_id=p.id,
            patient_public_id=p.public_id,
            grantee_email=u.email,
            scope=c.scope,
            expires_at=c.expires_at,
            revoked=c.revoked,
            created_at=c.created_at,
        )
        for (c, u) in rows
    ]

    return ConsentListOut(patient_id=p.id, patient_public_id=p.public_id, consents=consents)


@router.get("/me", response_model=ConsentListOut)
def list_my_consents(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Patient convenience endpoint
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can call /consents/me")

    p = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient profile not found. Call POST /patients/self/register.")

    rows = crud.list_consents_for_patient(db, p.id)
    consents = [
        ConsentOut(
            id=c.id,
            patient_id=p.id,
            patient_public_id=p.public_id,
            grantee_email=u.email,
            scope=c.scope,
            expires_at=c.expires_at,
            revoked=c.revoked,
            created_at=c.created_at,
        )
        for (c, u) in rows
    ]

    return ConsentListOut(patient_id=p.id, patient_public_id=p.public_id, consents=consents)


@router.post("/{consent_id}/revoke")
def revoke_consent(
    consent_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    c = db.query(crud.ConsentGrant).filter(crud.ConsentGrant.id == consent_id).first()  # type: ignore
    if not c:
        raise HTTPException(status_code=404, detail="Consent not found")

    p = db.query(Patient).filter(Patient.id == c.patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Guardian can revoke if owns patient; Patient can revoke if self-linked
    if user.role == "guardian":
        if p.guardian_user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    elif user.role == "patient":
        if p.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        raise HTTPException(status_code=403, detail="Not allowed")

    if c.revoked:
        return {"status": "ok", "consent_id": c.id, "already_revoked": True}

    c.revoked = True
    db.commit()

    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="CONSENT_REVOKE",
        details=f"consent_id={c.id} patient_public_id={p.public_id}",
    )

    return {"status": "ok", "consent_id": c.id}

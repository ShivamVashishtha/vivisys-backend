from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .deps import get_current_user
from .models import RecordPointer, Patient
from . import crud
from .fhir_client import fetch_fhir_resource
from .schemas import SelfPointerIn, SelfPointerOut
from .schemas import CatalogCreateIn, CatalogCreateOut
import httpx
from datetime import datetime, timezone

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/patients/{patient_identifier}")
async def get_records(
    patient_identifier: str,
    scope: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view records")

    p = crud.get_patient_by_identifier(db, patient_identifier)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if not crud.has_valid_consent(db, p.id, user.id, scope, now):
        raise HTTPException(status_code=403, detail="No valid consent for this scope")

    scope_to_type = {
        "immunizations": "immunization",
        "allergies": "allergy",
        "conditions": "condition",
    }
    if scope not in scope_to_type:
        raise HTTPException(status_code=400, detail="Invalid scope")

    record_type = scope_to_type[scope]

    pointers = (
        db.query(RecordPointer)
        .filter(RecordPointer.patient_id == p.id)
        .filter(RecordPointer.record_type == record_type)
        .all()
    )

    results = []
    for ptr in pointers:
        resource = await fetch_fhir_resource(
            ptr.fhir_base_url, ptr.fhir_resource_type, ptr.fhir_resource_id
        )
        results.append({
            "issuer": ptr.issuer,
            "pointer_id": ptr.id,
            "resource": resource,
            "missing": bool(resource.get("_error")),
    })


    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="RECORD_VIEW",
        details=f"scope={scope} count={len(results)} patient_public_id={p.public_id}",
    )

    return {
        "patient_id": p.id,
        "patient_public_id": p.public_id,
        "scope": scope,
        "count": len(results),
        "records": results,
    }


@router.get("/me")
async def get_my_records(
    scope: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Patient self-access endpoint (18+).
    Patient must have a linked Patient row: patients.user_id == current user.id.
    No consent check is required because this is self-access.
    """
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can view /records/me")

    p = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found. Call POST /patients/self/register first.",
        )

    scope = crud.normalize_scope(scope)

    scope_to_type = {
        "immunizations": "immunization",
        "allergies": "allergy",
        "conditions": "condition",
    }

    if scope not in scope_to_type:
        raise HTTPException(status_code=400, detail="Invalid scope")

    record_type = scope_to_type[scope]

    pointers = (
        db.query(RecordPointer)
        .filter(RecordPointer.patient_id == p.id)
        .filter(RecordPointer.record_type == record_type)
        .all()
    )

    results = []
    for ptr in pointers:
        resource = await fetch_fhir_resource(
            ptr.fhir_base_url, ptr.fhir_resource_type, ptr.fhir_resource_id
        )
        results.append({
            "issuer": ptr.issuer,
            "pointer_id": ptr.id,
            "resource": resource,
            "missing": bool(resource.get("_error")),
    })


    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="PATIENT_RECORD_VIEW",
        details=f"scope={scope} count={len(results)} patient_public_id={p.public_id}",
    )

    return {
        "patient_id": p.id,
        "patient_public_id": p.public_id,
        "scope": scope,
        "count": len(results),
        "records": results,
    }

@router.post("/me/pointers", response_model=SelfPointerOut)
def add_my_pointer(
    data: SelfPointerIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can add their own pointers")

    p = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient profile not found. Call POST /patients/self/register.")

    scope_to_pointer = {
        "immunizations": ("immunization", "Immunization"),
        "allergies": ("allergy", "AllergyIntolerance"),
        "conditions": ("condition", "Condition"),
    }

    if scope not in scope_to_pointer:
        raise HTTPException(status_code=400, detail="Invalid scope")

    record_type, fhir_resource_type = scope_to_pointer[scope]


    fhir_id = (data.fhir_resource_id or "").strip()
    if not fhir_id:
        raise HTTPException(status_code=400, detail="fhir_resource_id is required")

    ptr = crud.create_pointer_for_patient(
        db,
        patient_id=p.id,
        record_type=record_type,
        fhir_base_url="http://localhost:8080/fhir",
        fhir_resource_type=fhir_resource_type,
        fhir_resource_id=fhir_id,
        issuer=(data.issuer or "Self (Patient)"),
    )

    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="POINTER_CREATE_SELF",
        details=f"scope={scope} fhir={fhir_resource_type}/{fhir_id} issuer={data.issuer or 'Self (Patient)'} patient_public_id={p.public_id}",
    )

    return {"status": "ok", "pointer_id": ptr.id, "record_type": ptr.record_type}

@router.post("/me/catalog/create", response_model=CatalogCreateOut)
async def create_from_catalog_and_link(
    data: CatalogCreateIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    if user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can create and link their records")

    p = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient profile not found. Call POST /patients/self/register.")
    
    scope = crud.normalize_scope(data.scope)
    
    scope_map = {
        "immunizations": ("immunization", "Immunization"),
        "conditions": ("condition", "Condition"),
        "allergies": ("allergy", "AllergyIntolerance"),
    }
    if scope not in scope_map:
        raise HTTPException(status_code=400, detail="Invalid scope")
    record_type, fhir_type = scope_map[scope]

    issuer = (data.issuer or "Self (Patient)").strip()
    display = data.display.strip()
    if not display:
        raise HTTPException(status_code=400, detail="display is required")

    base_url = "http://localhost:8080/fhir"

    # Minimal FHIR resource bodies for demo
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if fhir_type == "Immunization":
        payload = {
            "resourceType": "Immunization",
            "status": "completed",
            "vaccineCode": {"text": display},
            "occurrenceDateTime": now_iso,
        }
    elif fhir_type == "Condition":
        payload = {
            "resourceType": "Condition",
            "clinicalStatus": {"text": "active"},
            "code": {"text": display},
            "recordedDate": now_iso,
        }
    else:  # AllergyIntolerance
        payload = {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"text": "active"},
            "code": {"text": display},
            "recordedDate": now_iso,
        }

    # Create on HAPI FHIR
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{base_url}/{fhir_type}",
            json=payload,
            headers={"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"},
        )

    r.raise_for_status()

    # HAPI returns created resource; ID is usually in the body or Location header
    body = r.json()
    created_id = body.get("id")

    if not created_id:
        loc = r.headers.get("location") or r.headers.get("Location") or ""
        # e.g. http://localhost:8080/fhir/Immunization/123/_history/1
        parts = loc.split("/")
        if fhir_type in parts:
            idx = parts.index(fhir_type)
            if idx + 1 < len(parts):
                created_id = parts[idx + 1]

    if not created_id:
        raise HTTPException(status_code=500, detail="FHIR resource created but id could not be determined")

    ptr = crud.create_pointer_for_patient(
        db,
        patient_id=p.id,
        record_type=record_type,
        fhir_base_url=base_url,
        fhir_resource_type=fhir_type,
        fhir_resource_id=created_id,
        issuer=issuer,
    )

    crud.log(
        db,
        actor_user_id=user.id,
        patient_id=p.id,
        action="FHIR_CREATE_AND_POINTER",
        details=f"scope={scope} display={display} fhir={fhir_type}/{created_id} patient_public_id={p.public_id}",
    )

    return {
        "status": "ok",
        "fhir_resource_type": fhir_type,
        "fhir_resource_id": created_id,
        "pointer_id": ptr.id,
    }

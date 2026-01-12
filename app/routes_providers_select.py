from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from .crud import get_provider_selection, upsert_provider_selection, clear_provider_selection

# IMPORTANT: match whatever your hospital selection routes use.
# Your earlier error was importing get_current_user from routes_auth.
# Your project already uses deps_auth in working routes.
from .deps import get_current_user
from .crud import get_patient_by_user_id  # this should already exist in your crud.py


router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderSelectIn(BaseModel):
    npi: str
    name: str
    taxonomy_desc: str | None = None
    telephone_number: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None


@router.get("/me")
def get_my_provider(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        return {"selected": None}

    row = get_provider_selection(db, patient.id)
    if not row:
        return {"selected": None}

    return {
        "selected": {
            "npi": row.npi,
            "name": row.name,
            "taxonomy_desc": row.taxonomy_desc,
            "telephone_number": row.telephone_number,
            "line1": row.line1,
            "line2": row.line2,
            "city": row.city,
            "state": row.state,
            "postal_code": row.postal_code,
        }
    }


@router.post("/me/select")
def set_my_provider(
    payload: ProviderSelectIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        # if you prefer raising HTTPException, do it. keeping minimal.
        return {"status": "error", "message": "patient profile not found"}

    row = upsert_provider_selection(
        db,
        patient.id,
        npi=payload.npi,
        name=payload.name,
        taxonomy_desc=payload.taxonomy_desc,
        telephone_number=payload.telephone_number,
        line1=payload.line1,
        line2=payload.line2,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
    )
    return {"status": "ok", "selected": {"npi": row.npi, "name": row.name}}


@router.post("/me/clear")
def clear_my_provider(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    patient = get_patient_by_user_id(db, user.id)
    if not patient:
        return {"status": "ok", "cleared": False}

    cleared = clear_provider_selection(db, patient.id)
    return {"status": "ok", "cleared": cleared}

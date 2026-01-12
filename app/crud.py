# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from .models_providers_select import PatientProviderSelection
from .models import User, Patient, ConsentGrant, RecordPointer, AuditLog, generate_public_patient_id
from .auth import hash_password, verify_password


def normalize_scope(scope: str) -> str:
    """
    Normalize scope strings and aliases.
    Supports:
      - immunizations, allergies, conditions
      - all (wildcard)
    """
    s = (scope or "").strip().lower()
    aliases = {
        "immunization": "immunizations",
        "immunizations": "immunizations",
        "allergy": "allergies",
        "allergies": "allergies",
        "condition": "conditions",
        "conditions": "conditions",
        "all": "all",
        "*": "all",
    }
    return aliases.get(s, s)


def log(db: Session, actor_user_id: str, patient_id: str, action: str, details: str = ""):
    db.add(AuditLog(actor_user_id=actor_user_id, patient_id=patient_id, action=action, details=details))
    db.commit()


def create_user(db: Session, email: str, password: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(AuditLog(actor_user_id=user.id, patient_id="", action="REGISTER", details=email))
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    db.add(AuditLog(actor_user_id=user.id, patient_id="", action="LOGIN", details=email))
    db.commit()
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_patient_by_identifier(db: Session, identifier: str) -> Patient | None:
    """
    Accept either internal UUID (patients.id) or human readable patients.public_id.
    """
    p = db.get(Patient, identifier)
    if p:
        return p
    return db.query(Patient).filter(Patient.public_id == identifier).first()


def create_patient(db: Session, guardian_user_id: str) -> Patient:
    # Generate a unique public_id. Retry a few times on collision.
    for _ in range(10):
        public_id = generate_public_patient_id()
        exists = db.query(Patient).filter(Patient.public_id == public_id).first()
        if not exists:
            p = Patient(guardian_user_id=guardian_user_id, public_id=public_id)
            db.add(p)
            db.commit()
            db.refresh(p)
            db.add(
                AuditLog(
                    actor_user_id=guardian_user_id,
                    patient_id=p.id,
                    action="PATIENT_CREATE",
                    details=f"public_id={p.public_id}",
                )
            )
            db.commit()
            return p

    raise RuntimeError("Failed to generate a unique public patient id")


def add_pointer(db: Session, patient_id: str, pointer: RecordPointer) -> RecordPointer:
    db.add(pointer)
    db.commit()
    db.refresh(pointer)
    return pointer


def grant_consent(db: Session, patient_id: str, grantee_user_id: str, scope: str, expires_at: datetime) -> ConsentGrant:
    c = ConsentGrant(patient_id=patient_id, grantee_user_id=grantee_user_id, scope=scope, expires_at=expires_at)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def has_valid_consent(db: Session, patient_id: str, doctor_user_id: str, scope: str, now: datetime) -> bool:
    """
    Returns True if doctor has a non-revoked, non-expired consent for:
      - the requested scope, OR
      - scope == 'all' (wildcard)
    """
    scope = normalize_scope(scope)

    c = (
        db.query(ConsentGrant)
        .filter(ConsentGrant.patient_id == patient_id)
        .filter(ConsentGrant.grantee_user_id == doctor_user_id)
        .filter(or_(ConsentGrant.scope == scope, ConsentGrant.scope == "all"))
        .filter(ConsentGrant.expires_at > now)
        .filter(ConsentGrant.revoked == False)  # noqa: E712
        .first()
    )
    return c is not None


def get_patient_by_user_id(db: Session, user_id: str) -> Patient | None:
    return db.query(Patient).filter(Patient.user_id == user_id).first()


def list_consents_for_patient(db: Session, patient_id: str) -> list[tuple[ConsentGrant, User]]:
    """
    Returns consent rows + grantee user for display.
    """
    rows = (
        db.query(ConsentGrant, User)
        .join(User, ConsentGrant.grantee_user_id == User.id)
        .filter(ConsentGrant.patient_id == patient_id)
        .order_by(ConsentGrant.created_at.desc())
        .all()
    )
    return rows


def revoke_consent(db: Session, consent_id: str) -> ConsentGrant | None:
    c = db.query(ConsentGrant).filter(ConsentGrant.id == consent_id).first()
    if not c:
        return None
    c.revoked = True
    db.commit()
    db.refresh(c)
    return c


def create_pointer_for_patient(
    db: Session,
    *,
    patient_id: str,
    record_type: str,
    fhir_base_url: str,
    fhir_resource_type: str,
    fhir_resource_id: str,
    issuer: str,
) -> RecordPointer:
    ptr = RecordPointer(
        patient_id=patient_id,
        record_type=record_type,
        fhir_base_url=fhir_base_url,
        fhir_resource_type=fhir_resource_type,
        fhir_resource_id=fhir_resource_id,
        issuer=issuer,
    )
    db.add(ptr)
    db.commit()
    db.refresh(ptr)
    return ptr


def get_provider_selection(db: Session, patient_id: int) -> PatientProviderSelection | None:
    return (
        db.query(PatientProviderSelection)
        .filter(PatientProviderSelection.patient_id == patient_id)
        .one_or_none()
    )


def upsert_provider_selection(
    db: Session,
    patient_id: int,
    *,
    npi: str,
    name: str,
    taxonomy_desc: str | None = None,
    telephone_number: str | None = None,
    line1: str | None = None,
    line2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
) -> PatientProviderSelection:
    row = get_provider_selection(db, patient_id)
    if row is None:
        row = PatientProviderSelection(
            patient_id=patient_id,
            npi=npi,
            name=name,
            taxonomy_desc=taxonomy_desc,
            telephone_number=telephone_number,
            line1=line1,
            line2=line2,
            city=city,
            state=state,
            postal_code=postal_code,
        )
        db.add(row)
    else:
        row.npi = npi
        row.name = name
        row.taxonomy_desc = taxonomy_desc
        row.telephone_number = telephone_number
        row.line1 = line1
        row.line2 = line2
        row.city = city
        row.state = state
        row.postal_code = postal_code

    db.commit()
    db.refresh(row)
    return row


def clear_provider_selection(db: Session, patient_id: int) -> bool:
    row = get_provider_selection(db, patient_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True

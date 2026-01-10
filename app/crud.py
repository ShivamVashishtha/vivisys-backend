from sqlalchemy.orm import Session
from datetime import datetime
from .models import User, Patient, ConsentGrant, RecordPointer, AuditLog, generate_public_patient_id
from .auth import hash_password, verify_password
from .models import ConsentGrant, Patient, User, RecordPointer

def normalize_scope(scope: str) -> str:
    s = (scope or "").strip().lower()
    aliases = {
        "immunization": "immunizations",
        "immunizations": "immunizations",
        "allergy": "allergies",
        "allergies": "allergies",
        "condition": "conditions",
        "conditions": "conditions",
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
            db.add(AuditLog(actor_user_id=guardian_user_id, patient_id=p.id, action="PATIENT_CREATE", details=f"public_id={p.public_id}"))
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


def has_valid_consent(db, patient_id, doctor_user_id, scope, now):
    scope = normalize_scope(scope)

    return (
        db.query(ConsentGrant)
        .filter(ConsentGrant.patient_id == patient_id)
        .filter(ConsentGrant.grantee_user_id == doctor_user_id)
        .filter(ConsentGrant.scope == scope)
        .filter(ConsentGrant.expires_at > now)
        .filter(ConsentGrant.revoked == False)
        .first()
        is not None
    )

    return db.query(q.exists()).scalar()


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
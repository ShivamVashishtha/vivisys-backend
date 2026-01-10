from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date
from typing import Optional
from datetime import datetime, date
import uuid
import secrets

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


# Human-readable public patient id:
# Example: MED-7F2A-93Q (3-4-3 format)
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0,O,1,I to avoid confusion


def generate_public_patient_id(prefix: str = "MED") -> str:
    def chunk(n: int) -> str:
        return "".join(secrets.choice(_ALPHABET) for _ in range(n))

    return f"{prefix}-{chunk(4)}-{chunk(3)}"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    role: Mapped[str] = mapped_column(String)  # "doctor" | "guardian" | "clinic_admin"
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)  # internal UUID
    public_id: Mapped[str] = mapped_column(String, unique=True, index=True)      # human readable

    # Guardian-owned patients (minors) will use guardian_user_id
    guardian_user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), index=True, nullable=True
    )

    # Adult self-owned patients will use user_id
    user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), index=True, nullable=True
    )

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConsentGrant(Base):
    __tablename__ = "consents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), index=True)
    grantee_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True)  # doctor
    scope: Mapped[str] = mapped_column(String)  # "immunizations" | "allergies" | "conditions"
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecordPointer(Base):
    __tablename__ = "record_pointers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), index=True)
    record_type: Mapped[str] = mapped_column(String)  # "immunization" | "allergy" | "condition"
    fhir_base_url: Mapped[str] = mapped_column(String)  # e.g., http://localhost:8080/fhir
    fhir_resource_type: Mapped[str] = mapped_column(String)  # e.g., "Immunization"
    fhir_resource_id: Mapped[str] = mapped_column(String)    # e.g., "123"
    issuer: Mapped[str] = mapped_column(String)              # hospital/clinic name
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    actor_user_id: Mapped[str] = mapped_column(String, index=True)
    patient_id: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)  # "REGISTER" | "LOGIN" | "PATIENT_CREATE" | "CONSENT_GRANT" | "RECORD_VIEW"
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

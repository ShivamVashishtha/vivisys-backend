from pydantic import BaseModel, EmailStr
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from datetime import date as date_type
from typing import Literal
from typing import Optional

Role = Literal["guardian", "doctor", "patient", "clinic_admin"]
Scope = Literal["immunizations", "allergies", "conditions"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    role: Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PatientOut(BaseModel):
    id: str
    public_id: str
    guardian_user_id: str
    created_at: datetime


class CreatePatientIn(BaseModel):
    # MVP: no PII stored here. Later: optional metadata.
    pass


class CreatePointerIn(BaseModel):
    record_type: Literal["immunization", "allergy", "condition"]
    fhir_base_url: str = "http://localhost:8080/fhir"
    fhir_resource_type: str
    fhir_resource_id: str
    issuer: str


class ConsentIn(BaseModel):
    grantee_email: EmailStr
    scope: Scope
    expires_at: datetime


class PatientSelfRegisterIn(BaseModel):
    date_of_birth: date_type


class ConsentOut(BaseModel):
    id: str
    patient_id: str
    patient_public_id: str
    grantee_email: str
    scope: str
    expires_at: datetime
    revoked: bool
    created_at: datetime


class ConsentListOut(BaseModel):
    patient_id: str
    patient_public_id: str
    consents: list[ConsentOut]

class SelfPointerIn(BaseModel):
    scope: Literal["immunizations", "allergies", "conditions"]
    fhir_resource_id: str
    issuer: str | None = None

class SelfPointerOut(BaseModel):
    status: str
    pointer_id: str
    record_type: str


class CatalogCreateIn(BaseModel):
    scope: Literal["immunizations", "conditions", "allergies"]
    display: str
    issuer: Optional[str] = None

class CatalogCreateOut(BaseModel):
    status: str
    fhir_resource_type: str
    fhir_resource_id: str
    pointer_id: str
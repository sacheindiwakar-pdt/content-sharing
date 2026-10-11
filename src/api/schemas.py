"""
Pydantic Schemas for Request & Response Data Validation
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str
    username: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(Admin|Healthcare Staff|Analyst)$")


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    race: Optional[str] = "Caucasian"
    gender: Optional[str] = "Male"


class PatientCreate(PatientBase):
    patient_nbr: int


class PatientUpdate(BaseModel):
    race: Optional[str] = None
    gender: Optional[str] = None


class PatientResponse(PatientBase):
    patient_nbr: int


class EncounterBase(BaseModel):
    patient_nbr: int
    age: Optional[str] = "[60-70)"
    admission_type_id: Optional[int] = 1
    discharge_disposition_id: Optional[int] = 1
    admission_source_id: Optional[int] = 7
    time_in_hospital: Optional[int] = 3
    payer_code: Optional[str] = "MC"
    medical_specialty: Optional[str] = "InternalMedicine"
    num_lab_procedures: Optional[int] = 40
    num_procedures: Optional[int] = 1
    num_medications: Optional[int] = 15
    number_outpatient: Optional[int] = 0
    number_emergency: Optional[int] = 0
    number_inpatient: Optional[int] = 0
    number_diagnoses: Optional[int] = 9
    change: Optional[str] = "No"
    diabetesMed: Optional[str] = "Yes"
    readmitted: Optional[str] = "NO"
    weight: Optional[str] = "?"
    max_glu_serum: Optional[str] = "None"
    A1Cresult: Optional[str] = "None"


class EncounterCreate(EncounterBase):
    encounter_id: int


class EncounterUpdate(BaseModel):
    patient_nbr: Optional[int] = None
    age: Optional[str] = None
    admission_type_id: Optional[int] = None
    discharge_disposition_id: Optional[int] = None
    admission_source_id: Optional[int] = None
    time_in_hospital: Optional[int] = None
    payer_code: Optional[str] = None
    medical_specialty: Optional[str] = None
    num_lab_procedures: Optional[int] = None
    num_procedures: Optional[int] = None
    num_medications: Optional[int] = None
    number_outpatient: Optional[int] = None
    number_emergency: Optional[int] = None
    number_inpatient: Optional[int] = None
    number_diagnoses: Optional[int] = None
    change: Optional[str] = None
    diabetesMed: Optional[str] = None
    readmitted: Optional[str] = None
    weight: Optional[str] = None
    max_glu_serum: Optional[str] = None
    A1Cresult: Optional[str] = None


class EncounterResponse(EncounterBase):
    encounter_id: int


class AuditLogResponse(BaseModel):
    audit_id: int
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    outcome: str
    detail: Optional[str] = None
    created_at: str

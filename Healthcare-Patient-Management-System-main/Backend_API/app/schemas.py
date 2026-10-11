from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

RoleName = Literal["Admin", "Healthcare Staff", "Analyst"]

class PatientResponse(BaseModel):
    patient_nbr: int
    race: str | None = None
    gender: str | None = None

class PatientCreate(BaseModel):
    patient_nbr: int = Field(gt=0)
    race: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=255)

class PatientReplace(BaseModel):
    race: str | None = Field(max_length=255)
    gender: str | None = Field(max_length=255)

class PatientUpdate(BaseModel):
    race: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=255)

class EncounterFields(BaseModel):
    patient_nbr: int = Field(gt=0)
    age: str | None = None
    admission_type_id: int
    discharge_disposition_id: int
    admission_source_id: int
    time_in_hospital: int | None = Field(default=None, ge=0)
    payer_code: str | None = None
    medical_specialty: str | None = None
    num_lab_procedures: int | None = Field(default=None, ge=0)
    num_procedures: int | None = Field(default=None, ge=0)
    num_medications: int | None = Field(default=None, ge=0)
    number_outpatient: int | None = Field(default=None, ge=0)
    number_emergency: int | None = Field(default=None, ge=0)
    number_inpatient: int | None = Field(default=None, ge=0)
    number_diagnoses: int | None = Field(default=None, ge=0)
    change: str | None = None
    diabetesMed: str | None = None
    readmitted: str | None = None
    weight: str | None = None
    max_glu_serum: str | None = None
    A1Cresult: str | None = None

class EncounterCreate(EncounterFields):
    encounter_id: int = Field(gt=0)

class EncounterReplace(EncounterFields):
    pass

class EncounterUpdate(BaseModel):
    patient_nbr: int | None = Field(default=None, gt=0)
    age: str | None = None
    admission_type_id: int | None = None
    discharge_disposition_id: int | None = None
    admission_source_id: int | None = None
    time_in_hospital: int | None = Field(default=None, ge=0)
    payer_code: str | None = None
    medical_specialty: str | None = None
    num_lab_procedures: int | None = Field(default=None, ge=0)
    num_procedures: int | None = Field(default=None, ge=0)
    num_medications: int | None = Field(default=None, ge=0)
    number_outpatient: int | None = Field(default=None, ge=0)
    number_emergency: int | None = Field(default=None, ge=0)
    number_inpatient: int | None = Field(default=None, ge=0)
    number_diagnoses: int | None = Field(default=None, ge=0)
    change: str | None = None
    diabetesMed: str | None = None
    readmitted: str | None = None
    weight: str | None = None
    max_glu_serum: str | None = None
    A1Cresult: str | None = None

class DiagnosisCreate(BaseModel):
    encounter_id: int = Field(gt=0)
    diagnosis_position: int = Field(ge=1)
    diagnosis_code: str | None = Field(default=None, max_length=100)

class DiagnosisReplace(BaseModel):
    diagnosis_code: str | None = Field(max_length=100)

class DiagnosisUpdate(BaseModel):
    diagnosis_code: str | None = Field(default=None, max_length=100)

class MedicationCreate(BaseModel):
    encounter_id: int = Field(gt=0)
    medication: str = Field(min_length=1, max_length=100)
    medication_status: str | None = Field(default=None, max_length=100)

class MedicationReplace(BaseModel):
    medication_status: str | None = Field(max_length=100)

class MedicationUpdate(BaseModel):
    medication_status: str | None = Field(default=None, max_length=100)

class ReferenceDataResponse(BaseModel):
    id: int
    description: str | None = None

class AnalyticsOverviewResponse(BaseModel):
    total_patients: int
    total_encounters: int
    average_length_of_stay: float | None
    readmitted_encounters: int
    readmission_rate_percent: float | None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.@-]+$")
    password: str = Field(min_length=12, max_length=128)
    role: RoleName

class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    is_active: bool

class UserUpdate(BaseModel):
    role: RoleName | None = None
    is_active: bool | None = None

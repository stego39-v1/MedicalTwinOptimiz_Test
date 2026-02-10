# schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, List
import enum


# Enums для Pydantic
class GenderEnum(str, enum.Enum):
    male = 'м'
    female = 'ж'


class RoleEnum(str, enum.Enum):
    patient = 'patient'
    doctor = 'doctor'
    admin = 'admin'


class StatusEnum(str, enum.Enum):
    active = 'активно'
    completed = 'завершено'
    cancelled = 'отменено'


class AppointmentStatus(str, enum.Enum):
    scheduled = "запланировано"
    completed = "завершено"
    cancelled = "отменено"
    no_show = "неявка"


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    email: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshToken(BaseModel):
    refresh_token: str


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    role: RoleEnum


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Patient schemas
class PatientBase(BaseModel):
    surname: str
    name: str
    patronim: Optional[str] = None
    gender: GenderEnum
    birth_date: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    city: Optional[str] = None
    street: Optional[str] = None
    building: Optional[str] = None


class PatientCreate(PatientBase):
    password: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientWithUser(PatientResponse):
    user: Optional[UserResponse] = None


# Measurement schemas
class MeasurementBase(BaseModel):
    glucose: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    pulse: Optional[int] = None
    weight: Optional[float] = None
    measured_at: Optional[datetime] = None
    notes: Optional[str] = None


class MeasurementCreate(MeasurementBase):
    patient_id: int


class MeasurementResponse(MeasurementBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Prescription schemas
class PrescriptionBase(BaseModel):
    medication_name: str
    quantity: float
    dose_unit: str
    frequency: str
    duration_days: int
    start_date: datetime
    end_date: Optional[datetime] = None
    instructions: Optional[str] = None
    status: str = 'активно'


class PrescriptionCreate(PrescriptionBase):
    patient_id: int
    doctor_id: int


class PrescriptionResponse(PrescriptionBase):
    id: int
    patient_id: int
    doctor_id: int
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientResponse] = None
    doctor: Optional["DoctorResponse"] = None

    model_config = ConfigDict(from_attributes=True)


# Complaint schemas
class ComplaintBase(BaseModel):
    symptom_name: str
    complaint_date: Optional[datetime] = None
    severity: str
    description: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    patient_id: int


class ComplaintResponse(ComplaintBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Doctor schemas
class DoctorBase(BaseModel):
    surname: str
    name: str
    patronim: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class DoctorCreate(DoctorBase):
    password: Optional[str] = None


class DoctorResponse(DoctorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoctorWithUser(DoctorResponse):
    user: Optional[UserResponse] = None


# Appointment schemas
class AppointmentBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    status: AppointmentStatus = AppointmentStatus.scheduled
    reason: Optional[str] = None
    notes: Optional[str] = None
    diagnosis_id: Optional[int] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientResponse] = None
    doctor: Optional[DoctorResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Diagnosis schemas
class DiagnosisBase(BaseModel):
    mkb10_code: str
    name: str
    category: str


class DiagnosisResponse(DiagnosisBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientDiagnosisCreate(BaseModel):
    patient_id: int
    diagnosis_id: int
    diagnosed_at: Optional[datetime] = None
    notes: Optional[str] = None


class PatientDiagnosisResponse(BaseModel):
    id: int
    patient_id: int
    diagnosis_id: int
    diagnosed_at: datetime
    notes: Optional[str] = None
    diagnosis: DiagnosisResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Medical card response
class MedicalCardResponse(BaseModel):
    patient: PatientResponse
    measurements: List[MeasurementResponse] = []
    prescriptions: List[PrescriptionResponse] = []
    complaints: List[ComplaintResponse] = []
    appointments: List[AppointmentResponse] = []
    diagnoses: List[PatientDiagnosisResponse] = []


# Statistics
class PatientStatistics(BaseModel):
    total_patients: int
    active_prescriptions: int
    recent_measurements: int
    upcoming_appointments: int


# Update forward references
PrescriptionResponse.update_forward_refs()
AppointmentResponse.update_forward_refs()
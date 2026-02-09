from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime, time


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[str] = "patient"


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    role: Optional[str] = None  # Добавляем computed поле

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Patient schemas
class PatientBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    gender: str
    city: str
    street: str
    building: str
    email: str
    birth_date: str
    phone: str


class PatientCreate(PatientBase):
    pass


class Patient(PatientBase):
    id: int

    class Config:
        from_attributes = True


# Doctor schemas
class DoctorBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    specialty: str
    department: str
    email: str
    phone: str


class DoctorCreate(DoctorBase):
    pass


class Doctor(DoctorBase):
    id: int

    class Config:
        from_attributes = True


# Diagnosis schemas
class DiagnosisBase(BaseModel):
    icd_code: str
    name: str
    category: str


class DiagnosisCreate(DiagnosisBase):
    pass


class Diagnosis(DiagnosisBase):
    id: int

    class Config:
        from_attributes = True


# Symptom schemas
class SymptomBase(BaseModel):
    name: str
    description: str
    category_name: str


class SymptomCreate(SymptomBase):
    pass


class Symptom(SymptomBase):
    id: int

    class Config:
        from_attributes = True


# PatientComplaint schemas
class PatientComplaintBase(BaseModel):
    patient_last_name: str
    patient_first_name: str
    patient_middle_name: Optional[str] = None
    symptom_name: str
    complaint_date: date
    severity: str
    description: str


class PatientComplaintCreate(PatientComplaintBase):
    pass


class PatientComplaint(PatientComplaintBase):
    id: int

    class Config:
        from_attributes = True


# Prescription schemas
class PrescriptionBase(BaseModel):
    patient_last_name: str
    patient_first_name: str
    patient_middle_name: Optional[str] = None
    doctor_last_name: str
    doctor_first_name: str
    doctor_middle_name: Optional[str] = None
    medication_name: str
    quantity: float
    dose_unit: str
    frequency: str
    duration_in_days: int
    start_date: date
    end_date: Optional[date] = None
    instructions: str
    status: str
    created_at: datetime


class PrescriptionCreate(PrescriptionBase):
    pass


class Prescription(PrescriptionBase):
    id: int

    class Config:
        from_attributes = True


class UserRoleBase(BaseModel):
    user_id: int
    role: str


class UserRoleCreate(UserRoleBase):
    pass


class UserRole(UserRoleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# app/schemas.py (добавьте в конец файла)

# Схема для полной медицинской карты пациента
class MedicalRecordBase(BaseModel):
    patient_id: int
    patient_name: str


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecord(MedicalRecordBase):
    patient_info: Patient
    complaints: List[PatientComplaint]
    prescriptions: List[Prescription]
    diagnoses: List[Diagnosis]  # Диагнозы, связанные с пациентом

    class Config:
        from_attributes = True


# Схема для краткой истории лечения
class TreatmentHistory(BaseModel):
    date: date
    type: str  # "complaint", "prescription", "diagnosis"
    description: str
    doctor_name: Optional[str] = None
    details: Optional[dict] = None

    class Config:
        from_attributes = True


# Схема для сводки по пациенту
class PatientSummary(BaseModel):
    patient: Patient
    total_complaints: int
    total_prescriptions: int
    active_prescriptions: int
    recent_diagnoses: List[Diagnosis]
    last_visit_date: Optional[date] = None

    class Config:
        from_attributes = True


class SelfMonitoringBase(BaseModel):
    measurement_date: date
    measurement_time: Optional[time] = None

    # Жизненные показатели
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=150)
    heart_rate: Optional[int] = Field(None, ge=30, le=200)
    body_temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    blood_sugar: Optional[float] = Field(None, ge=2.0, le=30.0)
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100)
    weight: Optional[float] = Field(None, ge=20.0, le=300.0)
    height: Optional[float] = Field(None, ge=50.0, le=250.0)

    # Симптомы и самочувствие
    pain_level: Optional[int] = Field(None, ge=0, le=10)
    fatigue_level: Optional[int] = Field(None, ge=0, le=10)
    mood: Optional[str] = None
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    appetite: Optional[str] = None

    # Примечания
    symptoms: Optional[str] = None
    medications_taken: Optional[str] = None
    notes: Optional[str] = None


class SelfMonitoringCreate(SelfMonitoringBase):
    patient_id: Optional[int] = None  # Можно не указывать, будет определяться автоматически


class SelfMonitoringUpdate(BaseModel):
    # Все поля опциональны для обновления
    measurement_date: Optional[date] = None
    measurement_time: Optional[time] = None
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=150)
    heart_rate: Optional[int] = Field(None, ge=30, le=200)
    body_temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    blood_sugar: Optional[float] = Field(None, ge=2.0, le=30.0)
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100)
    weight: Optional[float] = Field(None, ge=20.0, le=300.0)
    symptoms: Optional[str] = None
    medications_taken: Optional[str] = None
    notes: Optional[str] = None
    pain_level: Optional[int] = Field(None, ge=0, le=10)
    fatigue_level: Optional[int] = Field(None, ge=0, le=10)
    mood: Optional[str] = None
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    appetite: Optional[str] = None


class SelfMonitoring(SelfMonitoringBase):
    id: int
    patient_id: int
    is_alert: bool
    alert_messages: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схема для статистики показателей
class MonitoringStats(BaseModel):
    period: str
    average_bp_systolic: Optional[float] = None
    average_bp_diastolic: Optional[float] = None
    average_heart_rate: Optional[float] = None
    average_temperature: Optional[float] = None
    average_blood_sugar: Optional[float] = None
    average_weight: Optional[float] = None
    min_values: dict
    max_values: dict
    trend: str  # improving, stable, worsening


# Схема для графика/тренда
class MonitoringTrend(BaseModel):
    dates: List[date]
    values: List[Optional[float]]
    metric_name: str
    unit: str


# Схема для дневной сводки
class DailySummary(BaseModel):
    date: date
    measurements_count: int
    alerts_count: int
    critical_measurements: List[str]
    recommendations: List[str]


# Medical Appointment schemas
class AppointmentBase(BaseModel):
    appointment_type: str
    title: str
    description: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    preferred_time: Optional[str] = None
    status: Optional[str] = "active"
    priority: Optional[str] = "medium"
    reminder_enabled: Optional[bool] = True
    reminder_time: Optional[str] = None
    reminder_days_before: Optional[int] = 0
    total_doses: Optional[int] = None


class AppointmentCreate(AppointmentBase):
    patient_id: Optional[int] = None  # Можно не указывать, будет определяться из контекста
    doctor_id: int


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
    end_date: Optional[date] = None


class Appointment(AppointmentBase):
    id: int
    patient_id: int
    doctor_id: int
    completed_doses: int
    completion_rate: float
    last_taken_date: Optional[date] = None
    next_due_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Appointment Completion schemas
class CompletionBase(BaseModel):
    completion_date: date
    completion_time: Optional[str] = None
    actual_time: Optional[str] = None
    status: Optional[str] = "completed"
    notes: Optional[str] = None
    dosage_taken: Optional[str] = None
    side_effects: Optional[str] = None
    pain_level_after: Optional[int] = Field(None, ge=0, le=10)
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)


class CompletionCreate(CompletionBase):
    appointment_id: int


class Completion(CompletionBase):
    id: int
    appointment_id: int
    patient_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Reminder schemas
class ReminderBase(BaseModel):
    reminder_date: date
    reminder_time: str
    reminder_type: Optional[str] = "in_app"
    message: Optional[str] = None


class ReminderCreate(ReminderBase):
    appointment_id: int


class Reminder(ReminderBase):
    id: int
    appointment_id: int
    patient_id: int
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Статистика и отчеты
class AppointmentStats(BaseModel):
    total_appointments: int
    active_appointments: int
    completed_appointments: int
    completion_rate: float
    overdue_appointments: int
    today_appointments: int
    upcoming_appointments: List[Appointment]


class DailySchedule(BaseModel):
    date: date
    appointments: List[Appointment]
    completions: List[Completion]
    reminders: List[Reminder]


class MedicationAdherence(BaseModel):
    appointment_id: int
    appointment_title: str
    total_doses: int
    completed_doses: int
    adherence_rate: float
    missed_dates: List[date]
    streak_days: int
    last_completion: Optional[date] = None


class ConsultationBase(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_date: date
    scheduled_time: time
    consultation_type: str
    reason: str
    duration_minutes: Optional[int] = 30

class ConsultationCreate(ConsultationBase):
    pass

class Consultation(ConsultationBase):
    id: int
    status: str
    room: Optional[str] = None
    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None
    created_at: datetime

class AvailableSlot(BaseModel):
    date: date
    time: time
    doctor_id: int
    doctor_name: str
    specialty: str


class MedicalRecordResponse(BaseModel):
    """Ответ с полной медицинской картой"""
    patient: Patient
    complaints: List[PatientComplaint]
    prescriptions: List[Prescription]
    diagnoses: List[Diagnosis]

    class Config:
        from_attributes = True


class TreatmentHistoryItem(BaseModel):
    """Элемент истории лечения"""
    date: date
    type: str  # "complaint", "prescription", "diagnosis"
    description: str
    doctor_name: Optional[str] = None
    details: Optional[dict] = None

    class Config:
        from_attributes = True


class PatientSummaryResponse(BaseModel):
    """Сводная информация о пациенте"""
    patient: Patient
    total_complaints: int
    total_prescriptions: int
    active_prescriptions: int
    recent_diagnoses: List[Diagnosis]
    last_visit_date: Optional[date] = None

    class Config:
        from_attributes = True


class TimelineItem(BaseModel):
    """Элемент временной шкалы"""
    month: str  # "2024-01"
    year: int
    month_num: int
    complaints: int
    prescriptions: int
    visits: int

    class Config:
        from_attributes = True


class HealthTimelineReport(BaseModel):
    period: str
    patient_id: int
    total_measurements: int
    trend_analysis: dict
    recommendations: List[str]

class TreatmentEffectivenessReport(BaseModel):
    metrics: dict
    effectiveness_score: float
    recommendations: List[str]

class SymptomTrendsReport(BaseModel):
    patient_id: int
    analysis_period_months: int
    total_complaints: int
    symptom_analysis: dict
    trend_insights: List[str]

class ComprehensiveReport(BaseModel):
    report_type: str
    report_name: str
    generated_at: str
    data: dict


class DoctorScheduleBase(BaseModel):
    doctor_id: int
    day_of_week: int = Field(ge=0, le=6)  # 0-6
    start_time: time
    end_time: time
    appointment_type: Optional[str] = "consultation"
    slot_duration: Optional[int] = 30
    is_active: Optional[bool] = True


class DoctorScheduleCreate(DoctorScheduleBase):
    pass


class DoctorSchedule(DoctorScheduleBase):
    id: int

    class Config:
        from_attributes = True


# Consultation schemas
class ConsultationBase(BaseModel):
    patient_id: int
    doctor_id: int
    consultation_type: str
    scheduled_date: date
    scheduled_time: time
    duration_minutes: Optional[int] = 30
    reason: str
    slot_id: Optional[int] = None  # ID забронированного слота


class ConsultationCreate(ConsultationBase):
    pass


class ConsultationUpdate(BaseModel):
    status: Optional[str] = None
    preliminary_diagnosis: Optional[str] = None
    recommendations: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None


class Consultation(ConsultationBase):
    id: int
    status: str
    room: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Appointment Slot schemas
class AppointmentSlotBase(BaseModel):
    doctor_id: int
    slot_date: date
    start_time: time
    end_time: time


class AppointmentSlotCreate(AppointmentSlotBase):
    pass


class AppointmentSlot(AppointmentSlotBase):
    id: int
    status: str
    consultation_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    specialty: str
    slot_date: date
    start_time: time
    end_time: time
    duration_minutes: int


class BookSlotRequest(BaseModel):
    consultation_type: str
    reason: str
    patient_id: Optional[int] = None  # Если не указан, используется текущий пользователь
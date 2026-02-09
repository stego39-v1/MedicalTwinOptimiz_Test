# app/models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="patient")  # patient, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    gender = Column(String)
    city = Column(String)
    street = Column(String)
    building = Column(String)
    email = Column(String)
    birth_date = Column(String)
    phone = Column(String)

    # Связь с пользователем
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="patient_profile")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    specialty = Column(String)
    department = Column(String)
    email = Column(String)
    phone = Column(String)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    icd_code = Column(String, index=True)
    name = Column(String)
    category = Column(String)


class PatientComplaint(Base):
    __tablename__ = "patient_complaints"

    id = Column(Integer, primary_key=True, index=True)
    patient_last_name = Column(String)
    patient_first_name = Column(String)
    patient_middle_name = Column(String, nullable=True)
    symptom_name = Column(String)
    complaint_date = Column(Date)
    severity = Column(String)
    description = Column(Text)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", backref="complaints")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_last_name = Column(String)
    patient_first_name = Column(String)
    patient_middle_name = Column(String, nullable=True)
    doctor_last_name = Column(String)
    doctor_first_name = Column(String)
    doctor_middle_name = Column(String, nullable=True)
    medication_name = Column(String)
    quantity = Column(Float)
    dose_unit = Column(String)
    frequency = Column(String)
    duration_in_days = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    instructions = Column(Text)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    patient = relationship("Patient", backref="prescriptions")
    doctor = relationship("Doctor", backref="prescriptions")


class SelfMonitoring(Base):
    """Данные самоконтроля пациента"""
    __tablename__ = "self_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Основные показатели
    measurement_date = Column(Date, default=func.current_date())
    measurement_time = Column(Time, default=func.now())

    # Жизненные показатели
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    body_temperature = Column(Float, nullable=True)
    blood_sugar = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)

    # Субъективные ощущения (дневник самочувствия)
    pain_level = Column(Integer, nullable=True)  # 0-10
    fatigue_level = Column(Integer, nullable=True)  # 0-10
    mood = Column(String, nullable=True)  # good, normal, bad
    sleep_hours = Column(Float, nullable=True)
    appetite = Column(String, nullable=True)  # good, normal, bad

    # Симптомы и примечания
    symptoms = Column(Text, nullable=True)
    medications_taken = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Тревожные показатели
    is_alert = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", backref="self_monitoring_records")

    def check_alert_conditions(self):
        """Проверяет тревожные показатели"""
        alerts = []

        if self.blood_pressure_systolic and (self.blood_pressure_systolic > 180 or self.blood_pressure_systolic < 90):
            alerts.append("Аномальное систолическое давление")

        if self.blood_pressure_diastolic and (self.blood_pressure_diastolic > 120 or self.blood_pressure_diastolic < 60):
            alerts.append("Аномальное диастолическое давление")

        if self.heart_rate and (self.heart_rate > 120 or self.heart_rate < 50):
            alerts.append("Аномальный пульс")

        if self.body_temperature and self.body_temperature > 38.0:
            alerts.append("Повышенная температура")

        if self.blood_sugar and (self.blood_sugar > 10.0 or self.blood_sugar < 3.9):
            alerts.append("Аномальный уровень сахара")

        if self.pain_level and self.pain_level >= 7:
            alerts.append("Высокий уровень боли")

        return alerts


class MedicalAppointment(Base):
    """Медицинские назначения"""
    __tablename__ = "medical_appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Информация о назначении
    appointment_type = Column(String)  # medication, consultation, procedure
    title = Column(String)
    description = Column(Text, nullable=True)

    # Детали назначения
    dosage = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)

    # Даты и время
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    preferred_time = Column(String, nullable=True)

    # Статус
    status = Column(String, default="active")  # active, completed, cancelled

    # Напоминания
    reminder_enabled = Column(Boolean, default=True)
    reminder_time = Column(String, nullable=True)

    # Отслеживание выполнения
    completed_doses = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    next_due_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", backref="appointments")
    doctor = relationship("Doctor", backref="prescribed_appointments")


class AppointmentCompletion(Base):
    """Выполнение назначений"""
    __tablename__ = "appointment_completions"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("medical_appointments.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))

    completion_date = Column(Date, default=func.current_date())
    completion_time = Column(String, nullable=True)
    status = Column(String, default="completed")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship("MedicalAppointment", backref="completions")
    patient = relationship("Patient")


# ========== МОДЕЛИ ДЛЯ ПЛАНИРОВАНИЯ КОНСУЛЬТАЦИЙ ==========

class DoctorSchedule(Base):
    """Рабочий график врача"""
    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Рабочие дни и время
    day_of_week = Column(Integer)  # 0-6
    start_time = Column(Time)
    end_time = Column(Time)
    slot_duration = Column(Integer, default=30)  # Длительность слота

    # Доступность
    is_active = Column(Boolean, default=True)

    doctor = relationship("Doctor", backref="schedules")


class AppointmentSlot(Base):
    """Слот для записи"""
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    schedule_id = Column(Integer, ForeignKey("doctor_schedules.id"), nullable=True)

    # Время слота
    slot_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)

    # Статус
    status = Column(String, default="available")  # available, booked, blocked

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    doctor = relationship("Doctor", backref="slots")
    schedule = relationship("DoctorSchedule")


class Consultation(Base):
    """Консультация/визит"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Тип и статус
    consultation_type = Column(String)  # primary, follow_up, emergency
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled

    # Время
    scheduled_date = Column(Date)
    scheduled_time = Column(Time)
    duration_minutes = Column(Integer, default=30)

    # Детали
    reason = Column(Text)
    symptoms = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", backref="consultations")
    doctor = relationship("Doctor", backref="consultations")
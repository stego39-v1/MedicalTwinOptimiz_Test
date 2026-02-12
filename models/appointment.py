# models/appointment.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime
import enum


class AppointmentStatus(str, enum.Enum):
    scheduled = "запланировано"
    completed = "завершено"
    cancelled = "отменено"
    no_show = "неявка"


class Appointment(Base, BaseModel):
    __tablename__ = "appointments"

    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.scheduled)
    reason = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    diagnosis_id = Column(Integer, ForeignKey('diagnoses.id'), nullable=True)

    patient = relationship("Patient", back_populates="patient_appointments")
    doctor = relationship("Doctor", back_populates="doctor_appointments")
    diagnosis = relationship("Diagnosis", back_populates="diagnosis_appointments")

    __table_args__ = (
        Index('idx_appointments_doctor_date', 'doctor_id', 'appointment_date'),
        Index('idx_appointments_patient_date', 'patient_id', 'appointment_date'),
    )
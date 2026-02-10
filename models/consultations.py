# models/consultations.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Index
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime


class Consultation(Base, BaseModel):
    __tablename__ = "consultations"

    patient_id = Column(ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id = Column(ForeignKey('doctors.id'), nullable=False, index=True)
    consultation_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    notes = Column(String(1000), nullable=True)

    # Исправляем отношения
    patient = relationship("Patient", back_populates="consultations")
    doctor = relationship("Doctor", back_populates="consultations")

    __table_args__ = (
        Index('idx_consultations_doctor_date', 'doctor_id', 'consultation_date'),
    )
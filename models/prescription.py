from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime

class Prescription(Base, BaseModel):
    __tablename__ = "prescriptions"

    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    medication_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    dose_unit = Column(String(20), nullable=False)
    frequency = Column(String(50), nullable=False)
    duration_days = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(String(20), default='активно')

    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
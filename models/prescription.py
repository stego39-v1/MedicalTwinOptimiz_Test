from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Prescription(Base, BaseModel):
    __tablename__ = "prescriptions"

    patient_id = Column(ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id = Column(ForeignKey('doctors.id'), nullable=False, index=True)
    medication_name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    dose_unit = Column(String(20), nullable=False)
    frequency = Column(String(50), nullable=False)
    duration_days = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    instructions = Column(String(500), nullable=True)
    status = Column(String(20), default='активно', nullable=False)

    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
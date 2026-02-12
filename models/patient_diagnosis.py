from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime

class PatientDiagnosis(Base, BaseModel):
    __tablename__ = "patient_diagnoses"

    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    diagnosis_id = Column(Integer, ForeignKey('diagnoses.id'), nullable=False, index=True)
    diagnosed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(String(500), nullable=True)

    patient = relationship("Patient", back_populates="patient_diagnoses")
    diagnosis = relationship("Diagnosis", back_populates="patient_diagnoses")
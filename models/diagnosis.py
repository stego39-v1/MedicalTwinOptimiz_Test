from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime


class Diagnosis(Base, BaseModel):
    __tablename__ = "diagnoses"

    mkb10_code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)

    # ДОБАВЬТЕ ЭТУ СТРОКУ:
    patient_diagnoses = relationship("PatientDiagnosis", back_populates="diagnosis")


class PatientDiagnosis(Base, BaseModel):
    __tablename__ = "patient_diagnoses"

    patient_id = Column(ForeignKey('patients.id'), nullable=False, index=True)
    diagnosis_id = Column(ForeignKey('diagnoses.id'), nullable=False, index=True)
    diagnosed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    diagnosis_appointments = relationship("Appointment", back_populates="diagnosis")

    patient = relationship("Patient", back_populates="patient_diagnoses")
    diagnosis = relationship("Diagnosis", back_populates="patient_diagnoses")
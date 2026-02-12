from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime

class Complaint(Base, BaseModel):
    __tablename__ = "complaints"

    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    symptom_id = Column(Integer, ForeignKey('symptoms.id'), nullable=False)
    complaint_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="complaints")
    symptom = relationship("Symptom", back_populates="complaints")
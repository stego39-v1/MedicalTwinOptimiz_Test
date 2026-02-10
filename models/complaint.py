from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
from datetime import datetime

class Complaint(Base, BaseModel):
    __tablename__ = "complaints"

    patient_id = Column(ForeignKey('patients.id'), nullable=False, index=True)
    symptom_name = Column(String(100), nullable=False)
    complaint_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(String(500), nullable=True)

    patient = relationship("Patient", back_populates="complaints")
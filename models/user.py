from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class User(Base, BaseModel):
    __tablename__ = "users"

    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=True)

    patient = relationship("Patient", back_populates="user")
    doctor = relationship("Doctor", back_populates="user")
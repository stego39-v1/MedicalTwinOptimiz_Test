# models/patient.py
from sqlalchemy import Column, String, Date, Float, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum


class GenderEnum(str, enum.Enum):
    male = 'м'
    female = 'ж'


class Patient(Base, BaseModel):
    __tablename__ = "patients"

    surname = Column(String(50), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    patronim = Column(String(50), nullable=True)
    gender = Column(SQLEnum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=False, index=True)
    city = Column(String(100), nullable=True)
    street = Column(String(100), nullable=True)
    building = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)

    user = relationship("User", back_populates="patient", uselist=False)
    complaints = relationship("Complaint", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    measurements = relationship("Measurement", back_populates="patient")
    # Добавляем если нужны консультации
    # consultations = relationship("Consultation", back_populates="patient")

    __table_args__ = (
        Index('idx_patients_full_name', 'surname', 'name', 'patronim'),
    )
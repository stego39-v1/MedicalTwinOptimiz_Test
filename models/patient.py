from sqlalchemy import Column, String, Date, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel
import enum
from sqlalchemy import Enum as SQLEnum

class GenderEnum(str, enum.Enum):
    male = 'м'
    female = 'ж'

class Patient(Base, BaseModel):
    __tablename__ = "patients"

    surname = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    patronim = Column(String(50), nullable=True)
    gender = Column(SQLEnum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=False)
    city = Column(String(100), nullable=True)
    street = Column(String(100), nullable=True)
    building = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)

    user = relationship("User", back_populates="patient", uselist=False)
    prescriptions = relationship("Prescription", back_populates="patient")
    complaints = relationship("Complaint", back_populates="patient")
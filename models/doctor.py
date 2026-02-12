from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Doctor(Base, BaseModel):
    __tablename__ = "doctors"

    surname = Column(String(50), nullable=False)
    name = Column(String(50), nullable=False)
    patronim = Column(String(50), nullable=True)
    specialization_id = Column(Integer, ForeignKey('specializations.id'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="doctor", uselist=False)
    specialization_rel = relationship("Specialization", back_populates="doctors")
    department_rel = relationship("Department", back_populates="doctors")
    prescriptions = relationship("Prescription", back_populates="doctor")
# models/doctor.py
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base, BaseModel


class Doctor(Base, BaseModel):
    __tablename__ = "doctors"

    surname = Column(String(50), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    patronim = Column(String(50), nullable=True)
    specialization = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)

    user = relationship("User", back_populates="doctor", uselist=False)
    prescriptions = relationship("Prescription", back_populates="doctor")
    # УДАЛИТЕ ЭТУ СТРОКУ: consultations = relationship("Consultation", back_populates="doctor")

    __table_args__ = (
        Index('idx_doctors_full_name', 'surname', 'name', 'patronim'),
    )
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Specialization(Base, BaseModel):
    __tablename__ = "specializations"

    name = Column(String(100), unique=True, nullable=False)

    doctors = relationship("Doctor", back_populates="specialization_rel")
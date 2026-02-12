from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Department(Base, BaseModel):
    __tablename__ = "departments"

    name = Column(String(100), unique=True, nullable=False)

    doctors = relationship("Doctor", back_populates="department_rel")
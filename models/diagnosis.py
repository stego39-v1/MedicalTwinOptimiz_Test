from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Diagnosis(Base, BaseModel):
    __tablename__ = "diagnoses"

    mkb10_code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
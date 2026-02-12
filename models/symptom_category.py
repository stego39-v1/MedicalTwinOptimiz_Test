from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class SymptomCategory(Base, BaseModel):
    __tablename__ = "symptom_categories"

    name = Column(String(100), unique=True, nullable=False)

    symptoms = relationship("Symptom", back_populates="category")
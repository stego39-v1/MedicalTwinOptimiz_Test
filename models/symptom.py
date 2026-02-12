from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class Symptom(Base, BaseModel):
    __tablename__ = "symptoms"

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey('symptom_categories.id'), nullable=False)

    category = relationship("SymptomCategory", back_populates="symptoms")
    complaints = relationship("Complaint", back_populates="symptom")
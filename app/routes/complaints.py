# app/routes/complaints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import crud, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/complaints", tags=["complaints"])

@router.post("/", response_model=schemas.PatientComplaint)
def create_complaint(
    complaint: schemas.PatientComplaintCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    return crud.create_patient_complaint(db=db, complaint=complaint)

@router.get("/", response_model=List[schemas.PatientComplaint])
def read_complaints(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    complaints = crud.get_patient_complaints(db, skip=skip, limit=limit)
    return complaints

@router.get("/{complaint_id}", response_model=schemas.PatientComplaint)
def read_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    db_complaint = crud.get_patient_complaint(db, complaint_id=complaint_id)
    if db_complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return db_complaint

@router.get("/patient/{patient_id}", response_model=List[schemas.PatientComplaint])
def read_complaints_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    complaints = crud.get_complaints_by_patient(db, patient_id=patient_id)
    return complaints
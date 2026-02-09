# app/routes/prescriptions.py
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

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

@router.post("/", response_model=schemas.Prescription)
def create_prescription(
    prescription: schemas.PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    return crud.create_prescription(db=db, prescription=prescription)

@router.get("/", response_model=List[schemas.Prescription])
def read_prescriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    prescriptions = crud.get_prescriptions(db, skip=skip, limit=limit)
    return prescriptions

@router.get("/{prescription_id}", response_model=schemas.Prescription)
def read_prescription(
    prescription_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    db_prescription = crud.get_prescription(db, prescription_id=prescription_id)
    if db_prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return db_prescription

@router.get("/patient/{patient_id}", response_model=List[schemas.Prescription])
def read_prescriptions_by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    prescriptions = crud.get_prescriptions_by_patient(db, patient_id=patient_id)
    return prescriptions

@router.get("/doctor/{doctor_id}", response_model=List[schemas.Prescription])
def read_prescriptions_by_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    prescriptions = crud.get_prescriptions_by_doctor(db, doctor_id=doctor_id)
    return prescriptions

@router.get("/status/{status}", response_model=List[schemas.Prescription])
def read_prescriptions_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    prescriptions = crud.get_prescriptions_by_status(db, status=status)
    return prescriptions

@router.patch("/{prescription_id}/status")
def update_prescription_status(
    prescription_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    db_prescription = crud.update_prescription_status(db, prescription_id, status)
    if db_prescription is None:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return {"message": "Prescription status updated successfully"}
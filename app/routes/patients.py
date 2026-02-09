# app/routes/patients.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import sys

# Добавляем родительскую директорию в путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import crud, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=schemas.Patient)
def create_patient(
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    return crud.create_patient(db=db, patient=patient)

# ИСПРАВЛЕНО: используем предварительно созданную зависимость
@router.get("/", response_model=List[schemas.Patient])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Только врачи и админы
):
    patients = crud.get_patients(db, skip=skip, limit=limit)
    return patients

@router.get("/{patient_id}", response_model=schemas.Patient)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    db_patient = crud.get_patient(db, patient_id=patient_id)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.put("/{patient_id}", response_model=schemas.Patient)
def update_patient(
    patient_id: int,
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Только врачи и админы
):
    db_patient = crud.update_patient(db, patient_id, patient)
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.admin_only)  # Только админы
):
    success = crud.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}
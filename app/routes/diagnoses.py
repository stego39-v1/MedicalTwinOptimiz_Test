# app/routes/diagnoses.py
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

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

@router.post("/", response_model=schemas.Diagnosis)
def create_diagnosis(
    diagnosis: schemas.DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.doctor_admin_only)  # Врачи и админы
):
    return crud.create_diagnosis(db=db, diagnosis=diagnosis)

@router.get("/", response_model=List[schemas.Diagnosis])
def read_diagnoses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    diagnoses = crud.get_diagnoses(db, skip=skip, limit=limit)
    return diagnoses

@router.get("/{diagnosis_id}", response_model=schemas.Diagnosis)
def read_diagnosis(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    db_diagnosis = crud.get_diagnosis(db, diagnosis_id=diagnosis_id)
    if db_diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return db_diagnosis

@router.get("/icd/{icd_code}", response_model=schemas.Diagnosis)
def read_diagnosis_by_icd(
    icd_code: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    db_diagnosis = crud.get_diagnosis_by_icd(db, icd_code=icd_code)
    if db_diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return db_diagnosis

@router.get("/category/{category}", response_model=List[schemas.Diagnosis])
def read_diagnoses_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.all_roles)  # Все аутентифицированные
):
    diagnoses = crud.get_diagnoses_by_category(db, category=category)
    return diagnoses
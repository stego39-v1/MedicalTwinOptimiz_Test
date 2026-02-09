# app/routes/medical_records.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import crud, schemas, auth
from app.database import get_db
from app.models import Patient

router = APIRouter(prefix="/medical-records", tags=["medical records"])


@router.get("/patient/{patient_id}/full")
def get_patient_full_medical_record(
        patient_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)  # Только врачи и админы
):
    """Полная медицинская карта пациента"""
    return crud.get_patient_medical_record(db, patient_id)


@router.get("/patient/{patient_id}/history")
def get_patient_treatment_history(
        patient_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """История лечения пациента в хронологическом порядке"""
    return crud.get_patient_treatment_history(db, patient_id)


@router.get("/patient/{patient_id}/summary")
def get_patient_summary(
        patient_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Сводная информация о пациенте"""
    return crud.get_patient_summary(db, patient_id)


@router.get("/patient/{patient_id}/timeline")
def get_patient_timeline(
        patient_id: int,
        months: int = Query(12, ge=1, le=60, description="Период в месяцах"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Временная шкала лечения пациента"""
    return crud.get_patient_timeline(db, patient_id, months)


@router.get("/my/record")
def get_my_medical_record(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)  # Только пациенты
):
    """Пациент получает свою медицинскую карту"""
    # Находим пациента по email пользователя
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found. Please complete your profile first."
        )

    return crud.get_patient_medical_record(db, patient.id)


@router.get("/my/history")
def get_my_treatment_history(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """Пациент получает свою историю лечения"""
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_patient_treatment_history(db, patient.id)


@router.get("/my/summary")
def get_my_summary(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """Пациент получает сводную информацию о себе"""
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_patient_summary(db, patient.id)


@router.get("/test")
def test_medical_records():
    """Тестовый endpoint"""
    return {
        "status": "ok",
        "message": "Medical records API is working",
        "endpoints": [
            "/patient/{id}/full - Полная медицинская карта",
            "/patient/{id}/history - История лечения",
            "/patient/{id}/summary - Сводная информация",
            "/patient/{id}/timeline - Временная шкала",
            "/my/record - Моя медицинская карта",
            "/my/history - Моя история лечения",
            "/my/summary - Моя сводная информация"
        ]
    }
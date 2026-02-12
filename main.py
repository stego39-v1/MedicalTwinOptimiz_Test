from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from database import get_db, init_db
from models import User, Patient, Doctor, Prescription, Complaint
from utils import (
    verify_password, create_access_token, create_refresh_token,
    get_current_user, require_role
)
from config import settings

# Инициализация БД
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="API для медицинской информационной системы",
    version=settings.VERSION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== БАЗОВЫЕ МЕТОДЫ ==========

@app.get("/")
async def root():
    return {"message": "Medical API работает"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Авторизация пользователя"""
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email
    }


# ========== МЕТОДЫ ДЛЯ ПАЦИЕНТОВ ==========

@app.get("/patient/profile")
async def patient_profile(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Получить профиль текущего пациента"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    patient = db.query(Patient).filter(Patient.id == current_user.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")

    return {
        "surname": patient.surname,
        "name": patient.name,
        "patronim": patient.patronim,
        "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
        "gender": patient.gender,
        "height": patient.height,
        "weight": patient.weight,
        "email": patient.email,
        "phone": patient.phone,
        "city": patient.city,
        "street": patient.street,
        "building": patient.building
    }


@app.get("/patient/prescriptions")
async def patient_prescriptions(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Получить список назначений текущего пациента"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == current_user.patient_id
    ).order_by(Prescription.start_date.desc()).all()

    result = []
    for p in prescriptions:
        doctor = db.query(Doctor).filter(Doctor.id == p.doctor_id).first()
        result.append({
            "id": p.id,
            "medication_name": p.medication_name,
            "quantity": p.quantity,
            "dose_unit": p.dose_unit,
            "frequency": p.frequency,
            "duration_days": p.duration_days,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "instructions": p.instructions,
            "status": p.status,
            "doctor_name": f"{doctor.surname} {doctor.name} {doctor.patronim or ''}".strip() if doctor else "Не указан"
        })

    return result


@app.get("/patient/complaints")
async def patient_complaints(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Получить список жалоб текущего пациента"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    complaints = db.query(Complaint).filter(
        Complaint.patient_id == current_user.patient_id
    ).order_by(Complaint.complaint_date.desc()).all()

    result = []
    for c in complaints:
        result.append({
            "id": c.id,
            "symptom_name": c.symptom.name if c.symptom else None,
            "complaint_date": c.complaint_date.isoformat() if c.complaint_date else None,
            "severity": c.severity,
            "description": c.description
        })

    return result


@app.get("/patient/measurements")
async def patient_measurements(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Получить список измерений (заглушка)"""
    # TODO: реализовать после добавления модели Measurement
    return []


@app.post("/patient/measurements")
async def add_measurement(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Добавить измерение (заглушка)"""
    # TODO: реализовать после добавления модели Measurement
    return {"status": "ok", "message": "Измерение добавлено"}


@app.post("/patient/complaints")
async def add_complaint(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Добавить жалобу (заглушка)"""
    # TODO: реализовать после добавления обработки тела запроса
    return {"status": "ok", "message": "Жалоба добавлена"}


# ========== МЕТОДЫ ДЛЯ ВРАЧЕЙ ==========

@app.get("/doctor/patients")
async def doctor_patients(
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Получить список пациентов врача (заглушка)"""
    # TODO: реализовать полноценный поиск пациентов
    patients = db.query(Patient).limit(10).all()

    result = []
    for p in patients:
        result.append({
            "id": p.id,
            "surname": p.surname,
            "name": p.name,
            "patronim": p.patronim,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "gender": p.gender,
            "email": p.email,
            "phone": p.phone
        })

    return result


@app.get("/doctor/patient/{patient_id}/card")
async def doctor_patient_card(
        patient_id: int,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Получить медицинскую карту пациента (заглушка)"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")

    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).limit(20).all()
    complaints = db.query(Complaint).filter(Complaint.patient_id == patient_id).limit(20).all()

    return {
        "patient": {
            "surname": patient.surname,
            "name": patient.name,
            "patronim": patient.patronim,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone
        },
        "prescriptions": [
            {
                "medication_name": p.medication_name,
                "quantity": p.quantity,
                "dose_unit": p.dose_unit,
                "frequency": p.frequency,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "status": p.status
            } for p in prescriptions
        ],
        "complaints": [
            {
                "symptom_name": c.symptom.name if c.symptom else None,
                "complaint_date": c.complaint_date.isoformat() if c.complaint_date else None,
                "severity": c.severity,
                "description": c.description
            } for c in complaints
        ],
        "measurements": []  # TODO: добавить измерения
    }


@app.post("/doctor/prescriptions")
async def create_prescription(
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Создать назначение (заглушка)"""
    # TODO: реализовать создание назначений
    return {"status": "ok", "message": "Назначение создано"}


# ========== ЗАПУСК ==========

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MEDICAL API ЗАПУЩЕН")
    print(f"📡 Порт: 5000")
    print(f"🔄 Режим: {'DEBUG' if settings.APP_NAME == 'Medical API' else 'PRODUCTION'}")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
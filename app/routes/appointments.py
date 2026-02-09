# app/routes/appointments.py
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import os
import sys

# Добавляем родительскую директорию в путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import crud, schemas, auth
from app.database import get_db
from app.models import Patient, Doctor

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ========== ДЛЯ ПАЦИЕНТОВ ==========

@router.get("/my/appointments", response_model=List[schemas.Appointment])
def get_my_appointments(
        status: Optional[str] = Query(None, description="Статус назначения"),
        appointment_type: Optional[str] = Query(None, description="Тип назначения"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает свои назначения
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_patient_appointments(
        db, patient.id, status, appointment_type, skip, limit
    )


@router.get("/my/today", response_model=List[schemas.Appointment])
def get_my_todays_appointments(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает сегодняшние назначения
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    today = date.today()

    appointments = db.query(crud.models.MedicalAppointment).filter(
        crud.models.MedicalAppointment.patient_id == patient.id,
        crud.models.MedicalAppointment.status == "active",
        crud.models.MedicalAppointment.next_due_date == today
    ).order_by(
        crud.models.MedicalAppointment.priority.desc()
    ).all()

    return appointments


@router.get("/my/reminders")
def get_my_reminders(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает свои напоминания
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    reminders = crud.get_todays_reminders(db, patient.id)

    return {
        "patient_id": patient.id,
        "today": date.today(),
        "reminders": reminders,
        "total_reminders": len(reminders)
    }


@router.post("/my/completion", response_model=schemas.Completion)
def create_my_completion(
        completion: schemas.CompletionCreate,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент отмечает выполнение назначения
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Проверяем, что назначение принадлежит пациенту
    appointment = crud.get_appointment(db, completion.appointment_id)
    if not appointment or appointment.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.create_completion(db, completion, patient.id)


@router.get("/my/completions", response_model=List[schemas.Completion])
def get_my_completions(
        start_date: Optional[date] = Query(None, description="Начальная дата"),
        end_date: Optional[date] = Query(None, description="Конечная дата"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает историю выполнения назначений
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_patient_completions(
        db, patient.id, start_date, end_date, skip, limit
    )


@router.get("/my/stats")
def get_my_appointment_stats(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает статистику по назначениям
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_appointment_stats(db, patient.id)


@router.get("/my/daily-schedule/{target_date}")
def get_my_daily_schedule(
        target_date: date,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает расписание на день
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_daily_schedule(db, patient.id, target_date)


@router.get("/my/adherence")
def get_my_medication_adherence(
        appointment_id: Optional[int] = Query(None, description="ID конкретного назначения"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает данные о приверженности к лечению
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_medication_adherence(db, patient.id, appointment_id)


@router.get("/my/upcoming")
def get_my_upcoming_appointments(
        days: int = Query(7, ge=1, le=30, description="Количество дней вперед"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает предстоящие назначения
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    today = date.today()
    end_date = today + timedelta(days=days)

    appointments = db.query(crud.models.MedicalAppointment).filter(
        crud.models.MedicalAppointment.patient_id == patient.id,
        crud.models.MedicalAppointment.status == "active",
        crud.models.MedicalAppointment.next_due_date >= today,
        crud.models.MedicalAppointment.next_due_date <= end_date
    ).order_by(
        crud.models.MedicalAppointment.next_due_date
    ).all()

    return {
        "patient_id": patient.id,
        "period_days": days,
        "start_date": today,
        "end_date": end_date,
        "total_appointments": len(appointments),
        "appointments": appointments
    }


# ========== ДЛЯ ВРАЧЕЙ ==========

@router.post("/doctor/create", response_model=schemas.Appointment)
def create_appointment_for_patient(
        appointment: schemas.AppointmentCreate,
        patient_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач создает назначение для пациента
    """
    # Проверяем, что врач существует
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # Проверяем, что пациент существует
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Используем ID врача из профиля
    appointment.doctor_id = doctor.id

    return crud.create_appointment(db, appointment, patient_id)


@router.get("/doctor/patient/{patient_id}/appointments", response_model=List[schemas.Appointment])
def get_patient_appointments_doctor(
        patient_id: int,
        status: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач получает назначения пациента
    """
    return crud.get_patient_appointments(db, patient_id, status, None, skip, limit)


@router.put("/doctor/appointment/{appointment_id}", response_model=schemas.Appointment)
def update_patient_appointment(
        appointment_id: int,
        appointment_update: schemas.AppointmentUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач обновляет назначение пациента
    """
    # Проверяем, что врач имеет доступ к этому назначению
    appointment = crud.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Проверяем, что врач создал это назначение или является админом
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if appointment.doctor_id != doctor.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    return crud.update_appointment(db, appointment_id, appointment_update)


@router.get("/doctor/patient/{patient_id}/completions", response_model=List[schemas.Completion])
def get_patient_completions_doctor(
        patient_id: int,
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач получает историю выполнения назначений пациента
    """
    return crud.get_patient_completions(db, patient_id, start_date, end_date, skip, limit)


@router.get("/doctor/patient/{patient_id}/adherence")
def get_patient_adherence_doctor(
        patient_id: int,
        appointment_id: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач получает данные о приверженности пациента к лечению
    """
    return crud.get_medication_adherence(db, patient_id, appointment_id)


# ========== ОБЩИЕ ЭНДПОИНТЫ ==========

@router.get("/test")
def test_appointments():
    """Тестовый эндпоинт"""
    return {
        "status": "ok",
        "message": "Appointments API is working",
        "features": [
            "Medical appointments tracking",
            "Medication reminders",
            "Completion history",
            "Adherence analytics",
            "Daily schedules"
        ]
    }


@router.get("/types")
def get_appointment_types():
    """Получить доступные типы назначений"""
    return {
        "appointment_types": [
            {"value": "medication", "label": "Лекарство", "description": "Прием лекарственных препаратов"},
            {"value": "procedure", "label": "Процедура", "description": "Медицинские процедуры"},
            {"value": "test", "label": "Анализ", "description": "Лабораторные анализы и исследования"},
            {"value": "consultation", "label": "Консультация", "description": "Врачебные консультации"},
            {"value": "exercise", "label": "Упражнения", "description": "Лечебная физкультура и упражнения"},
            {"value": "diet", "label": "Диета", "description": "Диетические рекомендации"},
            {"value": "measurement", "label": "Измерение", "description": "Измерение показателей здоровья"}
        ],
        "frequencies": [
            {"value": "ежедневно", "label": "Ежедневно", "description": "Каждый день"},
            {"value": "2 раза в неделю", "label": "2 раза в неделю", "description": "Два раза в неделю"},
            {"value": "3 раза в неделю", "label": "3 раза в неделю", "description": "Три раза в неделю"},
            {"value": "раз в неделю", "label": "Раз в неделю", "description": "Один раз в неделю"},
            {"value": "раз в месяц", "label": "Раз в месяц", "description": "Один раз в месяц"},
            {"value": "по требованию", "label": "По требованию", "description": "При появлении симптомов"},
            {"value": "однократно", "label": "Однократно", "description": "Однократное выполнение"}
        ],
        "priorities": [
            {"value": "low", "label": "Низкий", "description": "Не срочно"},
            {"value": "medium", "label": "Средний", "description": "Обычный приоритет"},
            {"value": "high", "label": "Высокий", "description": "Важное назначение"},
            {"value": "critical", "label": "Критический", "description": "Очень важное, не пропускать"}
        ]
    }
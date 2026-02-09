# app/routes/consultations.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import crud, schemas, auth
from app.database import get_db
from app.models import Patient, Doctor

router = APIRouter(prefix="/consultations", tags=["consultations"])


# ========== ДЛЯ ПАЦИЕНТОВ ==========

@router.get("/available-slots")
def get_available_appointment_slots(
        doctor_id: Optional[int] = Query(None, description="ID врача"),
        specialty: Optional[str] = Query(None, description="Специальность врача"),
        target_date: Optional[date] = Query(None, description="Дата для поиска"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.all_roles)
):
    """Поиск свободных слотов для записи"""

    query = db.query(crud.models.AppointmentSlot).join(
        crud.models.Doctor
    ).filter(
        crud.models.AppointmentSlot.status == "available"
    )

    if doctor_id:
        query = query.filter(crud.models.AppointmentSlot.doctor_id == doctor_id)

    if specialty:
        query = query.filter(crud.models.Doctor.specialty == specialty)

    if target_date:
        query = query.filter(crud.models.AppointmentSlot.slot_date == target_date)
    else:
        # По умолчанию показываем на 2 недели вперед
        start_date = date.today()
        end_date = start_date + timedelta(days=14)
        query = query.filter(
            crud.models.AppointmentSlot.slot_date >= start_date,
            crud.models.AppointmentSlot.slot_date <= end_date
        )

    slots = query.order_by(
        crud.models.AppointmentSlot.slot_date,
        crud.models.AppointmentSlot.start_time
    ).all()

    # Форматируем ответ
    available_slots = []
    for slot in slots:
        doctor = db.query(Doctor).filter(Doctor.id == slot.doctor_id).first()
        if doctor:
            available_slots.append({
                "id": slot.id,
                "doctor_id": doctor.id,
                "doctor_name": f"{doctor.last_name} {doctor.first_name}",
                "specialty": doctor.specialty,
                "slot_date": slot.slot_date,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "duration_minutes": 30  # Можно рассчитать из start_time и end_time
            })

    return available_slots


@router.post("/book-slot/{slot_id}", response_model=schemas.Consultation)
def book_appointment_slot(
        slot_id: int,
        booking_data: schemas.BookSlotRequest,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """Забронировать слот на консультацию"""

    # Проверяем, что слот существует и свободен
    slot = db.query(crud.models.AppointmentSlot).filter(
        crud.models.AppointmentSlot.id == slot_id,
        crud.models.AppointmentSlot.status == "available"
    ).first()

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found or not available")

    # Находим пациента
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Создаем консультацию
    consultation_data = schemas.ConsultationCreate(
        patient_id=patient.id,
        doctor_id=slot.doctor_id,
        consultation_type=booking_data.consultation_type,
        scheduled_date=slot.slot_date,
        scheduled_time=slot.start_time,
        reason=booking_data.reason,
        slot_id=slot_id
    )

    consultation = crud.create_consultation(db, consultation_data)
    return consultation


@router.get("/my/upcoming", response_model=List[schemas.Consultation])
def get_my_upcoming_consultations(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """Мои предстоящие консультации"""
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Получаем только предстоящие консультации (scheduled, confirmed)
    consultations = db.query(crud.models.Consultation).filter(
        crud.models.Consultation.patient_id == patient.id,
        crud.models.Consultation.status.in_(["scheduled", "confirmed"]),
        crud.models.Consultation.scheduled_date >= date.today()
    ).order_by(
        crud.models.Consultation.scheduled_date,
        crud.models.Consultation.scheduled_time
    ).all()

    return consultations


@router.get("/my/history", response_model=List[schemas.Consultation])
def get_my_consultation_history(
        limit: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """История моих консультаций"""
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    consultations = db.query(crud.models.Consultation).filter(
        crud.models.Consultation.patient_id == patient.id
    ).order_by(
        crud.models.Consultation.scheduled_date.desc(),
        crud.models.Consultation.scheduled_time.desc()
    ).limit(limit).all()

    return consultations


@router.patch("/my/cancel/{consultation_id}")
def cancel_my_consultation(
        consultation_id: int,
        reason: str = Query(..., description="Причина отмены"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """Отменить мою консультацию"""
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Проверяем, что консультация принадлежит пациенту
    consultation = crud.get_consultation(db, consultation_id)
    if not consultation or consultation.patient_id != patient.id:
        raise HTTPException(status_code=404, detail="Consultation not found")

    # Проверяем, можно ли отменить (не менее чем за 24 часа)
    consultation_datetime = datetime.combine(
        consultation.scheduled_date,
        consultation.scheduled_time
    )
    if datetime.now() > consultation_datetime - timedelta(hours=24):
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel less than 24 hours before appointment"
        )

    consultation = crud.cancel_consultation(db, consultation_id, reason)
    return {"message": "Consultation cancelled successfully"}


# ========== ДЛЯ ВРАЧЕЙ ==========

@router.get("/doctor/today", response_model=List[schemas.Consultation])
def get_doctor_today_consultations(
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Консультации врача на сегодня"""
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    today = date.today()
    consultations = db.query(crud.models.Consultation).filter(
        crud.models.Consultation.doctor_id == doctor.id,
        crud.models.Consultation.scheduled_date == today,
        crud.models.Consultation.status.in_(["scheduled", "confirmed"])
    ).order_by(crud.models.Consultation.scheduled_time).all()

    return consultations


@router.get("/doctor/schedule")
def get_doctor_schedule(
        week_start: Optional[date] = Query(None, description="Начало недели"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Расписание врача"""
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    if not week_start:
        week_start = date.today() - timedelta(days=date.today().weekday())

    week_end = week_start + timedelta(days=6)

    # Рабочий график
    schedule = crud.get_doctor_weekly_schedule(db, doctor.id)

    # Консультации на неделю
    consultations = db.query(crud.models.Consultation).filter(
        crud.models.Consultation.doctor_id == doctor.id,
        crud.models.Consultation.scheduled_date >= week_start,
        crud.models.Consultation.scheduled_date <= week_end
    ).order_by(
        crud.models.Consultation.scheduled_date,
        crud.models.Consultation.scheduled_time
    ).all()

    # Свободные слоты на неделю
    available_slots = db.query(crud.models.AppointmentSlot).filter(
        crud.models.AppointmentSlot.doctor_id == doctor.id,
        crud.models.AppointmentSlot.slot_date >= week_start,
        crud.models.AppointmentSlot.slot_date <= week_end,
        crud.models.AppointmentSlot.status == "available"
    ).all()

    return {
        "doctor_id": doctor.id,
        "doctor_name": f"{doctor.last_name} {doctor.first_name}",
        "week_start": week_start,
        "week_end": week_end,
        "schedule": schedule,
        "consultations": consultations,
        "available_slots": available_slots
    }


@router.post("/doctor/schedule", response_model=schemas.DoctorSchedule)
def create_schedule_entry(
        schedule: schemas.DoctorScheduleCreate,
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Создать запись в расписании врача"""
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # Проверяем, что врач создает свое расписание
    if schedule.doctor_id != doctor.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.create_doctor_schedule(db, schedule)


@router.post("/doctor/generate-slots")
def generate_slots_for_period(
        start_date: date = Query(..., description="Дата начала"),
        end_date: date = Query(..., description="Дата окончания"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Сгенерировать слоты для записи на период"""
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    slots = crud.generate_appointment_slots(db, doctor.id, start_date, end_date)

    return {
        "doctor_id": doctor.id,
        "start_date": start_date,
        "end_date": end_date,
        "slots_generated": len(slots)
    }


@router.patch("/doctor/consultation/{consultation_id}/status")
def update_consultation_status(
        consultation_id: int,
        status: str = Query(..., description="Новый статус"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Обновить статус консультации"""
    doctor = db.query(Doctor).filter(Doctor.email == current_user.email).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # Проверяем, что консультация у этого врача
    consultation = crud.get_consultation(db, consultation_id)
    if not consultation or consultation.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Consultation not found")

    consultation = crud.update_consultation_status(db, consultation_id, status)
    return {"message": f"Consultation status updated to {status}"}


# ========== ОБЩИЕ ЭНДПОИНТЫ ==========

@router.get("/test")
def test_consultations():
    """Тестовый эндпоинт"""
    return {
        "status": "ok",
        "message": "Consultations API is working",
        "features": [
            "Online appointment booking",
            "Doctor schedule management",
            "Appointment slot generation",
            "Patient consultation history",
            "Real-time availability checking"
        ]
    }
# main.py
from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
import schemas
from database import get_db, init_db
from models import User, Patient, Doctor, Measurement, Prescription, Complaint, Appointment, Diagnosis, PatientDiagnosis
from utils import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, verify_token, get_current_user,
    require_role, safe_str
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


# ========== БАЗОВЫЕ МЕТОДЫ API ==========

@app.get("/")
async def root():
    return {"message": "Medical API работает"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/auth/register", response_model=schemas.UserResponse)
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже существует")

    # Создаем пользователя
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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


@app.post("/auth/refresh", response_model=schemas.Token)
async def refresh_token(refresh_data: schemas.RefreshToken, db: Session = Depends(get_db)):
    try:
        payload = verify_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Неверный тип токена")

        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        new_refresh_token = create_refresh_token(data={"sub": user.email})

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "role": user.role,
            "email": user.email
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Невалидный refresh токен")


@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # В реальном приложении здесь можно добавить токен в черный список
    return {"message": "Успешный выход из системы"}


# ========== ФУНКЦИОНАЛ ДЛЯ ПАЦИЕНТОВ ==========

@app.get("/patients/me/medical-card", response_model=schemas.MedicalCardResponse)
async def get_my_medical_card(
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Просмотр персональной медицинской карты"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    patient = db.query(Patient).filter(Patient.id == current_user.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")

    measurements = db.query(Measurement).filter(
        Measurement.patient_id == patient.id
    ).order_by(Measurement.measured_at.desc()).limit(50).all()

    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient.id,
        Prescription.status == 'активно'
    ).order_by(Prescription.start_date.desc()).all()

    complaints = db.query(Complaint).filter(
        Complaint.patient_id == patient.id
    ).order_by(Complaint.complaint_date.desc()).limit(30).all()

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient.id,
        Appointment.status == 'запланировано'
    ).order_by(Appointment.appointment_date).all()

    diagnoses = db.query(PatientDiagnosis).filter(
        PatientDiagnosis.patient_id == patient.id
    ).order_by(PatientDiagnosis.diagnosed_at.desc()).all()

    return {
        "patient": patient,
        "measurements": measurements,
        "prescriptions": prescriptions,
        "complaints": complaints,
        "appointments": appointments,
        "diagnoses": diagnoses
    }


@app.post("/patients/me/measurements", response_model=schemas.MeasurementResponse)
async def create_self_measurement(
        measurement_data: schemas.MeasurementCreate,
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Ввод данных самоконтроля"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    if measurement_data.patient_id != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Нельзя добавлять измерения для другого пациента")

    measurement = Measurement(
        **measurement_data.model_dump(),
        measured_at=measurement_data.measured_at or datetime.utcnow()
    )

    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@app.get("/patients/me/prescriptions", response_model=List[schemas.PrescriptionResponse])
async def get_my_prescriptions(
        status: Optional[str] = Query(None, description="Фильтр по статусу"),
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Отслеживание текущих назначений"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    query = db.query(Prescription).filter(Prescription.patient_id == current_user.patient_id)

    if status:
        query = query.filter(Prescription.status == status)

    prescriptions = query.order_by(Prescription.start_date.desc()).all()

    # Добавляем информацию о враче
    for prescription in prescriptions:
        if prescription.doctor:
            prescription.doctor_info = {
                "surname": prescription.doctor.surname,
                "name": prescription.doctor.name,
                "specialization": prescription.doctor.specialization
            }

    return prescriptions


@app.post("/patients/me/complaints", response_model=schemas.ComplaintResponse)
async def create_self_complaint(
        complaint_data: schemas.ComplaintCreate,
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Ведение дневника самочувствия"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    if complaint_data.patient_id != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Нельзя добавлять жалобы для другого пациента")

    complaint = Complaint(
        **complaint_data.model_dump(),
        complaint_date=complaint_data.complaint_date or datetime.utcnow()
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@app.get("/patients/me/appointments", response_model=List[schemas.AppointmentResponse])
async def get_my_appointments(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Просмотр истории визитов и планирование"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    query = db.query(Appointment).filter(Appointment.patient_id == current_user.patient_id)

    if start_date:
        query = query.filter(Appointment.appointment_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Appointment.appointment_date <= datetime.combine(end_date, datetime.max.time()))
    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    return appointments


@app.post("/patients/me/appointments", response_model=schemas.AppointmentResponse)
async def create_appointment_request(
        appointment_data: schemas.AppointmentCreate,
        current_user: User = Depends(require_role("patient")),
        db: Session = Depends(get_db)
):
    """Запрос на консультацию"""
    if not current_user.patient_id:
        raise HTTPException(status_code=404, detail="Профиль пациента не найден")

    if appointment_data.patient_id != current_user.patient_id:
        raise HTTPException(status_code=403, detail="Нельзя создавать запись для другого пациента")

    # Проверяем доступность врача
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment_data.doctor_id,
        Appointment.appointment_date == appointment_data.appointment_date,
        Appointment.status.in_(["запланировано", "подтверждено"])
    ).first()

    if existing_appointment:
        raise HTTPException(status_code=400, detail="Врач занят в это время")

    appointment = Appointment(**appointment_data.model_dump())

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


# ========== ФУНКЦИОНАЛ ДЛЯ ВРАЧЕЙ ==========

@app.get("/doctors/patients", response_model=List[schemas.PatientResponse])
async def get_doctor_patients(
        search: Optional[str] = Query(None, description="Поиск по ФИО или email"),
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Управление списком пациентов с фильтрацией"""
    if not current_user.doctor_id:
        raise HTTPException(status_code=404, detail="Профиль врача не найден")

    query = db.query(Patient)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Patient.surname.ilike(search_term)) |
            (Patient.name.ilike(search_term)) |
            (Patient.patronim.ilike(search_term)) |
            (Patient.email.ilike(search_term))
        )

    # Получаем пациентов, у которых есть назначения от этого врача
    doctor_prescriptions = db.query(Prescription.patient_id).filter(
        Prescription.doctor_id == current_user.doctor_id
    ).distinct()

    patient_ids = [p[0] for p in doctor_prescriptions.all()]
    if patient_ids:
        query = query.filter(Patient.id.in_(patient_ids))

    patients = query.order_by(Patient.surname, Patient.name).all()
    return patients


@app.get("/doctors/patients/{patient_id}/medical-card", response_model=schemas.MedicalCardResponse)
async def get_patient_medical_card(
        patient_id: int,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Просмотр детализированной медицинской карты пациента"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")

    # Проверяем, что у врача есть доступ к этому пациенту
    has_access = db.query(Prescription).filter(
        Prescription.doctor_id == current_user.doctor_id,
        Prescription.patient_id == patient_id
    ).first()

    if not has_access and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Нет доступа к медицинской карте этого пациента")

    measurements = db.query(Measurement).filter(
        Measurement.patient_id == patient_id
    ).order_by(Measurement.measured_at.desc()).limit(100).all()

    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == patient_id
    ).order_by(Prescription.start_date.desc()).all()

    complaints = db.query(Complaint).filter(
        Complaint.patient_id == patient_id
    ).order_by(Complaint.complaint_date.desc()).all()

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(Appointment.appointment_date.desc()).all()

    diagnoses = db.query(PatientDiagnosis).filter(
        PatientDiagnosis.patient_id == patient_id
    ).order_by(PatientDiagnosis.diagnosed_at.desc()).all()

    return {
        "patient": patient,
        "measurements": measurements,
        "prescriptions": prescriptions,
        "complaints": complaints,
        "appointments": appointments,
        "diagnoses": diagnoses
    }


@app.post("/doctors/prescriptions", response_model=schemas.PrescriptionResponse)
async def create_prescription(
        prescription_data: schemas.PrescriptionCreate,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Формирование медицинских назначений"""
    if not current_user.doctor_id:
        raise HTTPException(status_code=404, detail="Профиль врача не найден")

    if prescription_data.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Нельзя создавать назначения от имени другого врача")

    # Проверяем существование пациента
    patient = db.query(Patient).filter(Patient.id == prescription_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")

    prescription = Prescription(**prescription_data.model_dump())

    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


@app.put("/doctors/prescriptions/{prescription_id}", response_model=schemas.PrescriptionResponse)
async def update_prescription(
        prescription_id: int,
        prescription_data: schemas.PrescriptionBase,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Коррекция медицинских назначений"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Назначение не найдено")

    if prescription.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать назначения другого врача")

    for field, value in prescription_data.model_dump().items():
        setattr(prescription, field, value)

    prescription.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(prescription)
    return prescription


@app.get("/doctors/patients/{patient_id}/statistics")
async def get_patient_statistics(
        patient_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Анализ динамики состояния пациента"""
    # Проверяем доступ
    has_access = db.query(Prescription).filter(
        Prescription.doctor_id == current_user.doctor_id,
        Prescription.patient_id == patient_id
    ).first()

    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к статистике этого пациента")

    # Получаем измерения
    query = db.query(Measurement).filter(Measurement.patient_id == patient_id)

    if start_date:
        query = query.filter(Measurement.measured_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Measurement.measured_at <= datetime.combine(end_date, datetime.max.time()))

    measurements = query.order_by(Measurement.measured_at).all()

    # Формируем статистику
    stats = {
        "total_measurements": len(measurements),
        "glucose_stats": [],
        "blood_pressure_stats": [],
        "weight_stats": []
    }

    for m in measurements:
        if m.glucose is not None:
            stats["glucose_stats"].append({
                "date": m.measured_at,
                "value": m.glucose
            })
        if m.systolic_bp is not None and m.diastolic_bp is not None:
            stats["blood_pressure_stats"].append({
                "date": m.measured_at,
                "systolic": m.systolic_bp,
                "diastolic": m.diastolic_bp
            })
        if m.weight is not None:
            stats["weight_stats"].append({
                "date": m.measured_at,
                "value": m.weight
            })

    return stats


@app.get("/doctors/appointments", response_model=List[schemas.AppointmentResponse])
async def get_doctor_appointments(
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status: Optional[str] = None,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Планирование консультаций и визитов"""
    if not current_user.doctor_id:
        raise HTTPException(status_code=404, detail="Профиль врача не найден")

    query = db.query(Appointment).filter(Appointment.doctor_id == current_user.doctor_id)

    if date_from:
        query = query.filter(Appointment.appointment_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Appointment.appointment_date <= datetime.combine(date_to, datetime.max.time()))
    if status:
        query = query.filter(Appointment.status == status)

    appointments = query.order_by(Appointment.appointment_date).all()
    return appointments


@app.post("/doctors/appointments", response_model=schemas.AppointmentResponse)
async def create_doctor_appointment(
        appointment_data: schemas.AppointmentCreate,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Создание консультации врачом"""
    if not current_user.doctor_id:
        raise HTTPException(status_code=404, detail="Профиль врача не найден")

    if appointment_data.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Нельзя создавать записи для другого врача")

    # Проверяем доступность
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment_data.doctor_id,
        Appointment.appointment_date == appointment_data.appointment_date,
        Appointment.status.in_(["запланировано", "подтверждено"])
    ).first()

    if existing_appointment:
        raise HTTPException(status_code=400, detail="В это время уже есть запись")

    appointment = Appointment(**appointment_data.model_dump())

    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@app.put("/doctors/appointments/{appointment_id}", response_model=schemas.AppointmentResponse)
async def update_appointment(
        appointment_id: int,
        appointment_data: schemas.AppointmentBase,
        current_user: User = Depends(require_role("doctor")),
        db: Session = Depends(get_db)
):
    """Обновление консультации"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    if appointment.doctor_id != current_user.doctor_id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать записи другого врача")

    for field, value in appointment_data.model_dump().items():
        setattr(appointment, field, value)

    appointment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(appointment)
    return appointment


# ========== ОБЩИЕ МЕТОДЫ ==========

@app.get("/patients", response_model=List[schemas.PatientResponse])
async def get_patients(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список пациентов (только для врачей и админов)"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients


@app.get("/doctors", response_model=List[schemas.DoctorResponse])
async def get_doctors(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список врачей"""
    doctors = db.query(Doctor).offset(skip).limit(limit).all()
    return doctors


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
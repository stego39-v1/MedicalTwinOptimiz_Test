# app/routes/self_monitoring.py
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
from app.models import Patient

router = APIRouter(prefix="/self-monitoring", tags=["self monitoring"])


# ========== ДЛЯ ПАЦИЕНТОВ ==========

@router.post("/my/record", response_model=schemas.SelfMonitoring)
def create_my_self_monitoring(
        monitoring: schemas.SelfMonitoringCreate,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)  # Только пациенты
):
    """
    Пациент создает запись самоконтроля
    """
    # Находим пациента по email пользователя
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient profile not found. Please complete your profile first."
        )

    # Проверяем, не существует ли уже запись на эту дату и время
    if monitoring.measurement_time:
        existing = db.query(crud.models.SelfMonitoring).filter(
            crud.models.SelfMonitoring.patient_id == patient.id,
            crud.models.SelfMonitoring.measurement_date == monitoring.measurement_date,
            crud.models.SelfMonitoring.measurement_time == monitoring.measurement_time
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Record already exists for this date and time"
            )

    return crud.create_self_monitoring(db, monitoring, patient.id)


@router.get("/my/records", response_model=List[schemas.SelfMonitoring])
def get_my_self_monitoring(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        start_date: Optional[date] = Query(None, description="Начальная дата периода"),
        end_date: Optional[date] = Query(None, description="Конечная дата периода"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)  # Только пациенты
):
    """
    Пациент получает свои записи самоконтроля
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_patient_self_monitoring(
        db, patient.id, skip, limit, start_date, end_date
    )


@router.get("/my/today", response_model=List[schemas.SelfMonitoring])
def get_my_todays_monitoring(
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает сегодняшние записи самоконтроля
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_todays_monitoring(db, patient.id)


@router.get("/my/stats")
def get_my_monitoring_stats(
        days: int = Query(30, ge=1, le=365, description="Период в днях"),
        metric: Optional[str] = Query(None, description="Конкретная метрика для статистики"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает статистику своих показателей
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    return crud.get_monitoring_stats(db, patient.id, days, metric)


@router.get("/my/trend/{metric}")
def get_my_monitoring_trend(
        metric: str,
        days: int = Query(7, ge=1, le=90, description="Период в днях"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает тренд конкретного показателя
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    trend = crud.get_monitoring_trend(db, patient.id, metric, days)
    if not trend:
        raise HTTPException(status_code=400, detail="Invalid metric or no data")

    return trend


@router.get("/my/daily-summary/{target_date}")
def get_my_daily_summary(
        target_date: date,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент получает дневную сводку по показателям
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Получаем записи за указанную дату
    records = crud.get_patient_self_monitoring(
        db, patient.id, start_date=target_date, end_date=target_date
    )

    if not records:
        raise HTTPException(status_code=404, detail="No records for this date")

    # Анализируем записи
    alerts = []
    for record in records:
        alerts.extend(record.alert_messages)

    # Формируем рекомендации
    recommendations = []

    # Проверяем давление
    bp_records = [r for r in records if r.blood_pressure_systolic]
    if bp_records:
        avg_systolic = sum(r.blood_pressure_systolic for r in bp_records) / len(bp_records)
        if avg_systolic > 140:
            recommendations.append("Повышенное давление. Рекомендуется отдых и консультация врача.")
        elif avg_systolic < 100:
            recommendations.append("Пониженное давление. Рекомендуется увеличить потребление жидкости.")

    # Проверяем сахар
    sugar_records = [r for r in records if r.blood_sugar]
    if sugar_records:
        avg_sugar = sum(r.blood_sugar for r in sugar_records) / len(sugar_records)
        if avg_sugar > 7.8:
            recommendations.append("Повышенный уровень сахара. Соблюдайте диету.")
        elif avg_sugar < 4.0:
            recommendations.append("Пониженный уровень сахара. Рекомендуется перекус.")

    # Проверяем температуру
    temp_records = [r for r in records if r.body_temperature]
    if temp_records:
        max_temp = max(r.body_temperature for r in temp_records)
        if max_temp > 37.5:
            recommendations.append("Повышенная температура. Отдыхайте и пейте больше жидкости.")

    return {
        "date": target_date,
        "measurements_count": len(records),
        "alerts_count": len(set(alerts)),
        "critical_alerts": list(set(alerts)),
        "recommendations": recommendations,
        "patient_name": f"{patient.last_name} {patient.first_name}"
    }


@router.put("/my/record/{monitoring_id}", response_model=schemas.SelfMonitoring)
def update_my_self_monitoring(
        monitoring_id: int,
        monitoring_update: schemas.SelfMonitoringUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент обновляет свою запись самоконтроля
    """
    # Проверяем, что запись принадлежит пациенту
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    monitoring = crud.get_self_monitoring(db, monitoring_id)
    if not monitoring:
        raise HTTPException(status_code=404, detail="Monitoring record not found")

    if monitoring.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this record")

    return crud.update_self_monitoring(db, monitoring_id, monitoring_update)


@router.delete("/my/record/{monitoring_id}")
def delete_my_self_monitoring(
        monitoring_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(auth.patient_only)
):
    """
    Пациент удаляет свою запись самоконтроля
    """
    patient = db.query(Patient).filter(Patient.email == current_user.email).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    monitoring = crud.get_self_monitoring(db, monitoring_id)
    if not monitoring:
        raise HTTPException(status_code=404, detail="Monitoring record not found")

    if monitoring.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")

    crud.delete_self_monitoring(db, monitoring_id)
    return {"message": "Monitoring record deleted successfully"}


# ========== ДЛЯ ВРАЧЕЙ ==========

@router.get("/patient/{patient_id}/records", response_model=List[schemas.SelfMonitoring])
def get_patient_self_monitoring(
        patient_id: int,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)  # Только врачи и админы
):
    """
    Врач получает записи самоконтроля пациента
    """
    return crud.get_patient_self_monitoring(
        db, patient_id, skip, limit, start_date, end_date
    )


@router.get("/patient/{patient_id}/alerts")
def get_patient_alerts(
        patient_id: int,
        days: int = Query(7, ge=1, le=90),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач получает тревожные показатели пациента
    """
    start_date = date.today() - timedelta(days=days)

    records = crud.get_patient_self_monitoring(
        db, patient_id, start_date=start_date, end_date=date.today()
    )

    alerts = []
    for record in records:
        if record.is_alert:
            alerts.append({
                "id": record.id,
                "date": record.measurement_date,
                "time": record.measurement_time,
                "alerts": record.alert_messages,
                "patient_id": record.patient_id
            })

    return {
        "patient_id": patient_id,
        "period_days": days,
        "total_alerts": len(alerts),
        "alerts": alerts
    }


@router.get("/patient/{patient_id}/stats")
def get_patient_monitoring_stats(
        patient_id: int,
        days: int = Query(30, ge=1, le=365),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """
    Врач получает статистику показателей пациента
    """
    return crud.get_monitoring_stats(db, patient_id, days)


@router.post("/quick-record", response_model=schemas.SelfMonitoring)
def create_quick_monitoring_record(
        patient_id: int,
        blood_pressure_systolic: Optional[int] = Query(None, ge=50, le=250),
        blood_pressure_diastolic: Optional[int] = Query(None, ge=30, le=150),
        heart_rate: Optional[int] = Query(None, ge=30, le=200),
        body_temperature: Optional[float] = Query(None, ge=35.0, le=42.0),
        blood_sugar: Optional[float] = Query(None, ge=2.0, le=30.0),
        notes: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)  # Только врачи и админы
):
    """
    Быстрая запись показателей (например, при визите пациента)
    """
    monitoring_data = schemas.SelfMonitoringCreate(
        measurement_date=date.today(),
        blood_pressure_systolic=blood_pressure_systolic,
        blood_pressure_diastolic=blood_pressure_diastolic,
        heart_rate=heart_rate,
        body_temperature=body_temperature,
        blood_sugar=blood_sugar,
        notes=notes or f"Запись при визите. Врач: {current_user.full_name}"
    )

    return crud.create_self_monitoring(db, monitoring_data, patient_id)


# ========== ОБЩИЕ ЭНДПОИНТЫ ==========

@router.get("/test")
def test_self_monitoring():
    """Тестовый эндпоинт"""
    return {
        "status": "ok",
        "message": "Self-monitoring API is working",
        "features": [
            "Daily health tracking",
            "Alert system for abnormal values",
            "Statistics and trends",
            "Doctor access to patient data"
        ]
    }


@router.get("/metrics-info")
def get_metrics_info():
    """Информация о доступных метриках"""
    return {
        "available_metrics": [
            {
                "name": "blood_pressure_systolic",
                "display_name": "Систолическое давление",
                "unit": "мм рт. ст.",
                "normal_range": "90-140",
                "description": "Верхнее значение артериального давления"
            },
            {
                "name": "blood_pressure_diastolic",
                "display_name": "Диастолическое давление",
                "unit": "мм рт. ст.",
                "normal_range": "60-90",
                "description": "Нижнее значение артериального давления"
            },
            {
                "name": "heart_rate",
                "display_name": "Пульс",
                "unit": "уд/мин",
                "normal_range": "60-100",
                "description": "Частота сердечных сокращений"
            },
            {
                "name": "body_temperature",
                "display_name": "Температура тела",
                "unit": "°C",
                "normal_range": "36.0-37.2",
                "description": "Температура тела"
            },
            {
                "name": "blood_sugar",
                "display_name": "Уровень сахара в крови",
                "unit": "ммоль/л",
                "normal_range": "3.9-6.1",
                "description": "Глюкоза в крови натощак"
            },
            {
                "name": "oxygen_saturation",
                "display_name": "Сатурация кислорода",
                "unit": "%",
                "normal_range": "95-100",
                "description": "Насыщение крови кислородом"
            },
            {
                "name": "weight",
                "display_name": "Вес",
                "unit": "кг",
                "normal_range": "Индивидуально",
                "description": "Масса тела"
            }
        ]
    }
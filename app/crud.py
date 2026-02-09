from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract
from collections import defaultdict


# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role if user.role else "patient"  # Добавляем роль
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Patient CRUD
def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()


def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def update_patient(db: Session, patient_id: int, patient_update: schemas.PatientCreate):
    db_patient = get_patient(db, patient_id)
    if db_patient:
        for key, value in patient_update.model_dump().items():
            setattr(db_patient, key, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient


def delete_patient(db: Session, patient_id: int):
    db_patient = get_patient(db, patient_id)
    if db_patient:
        db.delete(db_patient)
        db.commit()
    return db_patient


# Doctor CRUD
def get_doctor(db: Session, doctor_id: int):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()


def get_doctors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Doctor).offset(skip).limit(limit).all()


def get_doctors_by_specialty(db: Session, specialty: str):
    return db.query(models.Doctor).filter(models.Doctor.specialty == specialty).all()


def create_doctor(db: Session, doctor: schemas.DoctorCreate):
    db_doctor = models.Doctor(**doctor.model_dump())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


# Diagnosis CRUD
def get_diagnosis(db: Session, diagnosis_id: int):
    return db.query(models.Diagnosis).filter(models.Diagnosis.id == diagnosis_id).first()


def get_diagnosis_by_icd(db: Session, icd_code: str):
    return db.query(models.Diagnosis).filter(models.Diagnosis.icd_code == icd_code).first()


def get_diagnoses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Diagnosis).offset(skip).limit(limit).all()


def get_diagnoses_by_category(db: Session, category: str):
    return db.query(models.Diagnosis).filter(models.Diagnosis.category == category).all()


def create_diagnosis(db: Session, diagnosis: schemas.DiagnosisCreate):
    db_diagnosis = models.Diagnosis(**diagnosis.model_dump())
    db.add(db_diagnosis)
    db.commit()
    db.refresh(db_diagnosis)
    return db_diagnosis


# Symptom CRUD
def get_symptom(db: Session, symptom_id: int):
    return db.query(models.Symptom).filter(models.Symptom.id == symptom_id).first()


def get_symptoms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Symptom).offset(skip).limit(limit).all()


def get_symptoms_by_category(db: Session, category: str):
    return db.query(models.Symptom).filter(models.Symptom.category_name == category).all()


def create_symptom(db: Session, symptom: schemas.SymptomCreate):
    db_symptom = models.Symptom(**symptom.model_dump())
    db.add(db_symptom)
    db.commit()
    db.refresh(db_symptom)
    return db_symptom


# PatientComplaint CRUD
def get_patient_complaint(db: Session, complaint_id: int):
    return db.query(models.PatientComplaint).filter(models.PatientComplaint.id == complaint_id).first()


def get_patient_complaints(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PatientComplaint).offset(skip).limit(limit).all()


def get_complaints_by_patient(db: Session, patient_id: int):
    return db.query(models.PatientComplaint).filter(models.PatientComplaint.patient_id == patient_id).all()


def create_patient_complaint(db: Session, complaint: schemas.PatientComplaintCreate):
    # Найдем пациента по ФИО
    patient = db.query(models.Patient).filter(
        models.Patient.last_name == complaint.patient_last_name,
        models.Patient.first_name == complaint.patient_first_name,
        models.Patient.middle_name == complaint.patient_middle_name
    ).first()

    db_complaint = models.PatientComplaint(
        **complaint.model_dump(),
        patient_id=patient.id if patient else None
    )
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    return db_complaint


# Prescription CRUD
def get_prescription(db: Session, prescription_id: int):
    return db.query(models.Prescription).filter(models.Prescription.id == prescription_id).first()


def get_prescriptions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Prescription).offset(skip).limit(limit).all()


def get_prescriptions_by_patient(db: Session, patient_id: int):
    return db.query(models.Prescription).filter(models.Prescription.patient_id == patient_id).all()


def get_prescriptions_by_doctor(db: Session, doctor_id: int):
    return db.query(models.Prescription).filter(models.Prescription.doctor_id == doctor_id).all()


def get_prescriptions_by_status(db: Session, status: str):
    return db.query(models.Prescription).filter(models.Prescription.status == status).all()


def create_prescription(db: Session, prescription: schemas.PrescriptionCreate):
    # Найдем пациента и врача по ФИО
    patient = db.query(models.Patient).filter(
        models.Patient.last_name == prescription.patient_last_name,
        models.Patient.first_name == prescription.patient_first_name,
        models.Patient.middle_name == prescription.patient_middle_name
    ).first()

    doctor = db.query(models.Doctor).filter(
        models.Doctor.last_name == prescription.doctor_last_name,
        models.Doctor.first_name == prescription.doctor_first_name,
        models.Doctor.middle_name == prescription.doctor_middle_name
    ).first()

    db_prescription = models.Prescription(
        **prescription.model_dump(),
        patient_id=patient.id if patient else None,
        doctor_id=doctor.id if doctor else None
    )
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription


def update_prescription_status(db: Session, prescription_id: int, status: str):
    db_prescription = get_prescription(db, prescription_id)
    if db_prescription:
        db_prescription.status = status
        db.commit()
        db.refresh(db_prescription)
    return db_prescription


def update_user_role(db: Session, user_id: int, role: str):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.role = role
        db.commit()
        db.refresh(db_user)
    return db_user


# Medical Record CRUD
def get_patient_medical_record(db: Session, patient_id: int):
    """Получает полную медицинскую карту пациента"""
    # Получаем информацию о пациенте
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    # Получаем все жалобы пациента
    complaints = get_complaints_by_patient(db, patient_id)

    # Получаем все рецепты пациента
    prescriptions = get_prescriptions_by_patient(db, patient_id)

    # Для диагнозов нужно будет добавить связь с пациентами
    # Пока вернем все диагнозы (в будущем можно связать через отдельную таблицу)
    diagnoses = get_diagnoses(db, skip=0, limit=100)

    return {
        "patient": patient,
        "complaints": complaints,
        "prescriptions": prescriptions,
        "diagnoses": diagnoses[:10]  # Ограничим для примера
    }


def get_patient_treatment_history(db: Session, patient_id: int):
    """Получает историю лечения пациента в хронологическом порядке"""
    # Получаем жалобы пациента
    complaints = get_complaints_by_patient(db, patient_id)

    # Получаем рецепты пациента
    prescriptions = get_prescriptions_by_patient(db, patient_id)

    # Создаем единый список событий
    history = []

    # Добавляем жалобы
    for complaint in complaints:
        history.append({
            "date": complaint.complaint_date,
            "type": "complaint",
            "description": f"Жалоба: {complaint.symptom_name}",
            "doctor_name": None,  # У жалоб нет врача
            "details": {
                "symptom": complaint.symptom_name,
                "severity": complaint.severity,
                "description": complaint.description
            }
        })

    # Добавляем рецепты
    for prescription in prescriptions:
        history.append({
            "date": prescription.start_date,
            "type": "prescription",
            "description": f"Рецепт: {prescription.medication_name}",
            "doctor_name": f"{prescription.doctor_last_name} {prescription.doctor_first_name}",
            "details": {
                "medication": prescription.medication_name,
                "quantity": prescription.quantity,
                "instructions": prescription.instructions,
                "status": prescription.status
            }
        })

    # Сортируем по дате (от новых к старым)
    history.sort(key=lambda x: x["date"], reverse=True)

    return history


def get_patient_summary(db: Session, patient_id: int):
    """Получает сводную информацию о пациенте"""
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    complaints = get_complaints_by_patient(db, patient_id)
    prescriptions = get_prescriptions_by_patient(db, patient_id)
    diagnoses = get_diagnoses(db, skip=0, limit=5)  # Последние 5 диагнозов

    # Считаем активные рецепты
    active_prescriptions = len([p for p in prescriptions if p.status.lower() == "active"])

    # Находим дату последнего визита
    last_visit_date = None
    if complaints:
        last_complaint = max(complaints, key=lambda x: x.complaint_date)
        last_visit_date = last_complaint.complaint_date

    return {
        "patient": patient,
        "total_complaints": len(complaints),
        "total_prescriptions": len(prescriptions),
        "active_prescriptions": active_prescriptions,
        "recent_diagnoses": diagnoses,
        "last_visit_date": last_visit_date
    }


def get_patient_timeline(db: Session, patient_id: int, months: int = 12):
    """Получает временную шкалу лечения за указанный период"""
    # Рассчитываем дату начала периода
    end_date = date.today()
    start_date = end_date - relativedelta(months=months)

    # Получаем данные за период
    complaints = db.query(models.PatientComplaint).filter(
        models.PatientComplaint.patient_id == patient_id,
        models.PatientComplaint.complaint_date >= start_date,
        models.PatientComplaint.complaint_date <= end_date
    ).all()

    prescriptions = db.query(models.Prescription).filter(
        models.Prescription.patient_id == patient_id,
        models.Prescription.start_date >= start_date,
        models.Prescription.start_date <= end_date
    ).all()

    # Группируем по месяцам
    timeline = {}

    for complaint in complaints:
        month_key = complaint.complaint_date.strftime("%Y-%m")
        if month_key not in timeline:
            timeline[month_key] = {"complaints": 0, "prescriptions": 0, "visits": 0}
        timeline[month_key]["complaints"] += 1
        timeline[month_key]["visits"] += 1

    for prescription in prescriptions:
        month_key = prescription.start_date.strftime("%Y-%m")
        if month_key not in timeline:
            timeline[month_key] = {"complaints": 0, "prescriptions": 0, "visits": 0}
        timeline[month_key]["prescriptions"] += 1

    # Преобразуем в список и сортируем
    timeline_list = [
        {
            "month": month,
            "year": int(month.split("-")[0]),
            "month_num": int(month.split("-")[1]),
            **data
        }
        for month, data in timeline.items()
    ]

    timeline_list.sort(key=lambda x: (x["year"], x["month_num"]), reverse=True)

    return timeline_list


def create_self_monitoring(db: Session, monitoring: schemas.SelfMonitoringCreate, patient_id: int):
    """Создает запись самоконтроля"""
    db_monitoring = models.SelfMonitoring(
        patient_id=patient_id,
        **monitoring.model_dump(exclude={"patient_id"})
    )

    # Проверяем тревожные показатели
    alerts = db_monitoring.check_alert_conditions()
    db_monitoring.is_alert = len(alerts) > 0

    db.add(db_monitoring)
    db.commit()
    db.refresh(db_monitoring)

    # Добавляем сообщения об алертах
    db_monitoring.alert_messages = alerts

    return db_monitoring


def get_self_monitoring(db: Session, monitoring_id: int):
    """Получает запись самоконтроля по ID"""
    monitoring = db.query(models.SelfMonitoring).filter(models.SelfMonitoring.id == monitoring_id).first()
    if monitoring:
        monitoring.alert_messages = monitoring.check_alert_conditions()
    return monitoring


def get_patient_self_monitoring(
        db: Session,
        patient_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
):
    """Получает все записи самоконтроля пациента"""
    query = db.query(models.SelfMonitoring).filter(
        models.SelfMonitoring.patient_id == patient_id
    )

    if start_date:
        query = query.filter(models.SelfMonitoring.measurement_date >= start_date)
    if end_date:
        query = query.filter(models.SelfMonitoring.measurement_date <= end_date)

    records = query.order_by(
        models.SelfMonitoring.measurement_date.desc(),
        models.SelfMonitoring.measurement_time.desc()
    ).offset(skip).limit(limit).all()

    # Добавляем сообщения об алертах
    for record in records:
        record.alert_messages = record.check_alert_conditions()

    return records


def update_self_monitoring(db: Session, monitoring_id: int, monitoring_update: schemas.SelfMonitoringUpdate):
    """Обновляет запись самоконтроля"""
    db_monitoring = get_self_monitoring(db, monitoring_id)
    if db_monitoring:
        update_data = monitoring_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_monitoring, key, value)

        # Проверяем тревожные показатели после обновления
        alerts = db_monitoring.check_alert_conditions()
        db_monitoring.is_alert = len(alerts) > 0
        db_monitoring.alert_messages = alerts

        db.commit()
        db.refresh(db_monitoring)
    return db_monitoring


def delete_self_monitoring(db: Session, monitoring_id: int):
    """Удаляет запись самоконтроля"""
    db_monitoring = get_self_monitoring(db, monitoring_id)
    if db_monitoring:
        db.delete(db_monitoring)
        db.commit()
    return db_monitoring


def get_todays_monitoring(db: Session, patient_id: int):
    """Получает сегодняшние записи самоконтроля пациента"""
    today = date.today()

    records = db.query(models.SelfMonitoring).filter(
        models.SelfMonitoring.patient_id == patient_id,
        models.SelfMonitoring.measurement_date == today
    ).order_by(models.SelfMonitoring.measurement_time.desc()).all()

    for record in records:
        record.alert_messages = record.check_alert_conditions()

    return records


def get_monitoring_stats(
        db: Session,
        patient_id: int,
        days: int = 30,
        metric: Optional[str] = None
):
    """Получает статистику по показателям за период"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Базовый запрос
    query = db.query(models.SelfMonitoring).filter(
        models.SelfMonitoring.patient_id == patient_id,
        models.SelfMonitoring.measurement_date >= start_date,
        models.SelfMonitoring.measurement_date <= end_date
    )

    stats = {
        "period": f"{days} дней",
        "total_measurements": query.count(),
        "alerts_count": query.filter(models.SelfMonitoring.is_alert == True).count(),
        "metrics": {}
    }

    # Статистика по конкретным метрикам
    metrics_to_check = [
        'blood_pressure_systolic', 'blood_pressure_diastolic',
        'heart_rate', 'body_temperature', 'blood_sugar', 'weight'
    ]

    for metric_name in metrics_to_check:
        if metric and metric != metric_name:
            continue

        # Получаем только записи с заполненной метрикой
        metric_query = query.filter(getattr(models.SelfMonitoring, metric_name) != None)

        if metric_query.count() > 0:
            # Среднее значение
            avg_value = db.query(
                func.avg(getattr(models.SelfMonitoring, metric_name))
            ).filter(
                models.SelfMonitoring.patient_id == patient_id,
                models.SelfMonitoring.measurement_date >= start_date,
                models.SelfMonitoring.measurement_date <= end_date,
                getattr(models.SelfMonitoring, metric_name) != None
            ).scalar()

            # Минимум и максимум
            min_value = db.query(
                func.min(getattr(models.SelfMonitoring, metric_name))
            ).filter(
                models.SelfMonitoring.patient_id == patient_id,
                models.SelfMonitoring.measurement_date >= start_date,
                models.SelfMonitoring.measurement_date <= end_date,
                getattr(models.SelfMonitoring, metric_name) != None
            ).scalar()

            max_value = db.query(
                func.max(getattr(models.SelfMonitoring, metric_name))
            ).filter(
                models.SelfMonitoring.patient_id == patient_id,
                models.SelfMonitoring.measurement_date >= start_date,
                models.SelfMonitoring.measurement_date <= end_date,
                getattr(models.SelfMonitoring, metric_name) != None
            ).scalar()

            stats["metrics"][metric_name] = {
                "average": round(avg_value, 2) if avg_value else None,
                "min": min_value,
                "max": max_value,
                "count": metric_query.count()
            }

    return stats


def get_monitoring_trend(
        db: Session,
        patient_id: int,
        metric: str,
        days: int = 7
):
    """Получает тренд показателя за период"""
    if metric not in ['blood_pressure_systolic', 'blood_pressure_diastolic',
                      'heart_rate', 'body_temperature', 'blood_sugar', 'weight']:
        return None

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Группируем по дате и получаем среднее значение за день
    results = db.query(
        models.SelfMonitoring.measurement_date,
        func.avg(getattr(models.SelfMonitoring, metric)).label('avg_value')
    ).filter(
        models.SelfMonitoring.patient_id == patient_id,
        models.SelfMonitoring.measurement_date >= start_date,
        models.SelfMonitoring.measurement_date <= end_date,
        getattr(models.SelfMonitoring, metric) != None
    ).group_by(
        models.SelfMonitoring.measurement_date
    ).order_by(
        models.SelfMonitoring.measurement_date
    ).all()

    # Подготавливаем данные для графика
    dates = []
    values = []

    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)

        # Ищем значение для этой даты
        value = None
        for result in results:
            if result.measurement_date == current_date:
                value = round(result.avg_value, 2)
                break

        values.append(value)
        current_date += timedelta(days=1)

    # Определяем единицы измерения
    units = {
        'blood_pressure_systolic': 'мм рт. ст.',
        'blood_pressure_diastolic': 'мм рт. ст.',
        'heart_rate': 'уд/мин',
        'body_temperature': '°C',
        'blood_sugar': 'ммоль/л',
        'weight': 'кг'
    }

    return {
        "dates": dates,
        "values": values,
        "metric_name": metric,
        "unit": units.get(metric, ''),
        "period_days": days
    }


def create_appointment(db: Session, appointment: schemas.AppointmentCreate, patient_id: int):
    """Создает медицинское назначение"""
    # Рассчитываем следующую дату выполнения
    next_due_date = appointment.start_date

    db_appointment = models.MedicalAppointment(
        patient_id=patient_id,
        **appointment.model_dump(exclude={"patient_id"})
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # Создаем напоминания если включены
    if db_appointment.reminder_enabled and db_appointment.reminder_time:
        create_appointment_reminders(db, db_appointment.id)

    return db_appointment


def get_appointment(db: Session, appointment_id: int):
    """Получает назначение по ID"""
    return db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.id == appointment_id
    ).first()


def get_patient_appointments(
        db: Session,
        patient_id: int,
        status: Optional[str] = None,
        appointment_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
):
    """Получает все назначения пациента"""
    query = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id
    )

    if status:
        query = query.filter(models.MedicalAppointment.status == status)
    if appointment_type:
        query = query.filter(models.MedicalAppointment.appointment_type == appointment_type)

    return query.order_by(
        models.MedicalAppointment.priority.desc(),
        models.MedicalAppointment.next_due_date.asc()
    ).offset(skip).limit(limit).all()


def update_appointment(db: Session, appointment_id: int, appointment_update: schemas.AppointmentUpdate):
    """Обновляет назначение"""
    db_appointment = get_appointment(db, appointment_id)
    if db_appointment:
        update_data = appointment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_appointment, key, value)

        db.commit()
        db.refresh(db_appointment)

        # Обновляем напоминания если изменились настройки
        if 'reminder_enabled' in update_data or 'reminder_time' in update_data:
            update_appointment_reminders(db, appointment_id)

    return db_appointment


def delete_appointment(db: Session, appointment_id: int):
    """Удаляет назначение"""
    db_appointment = get_appointment(db, appointment_id)
    if db_appointment:
        # Удаляем связанные напоминания и записи о выполнении
        db.query(models.AppointmentReminder).filter(
            models.AppointmentReminder.appointment_id == appointment_id
        ).delete()

        db.query(models.AppointmentCompletion).filter(
            models.AppointmentCompletion.appointment_id == appointment_id
        ).delete()

        db.delete(db_appointment)
        db.commit()
    return db_appointment


# Appointment Completion CRUD
def create_completion(db: Session, completion: schemas.CompletionCreate, patient_id: int):
    """Создает запись о выполнении назначения"""
    db_completion = models.AppointmentCompletion(
        patient_id=patient_id,
        **completion.model_dump()
    )

    # Обновляем статистику назначения
    appointment = get_appointment(db, completion.appointment_id)
    if appointment:
        appointment.completed_doses += 1

        if appointment.total_doses:
            appointment.completion_rate = (appointment.completed_doses / appointment.total_doses) * 100

        appointment.last_taken_date = completion.completion_date

        # Рассчитываем следующую дату
        if appointment.frequency:
            appointment.next_due_date = calculate_next_due_date(
                appointment.frequency,
                completion.completion_date
            )

    db.add(db_completion)
    db.commit()
    db.refresh(db_completion)

    return db_completion


def get_appointment_completions(
        db: Session,
        appointment_id: int,
        skip: int = 0,
        limit: int = 100
):
    """Получает историю выполнения назначения"""
    return db.query(models.AppointmentCompletion).filter(
        models.AppointmentCompletion.appointment_id == appointment_id
    ).order_by(
        models.AppointmentCompletion.completion_date.desc(),
        models.AppointmentCompletion.completion_time.desc()
    ).offset(skip).limit(limit).all()


def get_patient_completions(
        db: Session,
        patient_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
):
    """Получает все выполнения пациентом"""
    query = db.query(models.AppointmentCompletion).filter(
        models.AppointmentCompletion.patient_id == patient_id
    )

    if start_date:
        query = query.filter(models.AppointmentCompletion.completion_date >= start_date)
    if end_date:
        query = query.filter(models.AppointmentCompletion.completion_date <= end_date)

    return query.order_by(
        models.AppointmentCompletion.completion_date.desc(),
        models.AppointmentCompletion.completion_time.desc()
    ).offset(skip).limit(limit).all()


# Reminder CRUD
def create_appointment_reminders(db: Session, appointment_id: int):
    """Создает напоминания для назначения"""
    appointment = get_appointment(db, appointment_id)
    if not appointment or not appointment.reminder_enabled:
        return []

    reminders = []

    # Создаем напоминание на каждую дату выполнения
    current_date = appointment.start_date
    if appointment.end_date:
        end_date = appointment.end_date
    else:
        # Если нет даты окончания, создаем на 30 дней вперед
        end_date = current_date + timedelta(days=30)

    while current_date <= end_date:
        reminder = models.AppointmentReminder(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            reminder_date=current_date,
            reminder_time=appointment.reminder_time or "09:00",
            reminder_type="in_app",
            message=f"Напоминание: {appointment.title}",
            status="scheduled"
        )

        db.add(reminder)
        reminders.append(reminder)

        # Переходим к следующей дате в зависимости от частоты
        current_date = calculate_next_due_date(appointment.frequency, current_date)
        if not current_date:  # Если частота не указана, только один раз
            break

    db.commit()
    return reminders


def update_appointment_reminders(db: Session, appointment_id: int):
    """Обновляет напоминания для назначения"""
    # Удаляем старые напоминания
    db.query(models.AppointmentReminder).filter(
        models.AppointmentReminder.appointment_id == appointment_id
    ).delete()

    # Создаем новые
    return create_appointment_reminders(db, appointment_id)


def get_todays_reminders(db: Session, patient_id: int):
    """Получает сегодняшние напоминания пациента"""
    today = date.today()

    return db.query(models.AppointmentReminder).filter(
        models.AppointmentReminder.patient_id == patient_id,
        models.AppointmentReminder.reminder_date == today,
        models.AppointmentReminder.status.in_(["scheduled", "sent"])
    ).order_by(models.AppointmentReminder.reminder_time).all()


def mark_reminder_sent(db: Session, reminder_id: int):
    """Отмечает напоминание как отправленное"""
    reminder = db.query(models.AppointmentReminder).filter(
        models.AppointmentReminder.id == reminder_id
    ).first()

    if reminder:
        reminder.status = "sent"
        reminder.sent_at = datetime.now()
        db.commit()

    return reminder


# Вспомогательные функции
def calculate_next_due_date(frequency: Optional[str], current_date: date) -> Optional[date]:
    """Рассчитывает следующую дату выполнения на основе частоты"""
    if not frequency:
        return None

    frequency_lower = frequency.lower()

    if "ежедневно" in frequency_lower or "daily" in frequency_lower:
        return current_date + timedelta(days=1)
    elif "раз в неделю" in frequency_lower or "weekly" in frequency_lower:
        return current_date + timedelta(days=7)
    elif "2 раза в неделю" in frequency_lower:
        return current_date + timedelta(days=3)  # Примерно через 3 дня
    elif "3 раза в неделю" in frequency_lower:
        return current_date + timedelta(days=2)  # Примерно через 2 дня
    elif "раз в месяц" in frequency_lower or "monthly" in frequency_lower:
        # Простое приближение - добавляем 30 дней
        return current_date + timedelta(days=30)
    elif "раз в день" in frequency_lower:
        return current_date + timedelta(days=1)

    return None


def get_appointment_stats(db: Session, patient_id: int):
    """Получает статистику по назначениям пациента"""
    total = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id
    ).count()

    active = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active"
    ).count()

    completed = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "completed"
    ).count()

    # Рассчитываем процент выполнения активных назначений
    active_appointments = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active"
    ).all()

    total_completion_rate = 0
    if active_appointments:
        for app in active_appointments:
            total_completion_rate += app.completion_rate
        avg_completion_rate = total_completion_rate / len(active_appointments)
    else:
        avg_completion_rate = 0

    # Сегодняшние назначения
    today = date.today()
    today_appointments = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active",
        models.MedicalAppointment.next_due_date == today
    ).count()

    # Просроченные назначения
    overdue_appointments = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active",
        models.MedicalAppointment.next_due_date < today
    ).count()

    # Ближайшие назначения (следующие 7 дней)
    upcoming_end_date = today + timedelta(days=7)
    upcoming_appointments = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active",
        models.MedicalAppointment.next_due_date >= today,
        models.MedicalAppointment.next_due_date <= upcoming_end_date
    ).order_by(models.MedicalAppointment.next_due_date).limit(10).all()

    return {
        "total_appointments": total,
        "active_appointments": active,
        "completed_appointments": completed,
        "completion_rate": round(avg_completion_rate, 2),
        "overdue_appointments": overdue_appointments,
        "today_appointments": today_appointments,
        "upcoming_appointments": upcoming_appointments
    }


def get_daily_schedule(db: Session, patient_id: int, target_date: date):
    """Получает расписание на день"""
    # Назначения на день
    appointments = db.query(models.MedicalAppointment).filter(
        models.MedicalAppointment.patient_id == patient_id,
        models.MedicalAppointment.status == "active",
        models.MedicalAppointment.next_due_date == target_date
    ).all()

    # Выполнения за день
    completions = db.query(models.AppointmentCompletion).filter(
        models.AppointmentCompletion.patient_id == patient_id,
        models.AppointmentCompletion.completion_date == target_date
    ).all()

    # Напоминания на день
    reminders = db.query(models.AppointmentReminder).filter(
        models.AppointmentReminder.patient_id == patient_id,
        models.AppointmentReminder.reminder_date == target_date
    ).all()

    return {
        "date": target_date,
        "appointments": appointments,
        "completions": completions,
        "reminders": reminders
    }


def get_medication_adherence(db: Session, patient_id: int, appointment_id: Optional[int] = None):
    """Рассчитывает приверженность к лечению"""
    if appointment_id:
        # Для конкретного назначения
        appointment = get_appointment(db, appointment_id)
        if not appointment or appointment.patient_id != patient_id:
            return None

        completions = get_appointment_completions(db, appointment_id)

        # Находим пропущенные даты
        expected_dates = []
        current_date = appointment.start_date
        end_date = appointment.end_date or date.today()

        while current_date <= end_date:
            expected_dates.append(current_date)
            next_date = calculate_next_due_date(appointment.frequency, current_date)
            if not next_date:
                break
            current_date = next_date

        completed_dates = {c.completion_date for c in completions}
        missed_dates = [d for d in expected_dates if d not in completed_dates and d <= date.today()]

        # Рассчитываем серию
        streak_days = 0
        current_streak = 0
        check_date = date.today()

        while check_date >= appointment.start_date:
            if check_date in completed_dates:
                current_streak += 1
                streak_days = max(streak_days, current_streak)
            else:
                current_streak = 0
            check_date -= timedelta(days=1)

        return {
            "appointment_id": appointment.id,
            "appointment_title": appointment.title,
            "total_doses": appointment.total_doses or len(expected_dates),
            "completed_doses": appointment.completed_doses,
            "adherence_rate": appointment.completion_rate,
            "missed_dates": missed_dates,
            "streak_days": streak_days,
            "last_completion": appointment.last_taken_date
        }
    else:
        # Для всех назначений пациента
        appointments = get_patient_appointments(db, patient_id, status="active")

        adherence_data = []
        for appointment in appointments:
            if appointment.appointment_type == "medication":
                adherence = get_medication_adherence(db, patient_id, appointment.id)
                if adherence:
                    adherence_data.append(adherence)

        return adherence_data


# Consultation functions (заглушки - нужно реализовать)
def create_consultation(db: Session, consultation_data: schemas.ConsultationCreate):
    """Создать запись на консультацию"""
    # TODO: Реализовать
    pass


def get_doctor_schedule(db: Session, doctor_id: int, date: date):
    """Получить расписание врача на день"""
    # TODO: Реализовать
    pass


def get_available_slots(db: Session, doctor_id: int, date: date):
    """Получить свободные слоты для записи"""
    # TODO: Реализовать
    pass


def get_patient_consultation_history(db: Session, patient_id: int):
    """История консультаций пациента"""
    # TODO: Реализовать
    pass


def get_upcoming_consultations(db: Session, patient_id: int):
    """Предстоящие консультации пациента"""
    # TODO: Реализовать
    pass


def cancel_consultation(db: Session, consultation_id: int, reason: str):
    """Отменить консультацию"""
    # TODO: Реализовать
    pass


def complete_consultation(db: Session, consultation_id: int, medical_notes: str):
    """Завершить консультацию с медицинскими записями"""
    # TODO: Реализовать
    pass


def create_consultation(db: Session, consultation: schemas.ConsultationCreate):
    """Создать запись на консультацию"""
    db_consultation = models.Consultation(**consultation.model_dump())
    db.add(db_consultation)

    # Бронируем слот
    if consultation.slot_id:
        slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.id == consultation.slot_id
        ).first()
        if slot:
            slot.status = "booked"
            slot.consultation_id = db_consultation.id

    db.commit()
    db.refresh(db_consultation)
    return db_consultation


def get_consultation(db: Session, consultation_id: int):
    """Получить консультацию по ID"""
    return db.query(models.Consultation).filter(
        models.Consultation.id == consultation_id
    ).first()


def get_patient_consultations(db: Session, patient_id: int, status: Optional[str] = None):
    """Получить все консультации пациента"""
    query = db.query(models.Consultation).filter(
        models.Consultation.patient_id == patient_id
    )

    if status:
        query = query.filter(models.Consultation.status == status)

    return query.order_by(
        models.Consultation.scheduled_date.desc(),
        models.Consultation.scheduled_time.desc()
    ).all()


def get_doctor_consultations(db: Session, doctor_id: int, date: Optional[date] = None):
    """Получить консультации врача"""
    query = db.query(models.Consultation).filter(
        models.Consultation.doctor_id == doctor_id
    )

    if date:
        query = query.filter(models.Consultation.scheduled_date == date)

    return query.order_by(
        models.Consultation.scheduled_time
    ).all()


def update_consultation_status(db: Session, consultation_id: int, status: str):
    """Обновить статус консультации"""
    db_consultation = get_consultation(db, consultation_id)
    if db_consultation:
        db_consultation.status = status
        db.commit()
        db.refresh(db_consultation)
    return db_consultation


def cancel_consultation(db: Session, consultation_id: int, reason: str):
    """Отменить консультацию"""
    consultation = get_consultation(db, consultation_id)
    if consultation:
        consultation.status = "cancelled"
        consultation.notes = f"{consultation.notes or ''}\nОтменено: {reason}"

        # Освобождаем слот
        slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.consultation_id == consultation_id
        ).first()
        if slot:
            slot.status = "available"
            slot.consultation_id = None

        db.commit()
    return consultation


# Doctor Schedule CRUD
def create_doctor_schedule(db: Session, schedule: schemas.DoctorScheduleCreate):
    """Создать рабочий график врача"""
    db_schedule = models.DoctorSchedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


def generate_appointment_slots(db: Session, doctor_id: int, start_date: date, end_date: date):
    """Сгенерировать слоты для записи на основе расписания врача"""
    from datetime import timedelta

    slots = []
    current_date = start_date

    while current_date <= end_date:
        # Получаем расписание на день недели
        day_of_week = current_date.weekday()  # 0-понедельник, 6-воскресенье

        schedules = db.query(models.DoctorSchedule).filter(
            models.DoctorSchedule.doctor_id == doctor_id,
            models.DoctorSchedule.day_of_week == day_of_week,
            models.DoctorSchedule.is_active == True
        ).all()

        for schedule in schedules:
            # Проверяем исключения
            if schedule.exception_date == current_date:
                continue

            # Генерируем слоты
            start_datetime = datetime.combine(current_date, schedule.start_time)
            end_datetime = datetime.combine(current_date, schedule.end_time)
            slot_duration = timedelta(minutes=schedule.slot_duration or 30)

            current_slot = start_datetime
            while current_slot + slot_duration <= end_datetime:
                slot = models.AppointmentSlot(
                    doctor_id=doctor_id,
                    schedule_id=schedule.id,
                    slot_date=current_date,
                    start_time=current_slot.time(),
                    end_time=(current_slot + slot_duration).time(),
                    status="available"
                )
                db.add(slot)
                slots.append(slot)

                current_slot += slot_duration

        current_date += timedelta(days=1)

    db.commit()
    return slots


def get_available_slots(db: Session, doctor_id: int, target_date: date):
    """Получить свободные слоты врача на дату"""
    return db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.doctor_id == doctor_id,
        models.AppointmentSlot.slot_date == target_date,
        models.AppointmentSlot.status == "available"
    ).order_by(models.AppointmentSlot.start_time).all()


def block_slot(db: Session, slot_id: int, reason: str):
    """Заблокировать слот (например, для перерыва)"""
    slot = db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.id == slot_id
    ).first()

    if slot and slot.status == "available":
        slot.status = "blocked"
        slot.notes = reason
        db.commit()

    return slot


def get_doctor_schedule_for_day(db: Session, doctor_id: int, target_date: date):
    """Получить расписание врача на день"""
    day_of_week = target_date.weekday()

    return db.query(models.DoctorSchedule).filter(
        models.DoctorSchedule.doctor_id == doctor_id,
        models.DoctorSchedule.day_of_week == day_of_week,
        models.DoctorSchedule.is_active == True
    ).all()


def get_doctor_weekly_schedule(db: Session, doctor_id: int):
    """Получить недельное расписание врача"""
    return db.query(models.DoctorSchedule).filter(
        models.DoctorSchedule.doctor_id == doctor_id,
        models.DoctorSchedule.is_active == True
    ).order_by(models.DoctorSchedule.day_of_week).all()
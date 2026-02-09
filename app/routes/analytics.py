# app/routes/analytics.py
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
from sqlalchemy import func, and_, or_

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/patient/{patient_id}/health-timeline")
def get_patient_health_timeline(
        patient_id: int,
        start_date: date = Query(..., description="Дата начала"),
        end_date: date = Query(..., description="Дата окончания"),
        metric: str = Query("all", description="Метрика для анализа"),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Динамика состояния пациента за период"""

    # Получаем данные самоконтроля за период
    monitoring_data = crud.get_patient_self_monitoring(
        db, patient_id, start_date=start_date, end_date=end_date
    )

    # Анализируем динамику
    analysis = {
        "period": f"{start_date} - {end_date}",
        "patient_id": patient_id,
        "total_measurements": len(monitoring_data),
        "trend_analysis": {},
        "recommendations": []
    }

    # Анализ динамики давления
    bp_systolic = [m.blood_pressure_systolic for m in monitoring_data if m.blood_pressure_systolic]
    if bp_systolic:
        analysis["trend_analysis"]["blood_pressure"] = {
            "average": sum(bp_systolic) / len(bp_systolic),
            "min": min(bp_systolic),
            "max": max(bp_systolic),
            "trend": "улучшение" if bp_systolic[-1] < bp_systolic[0] else "ухудшение"
        }

    # Аналогично для других показателей

    return analysis


@router.get("/doctor/{doctor_id}/patient-progress")
def get_doctor_patients_progress(
        doctor_id: int,
        timeframe_days: int = Query(30, ge=1, le=365),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Прогресс всех пациентов врача"""

    # Находим всех пациентов врача
    patients = db.query(Patient).join(
        crud.models.MedicalAppointment
    ).filter(
        crud.models.MedicalAppointment.doctor_id == doctor_id
    ).distinct().all()

    progress_report = {
        "doctor_id": doctor_id,
        "timeframe_days": timeframe_days,
        "total_patients": len(patients),
        "patient_progress": []
    }

    for patient in patients:
        # Получаем статистику за период
        end_date = date.today()
        start_date = end_date - timedelta(days=timeframe_days)

        monitoring_stats = crud.get_monitoring_stats(db, patient.id, timeframe_days)
        appointment_stats = crud.get_appointment_stats(db, patient.id)

        progress_report["patient_progress"].append({
            "patient_id": patient.id,
            "patient_name": f"{patient.last_name} {patient.first_name}",
            "monitoring_stats": monitoring_stats,
            "appointment_stats": appointment_stats,
            "overall_status": "стабильный"  # Можно рассчитать на основе данных
        })

    return progress_report


@router.get("/treatment-effectiveness")
def get_treatment_effectiveness_report(
        patient_id: Optional[int] = Query(None),
        diagnosis: Optional[str] = Query(None),
        start_date: date = Query(None),
        end_date: date = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Отчет об эффективности лечения"""

    report = {
        "metrics": {},
        "effectiveness_score": 0,
        "recommendations": []
    }

    # Анализ приверженности к лечению
    if patient_id:
        adherence_data = crud.get_medication_adherence(db, patient_id)
        report["metrics"]["adherence"] = {
            "average_rate": sum(a["adherence_rate"] for a in adherence_data) / len(
                adherence_data) if adherence_data else 0,
            "total_appointments": len(adherence_data)
        }

    # Анализ динамики симптомов
    # ... дополнительная логика анализа

    return report


@router.get("/symptom-trends")
def get_symptom_trends_analysis(
        patient_id: int,
        symptom: Optional[str] = Query(None),
        months: int = Query(6, ge=1, le=24),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Анализ тенденций симптомов"""

    # Получаем жалобы пациента за период
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    complaints = db.query(crud.models.PatientComplaint).filter(
        crud.models.PatientComplaint.patient_id == patient_id,
        crud.models.PatientComplaint.complaint_date >= start_date,
        crud.models.PatientComplaint.complaint_date <= end_date
    ).all()

    # Анализируем частоту и тяжесть симптомов
    symptom_frequency = {}
    for complaint in complaints:
        symptom = complaint.symptom_name
        if symptom not in symptom_frequency:
            symptom_frequency[symptom] = {
                "count": 0,
                "severities": [],
                "dates": []
            }
        symptom_frequency[symptom]["count"] += 1
        symptom_frequency[symptom]["severities"].append(complaint.severity)
        symptom_frequency[symptom]["dates"].append(complaint.complaint_date)

    # Формируем отчет
    trend_report = {
        "patient_id": patient_id,
        "analysis_period_months": months,
        "total_complaints": len(complaints),
        "symptom_analysis": symptom_frequency,
        "trend_insights": []
    }

    # Генерируем инсайты
    for symptom, data in symptom_frequency.items():
        if data["count"] > 3:  # Частый симптом
            insight = f"Симптом '{symptom}' проявляется часто ({data['count']} раз за период)"
            trend_report["trend_insights"].append(insight)

    return trend_report


@router.get("/generate-report/{report_type}")
def generate_comprehensive_report(
        report_type: str,
        patient_id: Optional[int] = Query(None),
        doctor_id: Optional[int] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Генерация комплексных отчетов"""

    report_types = {
        "health_summary": "Сводка о здоровье",
        "treatment_progress": "Прогресс лечения",
        "medication_adherence": "Приверженность к лечению",
        "symptom_analysis": "Анализ симптомов",
        "comprehensive": "Комплексный отчет"
    }

    if report_type not in report_types:
        raise HTTPException(status_code=400, detail="Invalid report type")

    report = {
        "report_type": report_type,
        "report_name": report_types[report_type],
        "generated_at": date.today().isoformat(),
        "data": {}
    }

    if report_type == "health_summary" and patient_id:
        # Сводка о здоровье
        report["data"]["monitoring_stats"] = crud.get_monitoring_stats(db, patient_id, 30)
        report["data"]["appointment_stats"] = crud.get_appointment_stats(db, patient_id)
        report["data"]["patient_summary"] = crud.get_patient_summary(db, patient_id)

    elif report_type == "treatment_progress" and patient_id:
        # Прогресс лечения
        report["data"]["adherence"] = crud.get_medication_adherence(db, patient_id)
        report["data"]["timeline"] = crud.get_patient_timeline(db, patient_id, 6)

    elif report_type == "comprehensive" and patient_id:
        # Комплексный отчет
        report["data"]["health_data"] = crud.get_patient_medical_record(db, patient_id)
        report["data"]["monitoring_analysis"] = crud.get_monitoring_stats(db, patient_id, 90)
        report["data"]["treatment_analysis"] = {
            "adherence": crud.get_medication_adherence(db, patient_id),
            "appointments": crud.get_appointment_stats(db, patient_id)
        }

    return report


@router.get("/export-report/{report_type}")
def export_report_to_format(
        report_type: str,
        format: str = Query("json", pattern="^(json|pdf|csv)$"),
        patient_id: Optional[int] = Query(None),
        db: Session = Depends(get_db),
        current_user=Depends(auth.doctor_admin_only)
):
    """Экспорт отчета в различных форматах"""

    # Генерируем отчет
    report = generate_comprehensive_report(
        report_type, patient_id, None, None, None, db, current_user
    )

    if format == "json":
        return report
    elif format == "csv":
        # Конвертация в CSV (упрощенная)
        csv_data = "Report Type,Generated At,Data\n"
        csv_data += f"{report['report_type']},{report['generated_at']},See JSON for details\n"
        return {"csv": csv_data}
    elif format == "pdf":
        # Заглушка для PDF
        return {"message": "PDF export will be implemented", "report_id": "12345"}
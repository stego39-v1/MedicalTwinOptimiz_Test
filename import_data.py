import pandas as pd
from datetime import datetime
from database import SessionLocal, engine, Base
from models import (
    User, Patient, Doctor, Diagnosis,
    Prescription, Complaint, Symptom, SymptomCategory,
    Specialization, Department
)
from utils import get_password_hash, safe_str, parse_date
import os


# ✅ ФУНКЦИЯ ПАРСИНГА ДАТЫ-ВРЕМЕНИ - В ГЛОБАЛЬНОЙ ОБЛАСТИ ВИДИМОСТИ!
def parse_datetime(dt_str):
    """Парсинг строки с датой и временем в datetime объект"""
    if not dt_str or pd.isna(dt_str):
        return None
    dt_str = str(dt_str).strip()
    try:
        return datetime.fromisoformat(dt_str)
    except:
        # Пробуем другие форматы
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%d.%m.%Y %H:%M:%S'):
            try:
                return datetime.strptime(dt_str, fmt)
            except:
                continue
    return None


def get_or_create(session, model, defaults=None, **kwargs):
    """Найти или создать запись в БД"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    session.flush()
    return instance


def import_symptom_categories(session):
    df = pd.read_csv('data/symptom_categories.csv', sep=',', encoding='cp1251')
    count = 0
    for _, row in df.iterrows():
        name = safe_str(row.get('Name'))
        if name:
            get_or_create(session, SymptomCategory, name=name)
            count += 1
    print(f"   ✅ Категорий симптомов: {count}")


def import_symptoms(session):
    df = pd.read_csv('data/symptoms.csv', sep=',', encoding='cp1251')
    count = 0
    for _, row in df.iterrows():
        category_name = safe_str(row.get('CategoryName'))
        symptom_name = safe_str(row.get('Name'))
        if not category_name or not symptom_name:
            continue
        category = session.query(SymptomCategory).filter_by(name=category_name).first()
        if category:
            get_or_create(session, Symptom,
                          name=symptom_name,
                          category_id=category.id,
                          defaults={'description': safe_str(row.get('Description'))})
            count += 1
    print(f"   ✅ Симптомов: {count}")


def import_diagnoses(session):
    try:
        df = pd.read_csv('data/diagnoses.csv', sep=';', encoding='cp1251')
        count = 0
        for _, row in df.iterrows():
            code = safe_str(row.get('Код МКБ-10'))
            name = safe_str(row.get('Название диагноза'))
            category = safe_str(row.get('Категория'))
            if code and name:
                get_or_create(session, Diagnosis,
                              mkb10_code=code,
                              defaults={'name': name, 'category': category})
                count += 1
        print(f"   ✅ Диагнозов: {count}")
    except FileNotFoundError:
        print("   ⚠️ Файл diagnoses.csv не найден, пропускаем")


def import_specializations_departments(session):
    try:
        df = pd.read_csv('data/doctors.csv', sep=',', encoding='cp1251', header=None, skiprows=1)
        df.columns = ['surname', 'name', 'patronim', 'specialization', 'department', 'email', 'phone']

        spec_count = 0
        for spec in df['specialization'].dropna().unique():
            spec_name = safe_str(spec)
            if spec_name:
                get_or_create(session, Specialization, name=spec_name)
                spec_count += 1

        dept_count = 0
        for dept in df['department'].dropna().unique():
            dept_name = safe_str(dept)
            if dept_name:
                get_or_create(session, Department, name=dept_name)
                dept_count += 1
        print(f"   ✅ Специализаций: {spec_count}, Отделений: {dept_count}")
    except FileNotFoundError:
        print("   ⚠️ Файл doctors.csv не найден, пропускаем")


def import_doctors(session):
    try:
        df = pd.read_csv('data/doctors.csv', sep=',', encoding='cp1251', header=None, skiprows=1)
        df.columns = ['surname', 'name', 'patronim', 'specialization', 'department', 'email', 'phone']
    except FileNotFoundError:
        print("   ❌ Файл doctors.csv не найден!")
        return

    count = 0
    for _, row in df.iterrows():
        email = safe_str(row['email'])
        if not email:
            continue

        spec_name = safe_str(row['specialization'])
        spec = None
        if spec_name:
            spec = get_or_create(session, Specialization, name=spec_name)

        dept_name = safe_str(row['department'])
        dept = None
        if dept_name:
            dept = get_or_create(session, Department, name=dept_name)

        doctor = get_or_create(session, Doctor,
                               email=email,
                               defaults={
                                   'surname': safe_str(row['surname']),
                                   'name': safe_str(row['name']),
                                   'patronim': safe_str(row['patronim']),
                                   'specialization_id': spec.id if spec else None,
                                   'department_id': dept.id if dept else None,
                                   'phone': safe_str(row['phone'])
                               })
        session.flush()

        user = get_or_create(session, User,
                             email=email,
                             defaults={
                                 'password_hash': get_password_hash('default123')[:60],
                                 'role': 'doctor',
                                 'is_active': True,
                                 'doctor_id': doctor.id
                             })
        count += 1
    print(f"   ✅ Врачей: {count}")


def import_patients(session):
    try:
        df = pd.read_csv('data/patient.csv', sep=',', encoding='cp1251', header=None, skiprows=1)
        df.columns = ['surname', 'name', 'patronim', 'gender', 'city', 'street', 'building',
                      'email', 'birth_date', 'phone']
    except FileNotFoundError:
        print("   ❌ Файл patient.csv не найден!")
        return

    seen_emails = set()
    count = 0
    for _, row in df.iterrows():
        email = safe_str(row['email'])
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)

        gender_val = safe_str(row['gender'])
        gender = 'м' if gender_val and gender_val.lower() in ['м', 'male', 'мужской'] else 'ж'

        birth_date = parse_date(row['birth_date'])
        if not birth_date:
            print(f"   ⚠️ Пропущен пациент {email}: неверная дата")
            continue

        patient = get_or_create(session, Patient,
                                email=email,
                                defaults={
                                    'surname': safe_str(row['surname']),
                                    'name': safe_str(row['name']),
                                    'patronim': safe_str(row['patronim']),
                                    'gender': gender,
                                    'birth_date': birth_date,
                                    'city': safe_str(row['city']),
                                    'street': safe_str(row['street']),
                                    'building': safe_str(row['building']),
                                    'phone': safe_str(row['phone'])
                                })
        session.flush()

        user = get_or_create(session, User,
                             email=email,
                             defaults={
                                 'password_hash': get_password_hash('default123')[:60],
                                 'role': 'patient',
                                 'is_active': True,
                                 'patient_id': patient.id
                             })
        count += 1
    print(f"   ✅ Пациентов: {count}")


def import_prescriptions(session):
    try:
        df = pd.read_csv('data/prescriptions.csv', sep=',', encoding='cp1251')
        if 'Patient_FIO' not in df.columns:
            print("   ⚠️ Пропускаем назначения: неверный формат файла")
            return
    except FileNotFoundError:
        print("   ⚠️ Файл prescriptions.csv не найден, пропускаем")
        return

    patients = {f"{p.surname} {p.name} {p.patronim or ''}".strip().lower(): p
                for p in session.query(Patient).all()}
    doctors = {f"{d.surname} {d.name} {d.patronim or ''}".strip().lower(): d
               for d in session.query(Doctor).all()}

    count = 0
    for _, row in df.iterrows():
        patient_fio = safe_str(row.get('Patient_FIO'))
        doctor_fio = safe_str(row.get('Doctor_FIO'))

        if not patient_fio or not doctor_fio:
            continue

        patient_key = patient_fio.lower()
        doctor_key = doctor_fio.lower()

        patient = patients.get(patient_key)
        doctor = doctors.get(doctor_key)

        if patient and doctor:
            status = 'активно' if str(row.get('Status', 'активно')).strip().lower() in ['активно', 'active', '1'] else 'завершено'

            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=doctor.id,
                medication_name=safe_str(row.get('Medication_Name')),
                quantity=float(row['Quantity']) if pd.notna(row.get('Quantity')) else 0.0,
                dose_unit=safe_str(row.get('Dose_Unit')) or 'мг',
                frequency=safe_str(row.get('Frequency')) or '1 раз в день',
                duration_days=int(row['DurationInDays']) if pd.notna(row.get('DurationInDays')) else 0,
                start_date=parse_datetime(row.get('StartDate')) or datetime.utcnow(),
                end_date=parse_datetime(row.get('EndDate')) if pd.notna(row.get('EndDate')) else None,
                instructions=safe_str(row.get('Instructions')),
                status=status
            )
            session.add(prescription)
            count += 1
    print(f"   ✅ Назначений: {count}")


def import_complaints(session):
    try:
        df = pd.read_csv('data/patient_complaints.csv', sep=',', encoding='cp1251')
        if 'Patient_FIO' not in df.columns:
            print("   ⚠️ Пропускаем жалобы: неверный формат файла")
            return
    except FileNotFoundError:
        print("   ⚠️ Файл patient_complaints.csv не найден, пропускаем")
        return

    patients = {f"{p.surname} {p.name} {p.patronim or ''}".strip().lower(): p
                for p in session.query(Patient).all()}
    symptoms = {s.name.strip().lower(): s for s in session.query(Symptom).all()}

    count = 0
    for _, row in df.iterrows():
        patient_fio = safe_str(row.get('Patient_FIO'))
        symptom_name = safe_str(row.get('Symptom_Name'))

        if not patient_fio or not symptom_name:
            continue

        patient = patients.get(patient_fio.lower())
        symptom = symptoms.get(symptom_name.lower())

        if patient and symptom:
            complaint = Complaint(
                patient_id=patient.id,
                symptom_id=symptom.id,
                complaint_date=parse_datetime(row.get('ComplaintDate')) or datetime.utcnow(),
                severity=safe_str(row.get('Severity')) or 'Умеренная',
                description=safe_str(row.get('Description'))
            )
            session.add(complaint)
            count += 1
    print(f"   ✅ Жалоб: {count}")


def reset_and_import():
    """Главная функция импорта"""
    print("=" * 60)
    print("🚀 ИМПОРТ ДАННЫХ В БАЗУ (FastAPI + SQLAlchemy)")
    print("=" * 60)

    print("\n1. Создание таблиц...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("   ✅ Таблицы созданы")

    session = SessionLocal()

    try:
        print("\n2. Импорт справочников...")
        import_symptom_categories(session)
        import_symptoms(session)
        import_diagnoses(session)
        import_specializations_departments(session)
        session.commit()
        print("   ✅ Справочники загружены")

        print("\n3. Импорт врачей...")
        import_doctors(session)
        session.commit()

        print("\n4. Импорт пациентов...")
        import_patients(session)
        session.commit()

        print("\n5. Импорт назначений...")
        import_prescriptions(session)
        session.commit()

        print("\n6. Импорт жалоб...")
        import_complaints(session)
        session.commit()

        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ИМПОРТА")
        print("=" * 60)
        print(f"   Пациентов: {session.query(Patient).count()}")
        print(f"   Врачей: {session.query(Doctor).count()}")
        print(f"   Пользователей: {session.query(User).count()}")
        print(f"   Назначений: {session.query(Prescription).count()}")
        print(f"   Жалоб: {session.query(Complaint).count()}")
        print(f"   Симптомов: {session.query(Symptom).count()}")
        print(f"   Диагнозов: {session.query(Diagnosis).count()}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

    print("\n✅ ИМПОРТ ЗАВЕРШЕН")
    print("=" * 60)


if __name__ == "__main__":
    if not os.path.exists('data'):
        os.makedirs('data')
        print("📁 Создана папка 'data'. Положите в нее CSV файлы.")
    else:
        reset_and_import()
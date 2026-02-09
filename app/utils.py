# app/utils.py
import csv
from datetime import datetime
from sqlalchemy.orm import Session
import os
import sys


def import_csv_data(db: Session):
    """Импорт данных из CSV файлов"""
    try:
        # Импорт моделей
        from app.models import (
            Diagnosis, Doctor, Patient,
            PatientComplaint, Prescription, Symptom, User
        )

        print("✓ Models imported successfully for CSV import")

        csv_dir = os.path.join(os.path.dirname(__file__), "data")
        print(f"[DEBUG] CSV directory: {csv_dir}")

        # Проверяем существование директории
        if not os.path.exists(csv_dir):
            print(f"[WARNING] CSV directory does not exist: {csv_dir}")
            os.makedirs(csv_dir, exist_ok=True)
            print(f"[INFO] Created CSV directory: {csv_dir}")
            return

        # Импорт диагнозов
        diagnoses_csv = os.path.join(csv_dir, "diagnoses.csv")
        if os.path.exists(diagnoses_csv):
            print(f"[INFO] Importing diagnoses from {diagnoses_csv}")
            try:
                # Пробуем разные кодировки
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'latin-1']:
                    try:
                        with open(diagnoses_csv, 'r', encoding=encoding) as f:
                            reader = csv.DictReader(f)
                            count = 0
                            for row in reader:
                                diagnosis = Diagnosis(
                                    icd_code=row.get('icd_code', ''),
                                    name=row.get('name', ''),
                                    category=row.get('category', '')
                                )
                                db.add(diagnosis)
                                count += 1
                            db.commit()
                            print(f"✓ Imported {count} diagnoses using {encoding} encoding")
                            break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        print(f"✗ Error with {encoding} encoding: {e}")
                        db.rollback()
            except Exception as e:
                print(f"✗ Error importing diagnoses: {e}")
                db.rollback()

        # Импорт врачей
        doctors_csv = os.path.join(csv_dir, "doctors.csv")
        if os.path.exists(doctors_csv):
            print(f"[INFO] Importing doctors from {doctors_csv}")
            try:
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'latin-1']:
                    try:
                        with open(doctors_csv, 'r', encoding=encoding) as f:
                            reader = csv.DictReader(f)
                            count = 0
                            for row in reader:
                                doctor = Doctor(
                                    last_name=row.get('last_name', ''),
                                    first_name=row.get('first_name', ''),
                                    middle_name=row.get('middle_name', ''),
                                    specialty=row.get('specialty', ''),
                                    department=row.get('department', ''),
                                    email=row.get('email', ''),
                                    phone=row.get('phone', '')
                                )
                                db.add(doctor)
                                count += 1
                            db.commit()
                            print(f"✓ Imported {count} doctors using {encoding} encoding")
                            break
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                print(f"✗ Error importing doctors: {e}")
                db.rollback()

        # Импорт пациентов
        patients_csv = os.path.join(csv_dir, "patients.csv")
        if os.path.exists(patients_csv):
            print(f"[INFO] Importing patients from {patients_csv}")
            try:
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'latin-1']:
                    try:
                        with open(patients_csv, 'r', encoding=encoding) as f:
                            reader = csv.DictReader(f)
                            count = 0
                            for row in reader:
                                patient = Patient(
                                    last_name=row.get('last_name', ''),
                                    first_name=row.get('first_name', ''),
                                    middle_name=row.get('middle_name', ''),
                                    gender=row.get('gender', ''),
                                    city=row.get('city', ''),
                                    street=row.get('street', ''),
                                    building=row.get('building', ''),
                                    email=row.get('email', ''),
                                    birth_date=row.get('birth_date', ''),
                                    phone=row.get('phone', '')
                                )
                                db.add(patient)
                                count += 1
                            db.commit()
                            print(f"✓ Imported {count} patients using {encoding} encoding")
                            break
                    except UnicodeDecodeError:
                        continue
            except Exception as e:
                print(f"✗ Error importing patients: {e}")
                db.rollback()

        print("✓ CSV import completed")

    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error during CSV import: {e}")
        db.rollback()
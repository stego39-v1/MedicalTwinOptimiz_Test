# app/utils.py
import csv
from datetime import datetime
from sqlalchemy.orm import Session
import os
import sys


def import_csv_data(db: Session):
    """Импорт данных из CSV файлов"""
    try:
        # Импорт только существующих моделей
        from app.models import (
            Diagnosis, Doctor, Patient
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
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'latin-1']:
                    try:
                        with open(diagnoses_csv, 'r', encoding=encoding) as f:
                            # Проверяем формат файла
                            content = f.read(1024)
                            f.seek(0)

                            if ';' in content:
                                # Формат с разделителем ;
                                reader = csv.DictReader(f, delimiter=';')
                            else:
                                # Формат с разделителем ,
                                f.seek(0)
                                reader = csv.DictReader(f)

                            count = 0
                            for row in reader:
                                # Преобразуем ключи
                                if 'Код МКБ-10' in row:
                                    # Формат: Код МКБ-10;Название диагноза;Категория
                                    diagnosis = Diagnosis(
                                        icd_code=row.get('Код МКБ-10', '').strip(),
                                        name=row.get('Название диагноза', '').strip(),
                                        category=row.get('Категория', '').strip()
                                    )
                                else:
                                    # Другие форматы
                                    diagnosis = Diagnosis(
                                        icd_code=row.get('icd_code', row.get('icd', '')).strip(),
                                        name=row.get('name', row.get('diagnosis', '')).strip(),
                                        category=row.get('category', '').strip()
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
                            # Проверяем формат файла
                            content = f.read(1024)
                            f.seek(0)

                            if ';' in content:
                                reader = csv.DictReader(f, delimiter=';')
                            else:
                                f.seek(0)
                                reader = csv.DictReader(f)

                            count = 0
                            for row in reader:
                                # Поддерживаем разные форматы полей
                                doctor = Doctor(
                                    last_name=row.get('last_name', row.get('ФИО', row.get('Last Name', ''))).strip(),
                                    first_name=row.get('first_name', row.get('Имя', row.get('First Name', ''))).strip(),
                                    middle_name=row.get('middle_name',
                                                        row.get('Отчество', row.get('Middle Name', ''))).strip(),
                                    specialty=row.get('specialty',
                                                      row.get('Специальность', row.get('Specialty', ''))).strip(),
                                    department=row.get('department',
                                                       row.get('Отделение', row.get('Department', ''))).strip(),
                                    email=row.get('email', row.get('Email', row.get('Почта', ''))).strip(),
                                    phone=row.get('phone', row.get('НомерТелефона', row.get('Phone', ''))).strip()
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

        # Импорт пациентов (если файл существует)
        patients_csv = os.path.join(csv_dir, "patients.csv")
        if os.path.exists(patients_csv):
            print(f"[INFO] Importing patients from {patients_csv}")
            try:
                for encoding in ['utf-8', 'utf-8-sig', 'cp1251', 'windows-1251', 'latin-1']:
                    try:
                        with open(patients_csv, 'r', encoding=encoding) as f:
                            content = f.read(1024)
                            f.seek(0)

                            if ';' in content:
                                reader = csv.DictReader(f, delimiter=';')
                            else:
                                f.seek(0)
                                reader = csv.DictReader(f)

                            count = 0
                            for row in reader:
                                patient = Patient(
                                    last_name=row.get('last_name',
                                                      row.get('Фамилия', row.get('Last Name', ''))).strip(),
                                    first_name=row.get('first_name', row.get('Имя', row.get('First Name', ''))).strip(),
                                    middle_name=row.get('middle_name',
                                                        row.get('Отчество', row.get('Middle Name', ''))).strip(),
                                    gender=row.get('gender', row.get('Пол', row.get('Gender', ''))).strip(),
                                    city=row.get('city', row.get('Город', row.get('City', ''))).strip(),
                                    street=row.get('street', row.get('Улица', row.get('Street', ''))).strip(),
                                    building=row.get('building', row.get('Строение', row.get('Building', ''))).strip(),
                                    email=row.get('email', row.get('Почта', row.get('Email', ''))).strip(),
                                    birth_date=row.get('birth_date',
                                                       row.get('Дата рождения', row.get('Birth Date', ''))).strip(),
                                    phone=row.get('phone', row.get('Номер Телефона', row.get('Phone', ''))).strip()
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
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"✗ Error during CSV import: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
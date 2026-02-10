# import_data.py - исправленная версия
import csv
from datetime import datetime
from database import SessionLocal, engine, Base
from models import Patient, Doctor, User
from utils import get_password_hash, safe_str, parse_date


def reset_and_import():
    """Сброс и импорт данных"""
    print("=" * 50)
    print("СБРОС И ИМПОРТ ДАННЫХ")
    print("=" * 50)

    # 1. Создаем таблицы
    print("\n1. Создание таблиц...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("   Таблицы созданы")

    db = SessionLocal()

    try:
        # 2. Импорт пациентов
        print("\n2. Импорт пациентов из data/patient.csv...")
        patient_count = 0

        try:
            # Пробуем разные кодировки
            with open('data/patient.csv', 'r', encoding='cp1251') as f:
                reader = csv.reader(f, delimiter=',')
                headers = next(reader)
                print(f"   Заголовки: {headers}")

                for row in reader:
                    if len(row) < 10:
                        print(f"   Пропуск строки (мало данных): {row}")
                        continue

                    try:
                        # Парсим данные
                        surname = safe_str(row[0])
                        name = safe_str(row[1])
                        patronim = safe_str(row[2])
                        gender_str = safe_str(row[3])
                        birth_date = parse_date(row[8])
                        email = safe_str(row[7])
                        phone = safe_str(row[9])

                        if not email:
                            print(f"   Пропуск пациента без email: {surname} {name}")
                            continue

                        patient = Patient(
                            surname=surname,
                            name=name,
                            patronim=patronim,
                            gender='м' if gender_str == 'м' else 'ж',
                            birth_date=birth_date,
                            email=email,
                            phone=phone
                        )
                        db.add(patient)
                        db.flush()

                        # Создаем пользователя
                        user = User(
                            email=email,
                            password_hash=get_password_hash('password123'),
                            role='patient',
                            is_active=True,
                            patient_id=patient.id
                        )
                        db.add(user)

                        patient_count += 1
                        if patient_count % 5 == 0:
                            print(f"   Импортировано {patient_count} пациентов...")

                    except Exception as e:
                        print(f"   Ошибка импорта пациента {row[0] if row else 'N/A'}: {e}")
                        continue

        except Exception as e:
            print(f"   Ошибка чтения файла пациентов: {e}")
            import traceback
            traceback.print_exc()

        print(f"   Всего импортировано пациентов: {patient_count}")

        # 3. Импорт врачей
        print("\n3. Импорт врачей из data/doctors.csv...")
        doctor_count = 0

        try:
            with open('data/doctors.csv', 'r', encoding='cp1251') as f:
                reader = csv.reader(f, delimiter=',')
                headers = next(reader)
                print(f"   Заголовки: {headers}")

                for row in reader:
                    if len(row) < 7:
                        print(f"   Пропуск строки (мало данных): {row}")
                        continue

                    try:
                        # Парсим данные
                        surname = safe_str(row[0])
                        name = safe_str(row[1])
                        patronim = safe_str(row[2])
                        specialization = safe_str(row[3])
                        department = safe_str(row[4])
                        email = safe_str(row[5])
                        phone = safe_str(row[6])

                        if not email:
                            print(f"   Пропуск врача без email: {surname} {name}")
                            continue

                        doctor = Doctor(
                            surname=surname,
                            name=name,
                            patronim=patronim,
                            specialization=specialization,
                            department=department,
                            email=email,
                            phone=phone
                        )
                        db.add(doctor)
                        db.flush()

                        # Создаем пользователя
                        user = User(
                            email=email,
                            password_hash=get_password_hash('password123'),
                            role='doctor',
                            is_active=True,
                            doctor_id=doctor.id
                        )
                        db.add(user)

                        doctor_count += 1
                        if doctor_count % 5 == 0:
                            print(f"   Импортировано {doctor_count} врачей...")

                    except Exception as e:
                        print(f"   Ошибка импорта врача {row[0] if row else 'N/A'}: {e}")
                        continue

        except Exception as e:
            print(f"   Ошибка чтения файла врачей: {e}")
            import traceback
            traceback.print_exc()

        print(f"   Всего импортировано врачей: {doctor_count}")

        # 4. Сохраняем изменения
        db.commit()
        print("\n✅ Все изменения сохранены в базе данных")

        # 5. Статистика (после коммита, чтобы избежать ошибок)
        print("\n" + "=" * 50)
        print("СТАТИСТИКА ИМПОРТА")
        print("=" * 50)

        # Создаем новую сессию для статистики
        db.close()
        db = SessionLocal()

        total_patients = db.query(Patient).count()
        total_doctors = db.query(Doctor).count()
        total_users = db.query(User).count()

        print(f"Пациентов в базе: {total_patients}")
        print(f"Врачей в базе: {total_doctors}")
        print(f"Пользователей в базе: {total_users}")

        # Показать примеры
        if total_patients > 0:
            print("\nПримеры импортированных пациентов:")
            for patient in db.query(Patient).limit(3).all():
                print(f"  - {patient.surname} {patient.name} ({patient.email})")

        if total_doctors > 0:
            print("\nПримеры импортированных врачей:")
            for doctor in db.query(Doctor).limit(3).all():
                print(f"  - {doctor.surname} {doctor.name} ({doctor.specialization})")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 50)
    print("ИМПОРТ ЗАВЕРШЕН")
    print("=" * 50)


if __name__ == '__main__':
    reset_and_import()
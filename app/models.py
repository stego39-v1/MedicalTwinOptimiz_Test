# app/models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="patient")  # Добавляем поле роли: patient, doctor, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    gender = Column(String)
    city = Column(String)
    street = Column(String)
    building = Column(String)
    email = Column(String)
    birth_date = Column(String)
    phone = Column(String)

    # Добавляем связь с пользователем (необязательно, но полезно)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="patient_profile")  # Добавьте эту строку

    complaints = relationship("PatientComplaint", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    specialty = Column(String)
    department = Column(String)
    email = Column(String)
    phone = Column(String)

    prescriptions = relationship("Prescription", back_populates="doctor")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    icd_code = Column(String, index=True)
    name = Column(String)
    category = Column(String)


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    category_name = Column(String)


class PatientComplaint(Base):
    __tablename__ = "patient_complaints"

    id = Column(Integer, primary_key=True, index=True)
    patient_last_name = Column(String)
    patient_first_name = Column(String)
    patient_middle_name = Column(String, nullable=True)
    symptom_name = Column(String)
    complaint_date = Column(Date)
    severity = Column(String)
    description = Column(Text)

    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="complaints")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_last_name = Column(String)
    patient_first_name = Column(String)
    patient_middle_name = Column(String, nullable=True)
    doctor_last_name = Column(String)
    doctor_first_name = Column(String)
    doctor_middle_name = Column(String, nullable=True)
    medication_name = Column(String)
    quantity = Column(Float)
    dose_unit = Column(String)
    frequency = Column(String)
    duration_in_days = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    instructions = Column(Text)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")


class SelfMonitoring(Base):
    """Модель для данных самоконтроля пациента"""
    __tablename__ = "self_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Основные показатели
    measurement_date = Column(Date, default=func.current_date())
    measurement_time = Column(Time, default=func.now())

    # Жизненные показатели
    blood_pressure_systolic = Column(Integer, nullable=True)  # Систолическое давление
    blood_pressure_diastolic = Column(Integer, nullable=True)  # Диастолическое давление
    heart_rate = Column(Integer, nullable=True)  # Пульс
    body_temperature = Column(Float, nullable=True)  # Температура тела
    blood_sugar = Column(Float, nullable=True)  # Уровень сахара в крови
    oxygen_saturation = Column(Integer, nullable=True)  # Сатурация кислорода
    weight = Column(Float, nullable=True)  # Вес
    height = Column(Float, nullable=True)  # Рост (заполняется один раз)

    # Симптомы и самочувствие
    pain_level = Column(Integer, nullable=True)  # Уровень боли 0-10
    fatigue_level = Column(Integer, nullable=True)  # Уровень усталости 0-10
    mood = Column(String, nullable=True)  # Настроение (good, normal, bad)
    sleep_hours = Column(Float, nullable=True)  # Часы сна
    appetite = Column(String, nullable=True)  # Аппетит (good, normal, bad)

    # Примечания и симптомы
    symptoms = Column(Text, nullable=True)  # Описание симптомов
    medications_taken = Column(Text, nullable=True)  # Принятые лекарства
    notes = Column(Text, nullable=True)  # Дополнительные заметки

    # Статус
    is_alert = Column(Boolean, default=False)  # Флаг тревожных показателей

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", backref="self_monitoring_records")

    # Метод для проверки тревожных показателей
    def check_alert_conditions(self):
        """Проверяет, являются ли показатели тревожными"""
        alerts = []

        if self.blood_pressure_systolic and (self.blood_pressure_systolic > 180 or self.blood_pressure_systolic < 90):
            alerts.append("Аномальное систолическое давление")

        if self.blood_pressure_diastolic and (
                self.blood_pressure_diastolic > 120 or self.blood_pressure_diastolic < 60):
            alerts.append("Аномальное диастолическое давление")

        if self.heart_rate and (self.heart_rate > 120 or self.heart_rate < 50):
            alerts.append("Аномальный пульс")

        if self.body_temperature and self.body_temperature > 38.0:
            alerts.append("Повышенная температура")

        if self.blood_sugar and (self.blood_sugar > 10.0 or self.blood_sugar < 3.9):
            alerts.append("Аномальный уровень сахара")

        if self.oxygen_saturation and self.oxygen_saturation < 92:
            alerts.append("Низкая сатурация кислорода")

        if self.pain_level and self.pain_level >= 7:
            alerts.append("Высокий уровень боли")

        return alerts


class MedicalAppointment(Base):
    """Модель для медицинских назначений"""
    __tablename__ = "medical_appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Информация о назначении
    appointment_type = Column(String)  # medication, procedure, test, consultation, exercise
    title = Column(String)
    description = Column(Text, nullable=True)

    # Детали назначения
    dosage = Column(String, nullable=True)  # Дозировка для лекарств
    frequency = Column(String, nullable=True)  # Частота приема/выполнения
    duration_days = Column(Integer, nullable=True)  # Продолжительность курса в днях
    instructions = Column(Text, nullable=True)  # Подробные инструкции

    # Даты и время
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    preferred_time = Column(String, nullable=True)  # Предпочтительное время выполнения

    # Статус и выполнение
    status = Column(String, default="active")  # active, completed, cancelled, paused
    priority = Column(String, default="medium")  # low, medium, high, critical

    # Напоминания
    reminder_enabled = Column(Boolean, default=True)
    reminder_time = Column(String, nullable=True)  # Время напоминания
    reminder_days_before = Column(Integer, default=0)  # За сколько дней напоминать

    # Отслеживание выполнения
    total_doses = Column(Integer, nullable=True)  # Общее количество приемов/процедур
    completed_doses = Column(Integer, default=0)  # Выполнено приемов/процедур
    completion_rate = Column(Float, default=0.0)  # Процент выполнения

    # История выполнения
    last_taken_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", backref="appointments")
    doctor = relationship("Doctor", backref="prescribed_appointments")


class AppointmentCompletion(Base):
    """Модель для отслеживания выполнения назначений"""
    __tablename__ = "appointment_completions"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("medical_appointments.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Информация о выполнении
    completion_date = Column(Date, default=func.current_date())
    completion_time = Column(String, nullable=True)
    actual_time = Column(String, nullable=True)  # Фактическое время выполнения

    # Статус выполнения
    status = Column(String, default="completed")  # completed, missed, delayed, skipped
    notes = Column(Text, nullable=True)

    # Для лекарств
    dosage_taken = Column(String, nullable=True)
    side_effects = Column(Text, nullable=True)

    # Самооценка
    pain_level_after = Column(Integer, nullable=True)
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship("MedicalAppointment", backref="completions")
    patient = relationship("Patient")


class AppointmentReminder(Base):
    """Модель для напоминаний о назначениях"""
    __tablename__ = "appointment_reminders"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("medical_appointments.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Информация о напоминании
    reminder_date = Column(Date)
    reminder_time = Column(String)
    reminder_type = Column(String)  # push, email, sms, in_app

    # Статус напоминания
    status = Column(String, default="scheduled")  # scheduled, sent, delivered, read, cancelled
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship("MedicalAppointment", backref="reminders")
    patient = relationship("Patient")


# ========== НОВЫЕ МОДЕЛИ ДЛЯ ПЛАНИРОВАНИЯ КОНСУЛЬТАЦИЙ ==========

class DoctorSchedule(Base):
    """Рабочий график врача"""
    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Рабочие дни и время
    day_of_week = Column(Integer)  # 0-6 (понедельник-воскресенье)
    start_time = Column(Time)
    end_time = Column(Time)

    # Тип приема
    appointment_type = Column(String, default="consultation")  # consultation, procedure, etc.
    slot_duration = Column(Integer, default=30)  # Длительность слота в минутах

    # Доступность
    is_active = Column(Boolean, default=True)
    max_patients_per_day = Column(Integer, nullable=True)

    # Исключения (отпуск, больничный)
    exception_date = Column(Date, nullable=True)
    exception_reason = Column(String, nullable=True)

    doctor = relationship("Doctor", backref="schedules")


class AppointmentSlot(Base):
    """Слот для записи на прием"""
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    schedule_id = Column(Integer, ForeignKey("doctor_schedules.id"), nullable=True)

    # Время слота
    slot_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)

    # Статус слота
    status = Column(String, default="available")  # available, booked, blocked, cancelled
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)

    # Метод записи
    booking_method = Column(String, nullable=True)  # online, phone, in_person

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    doctor = relationship("Doctor", backref="slots")
    schedule = relationship("DoctorSchedule")


class Consultation(Base):
    """Запись на консультацию/визит"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))

    # Тип и статус консультации
    consultation_type = Column(String)  # primary, follow_up, emergency, routine, telemedicine
    status = Column(String, default="scheduled")  # scheduled, confirmed, in_progress, completed, cancelled, no_show

    # Время консультации
    scheduled_date = Column(Date)
    scheduled_time = Column(Time)
    duration_minutes = Column(Integer, default=30)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)

    # Детали консультации
    reason = Column(Text)  # Причина обращения
    symptoms = Column(Text, nullable=True)
    preliminary_diagnosis = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Заметки врача после консультации

    # Организационные детали
    room = Column(String, nullable=True)  # Кабинет
    follow_up_date = Column(Date, nullable=True)  # Дата следующего визита
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)

    # Отзыв пациента
    patient_feedback = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    patient = relationship("Patient", backref="consultations")
    doctor = relationship("Doctor", backref="consultations")
    prescription = relationship("Prescription")

    # Обратная связь с AppointmentSlot
    slot = relationship("AppointmentSlot", backref="consultation", uselist=False)
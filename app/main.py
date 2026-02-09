# app/main.py (исправленная версия)
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys
from pathlib import Path
import traceback


def create_directories():
    """Создает все необходимые директории."""
    directories = [
        Path("data"),
        Path("app/data"),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Directory created/verified: {directory}")


# Создаем директории
create_directories()

print(f"[DEBUG] Current working directory: {os.getcwd()}")
print(f"[DEBUG] Files in app directory: {os.listdir('.')}")

# Добавляем родительскую директорию проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Импорт модулей приложения
try:
    from app.database import engine, Base, SessionLocal, get_db
    from app.utils import import_csv_data

    print("[INFO] Core modules imported successfully")

    # Импортируем роутеры
    try:
        from app.routes.auth import router as auth_router
        from app.routes.patients import router as patients_router
        from app.routes.doctors import router as doctors_router
        from app.routes.diagnoses import router as diagnoses_router
        from app.routes.prescriptions import router as prescriptions_router
        from app.routes.complaints import router as complaints_router
        from app.routes.self_monitoring import router as self_monitoring_router
        from app.routes.appointments import router as appointments_router
        from app.routes.analytics import router as analytics_router
        from app.routes.consultations import router as consultations_router

        # Пробуем импортировать медицинские карты, если файл существует
        try:
            from app.routes.medical_records import router as medical_records_router

            print("[INFO] Medical records router imported successfully")
        except ImportError:
            print("[WARNING] Medical records router not found, creating stub")
            from fastapi import APIRouter

            medical_records_router = APIRouter()


            @medical_records_router.get("/test")
            def test_medical():
                return {"message": "Medical records router stub"}

        print("[INFO] All routers imported successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import routers: {e}")
        traceback.print_exc()

        # Создаем заглушки для отладки
        from fastapi import APIRouter

        auth_router = APIRouter()
        patients_router = APIRouter()
        doctors_router = APIRouter()
        diagnoses_router = APIRouter()
        prescriptions_router = APIRouter()
        complaints_router = APIRouter()
        medical_records_router = APIRouter()


        @auth_router.get("/test")
        def test_auth():
            return {"message": "Auth router stub"}


        print("[INFO] Created stub routers")

except ImportError as e:
    print(f"[ERROR] Failed to import core modules: {e}")
    traceback.print_exc()
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске
    print("[STARTUP] Starting up Hospital Management API...")

    try:
        # Создаем таблицы в базе данных
        print("[DATABASE] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("[DATABASE] Database tables created successfully!")

        # Импортируем данные из CSV
        print("[DATA] Importing CSV data...")
        db = SessionLocal()
        try:
            import_csv_data(db)
        finally:
            db.close()

    except Exception as e:
        print(f"[ERROR] Error during startup: {e}")
        traceback.print_exc()

    yield

    # При завершении
    print("[SHUTDOWN] Shutting down...")


# Создаем приложение FastAPI
app = FastAPI(
    title="Hospital Management API",
    description="API для управления больницей с аутентификацией JWT (использует PyJWT)",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(patients_router, prefix="/api/patients", tags=["patients"])
app.include_router(doctors_router, prefix="/api/doctors", tags=["doctors"])
app.include_router(diagnoses_router, prefix="/api/diagnoses", tags=["diagnoses"])
app.include_router(prescriptions_router, prefix="/api/prescriptions", tags=["prescriptions"])
app.include_router(complaints_router, prefix="/api/complaints", tags=["complaints"])
app.include_router(self_monitoring_router, prefix="/api/self-monitoring", tags=["self monitoring"])
app.include_router(appointments_router, prefix="/api/appointments", tags=["appointments"])
app.include_router(medical_records_router, prefix="/api/medical-records", tags=["medical records"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
app.include_router(consultations_router, prefix="/api/consultations", tags=["consultations"])


@app.get("/")
def read_root():
    return {
        "message": "Hospital Management API with JWT Authentication (PyJWT)",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    print("[INFO] Starting server on http://127.0.0.1:8080")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, init_db
from models import User  # ТОЛЬКО User!
from utils import verify_password, create_access_token, create_refresh_token
import uvicorn

# Инициализация БД
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Ищем пользователя
    user = db.query(User).filter(User.email == form_data.username).first()

    # Если нет - создаем тестового
    if not user:
        from utils import get_password_hash
        user = User(
            email=form_data.username,
            password_hash=get_password_hash(form_data.password),
            role="patient",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Создан пользователь: {user.email}")

    # Проверяем пароль
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный пароль")

    # Создаем токены
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "email": user.email
    }


if __name__ == "__main__":
    print("🚀 API ЗАПУЩЕН на порту 5000")
    print("✅ Используются ТОЛЬКО модели User, Patient, Doctor")
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
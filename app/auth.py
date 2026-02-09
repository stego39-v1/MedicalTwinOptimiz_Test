# app/auth.py
from datetime import datetime, timedelta
from typing import Optional, List, Callable
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

# Импортируем только схемы
from . import schemas
from .database import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    from . import crud
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from . import crud

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ========== ПРОСТАЯ РОЛЕВАЯ СИСТЕМА ==========

def get_user_role_simple(username: str) -> str:
    """Простая логика определения роли по имени пользователя"""
    username_lower = username.lower()
    if "admin" in username_lower:
        return "admin"
    elif "doctor" in username_lower:
        return "doctor"
    else:
        return "patient"


async def get_current_user_with_role(
        current_user: schemas.User = Depends(get_current_active_user)
):
    """Добавляет роль к пользователю"""
    # Добавляем атрибут role к объекту пользователя
    current_user.role = get_user_role_simple(current_user.username)
    return current_user


# ========== ФУНКЦИИ ДЛЯ ПРОВЕРКИ РОЛЕЙ (не фабрики) ==========

async def check_admin_role(current_user: schemas.User = Depends(get_current_user_with_role)):
    """Проверяет, что пользователь администратор"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def check_doctor_role(current_user: schemas.User = Depends(get_current_user_with_role)):
    """Проверяет, что пользователь врач или администратор"""
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor or admin privileges required"
        )
    return current_user


async def check_patient_role(current_user: schemas.User = Depends(get_current_user_with_role)):
    """Проверяет, что пользователь пациент"""
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient privileges required"
        )
    return current_user


# ========== ФАБРИКИ ДЛЯ СОЗДАНИЯ ЗАВИСИМОСТЕЙ ==========

def require_admin() -> Callable:
    """Возвращает зависимость для проверки роли админа"""

    async def admin_dep(
            current_user: schemas.User = Depends(get_current_user_with_role)
    ):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return current_user

    return admin_dep


def require_doctor() -> Callable:
    """Возвращает зависимость для проверки роли врача"""

    async def doctor_dep(
            current_user: schemas.User = Depends(get_current_user_with_role)
    ):
        if current_user.role not in ["doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor or admin privileges required"
            )
        return current_user

    return doctor_dep


def require_patient() -> Callable:
    """Возвращает зависимость для проверки роли пациента"""

    async def patient_dep(
            current_user: schemas.User = Depends(get_current_user_with_role)
    ):
        if current_user.role != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient privileges required"
            )
        return current_user

    return patient_dep


def require_roles(allowed_roles: List[str]) -> Callable:
    """Фабрика для создания зависимостей с разными ролями"""

    def role_checker_factory():
        async def role_checker(
                current_user: schemas.User = Depends(get_current_user_with_role)
        ):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {allowed_roles}"
                )
            return current_user

        return role_checker

    return role_checker_factory


# ========== КОНКРЕТНЫЕ ЗАВИСИМОСТИ (для удобства) ==========

# Предварительно созданные зависимости
admin_only = require_admin()
doctor_or_admin = require_doctor()
patient_only = require_patient()
doctor_admin_only = require_roles(["doctor", "admin"])
all_roles = require_roles(["admin", "doctor", "patient"])

# Алиасы для обратной совместимости
get_current_admin_user = check_admin_role
get_current_doctor_user = check_doctor_role
get_current_patient_user = check_patient_role
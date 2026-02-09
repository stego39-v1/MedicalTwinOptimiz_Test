# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/users", tags=["users"])


# Только админы могут просматривать всех пользователей
@router.get("/", response_model=List[schemas.User])
def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


# Пользователь может просмотреть свой профиль
@router.get("/me", response_model=schemas.User)
def read_user_me(
        current_user: schemas.User = Depends(auth.get_current_active_user)
):
    return current_user


# Изменение роли пользователя (только админы)
@router.patch("/{user_id}/role")
def update_user_role(
        user_id: int,
        role_update: dict,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(auth.get_current_admin_user)
):
    if role_update.get("role") not in ["patient", "doctor", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    db_user = crud.update_user_role(db, user_id=user_id, role=role_update.get("role"))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User role updated to {role_update.get('role')}"}
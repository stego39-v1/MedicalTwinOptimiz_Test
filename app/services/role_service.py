# app/services/role_service.py
import os
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from .. import models


class RoleService:
    """Сервис управления ролями без изменения БД"""

    def __init__(self, roles_file: str = "user_roles.json"):
        self.roles_file = roles_file
        self.roles = self._load_roles()

    def _load_roles(self) -> Dict[str, str]:
        """Загружает роли из файла"""
        if os.path.exists(self.roles_file):
            try:
                with open(self.roles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_roles(self):
        """Сохраняет роли в файл"""
        with open(self.roles_file, 'w', encoding='utf-8') as f:
            json.dump(self.roles, f, ensure_ascii=False, indent=2)

    def get_user_role(self, db: Session, user_id: int) -> str:
        """Получает роль пользователя"""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return "patient"

        # Проверяем в кэше
        if user.username in self.roles:
            return self.roles[user.username]

        # Определяем роль по логину (можно расширить)
        if user.username == "admin":
            role = "admin"
        elif "doctor" in user.username.lower():
            role = "doctor"
        else:
            role = "patient"

        # Сохраняем в кэш
        self.roles[user.username] = role
        self._save_roles()

        return role

    def set_user_role(self, db: Session, user_id: int, role: str) -> bool:
        """Устанавливает роль пользователя"""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False

        self.roles[user.username] = role
        self._save_roles()
        return True

    def get_users_by_role(self, db: Session, role: str) -> List[models.User]:
        """Получает пользователей по роли"""
        all_users = db.query(models.User).all()
        return [user for user in all_users if self.get_user_role(db, user.id) == role]

    def check_permission(self, db: Session, user_id: int, required_role: str) -> bool:
        """Проверяет права доступа"""
        user_role = self.get_user_role(db, user_id)

        # Иерархия ролей
        role_hierarchy = {
            "admin": 3,
            "doctor": 2,
            "patient": 1
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level


# Глобальный экземпляр
role_service = RoleService()
# app/create_admin.py
import sys
import os

# Добавляем пути для импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from app.database import SessionLocal, engine
from app.models import User, Base
from app.auth import get_password_hash


def create_admin_user():
    print("[INFO] Initializing database...")

    # Создаем все таблицы (если их нет)
    Base.metadata.create_all(bind=engine)
    print("[INFO] Database tables created")

    db = SessionLocal()
    try:
        # Проверяем, существует ли уже админ
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                email="admin@hospital.ru",
                full_name="Администратор",
                hashed_password=get_password_hash("admin123"),
                role="admin",  # Это поле теперь есть в модели
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("[SUCCESS] Admin user created successfully")
            print("[INFO] Username: admin")
            print("[INFO] Password: admin123")
            print("[INFO] Role: admin")
        else:
            # Обновляем роль существующего админа
            admin.role = "admin"
            db.commit()
            print("[INFO] Admin user already exists, role updated to 'admin'")

        # Проверяем всех пользователей
        users = db.query(User).all()
        print(f"[INFO] Total users in database: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.email}): role={user.role}")

    except Exception as e:
        print(f"[ERROR] Failed to create admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
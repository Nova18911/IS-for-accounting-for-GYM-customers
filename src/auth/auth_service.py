# src/auth/auth_service.py
import hashlib
from src.database.connector import db
from src.models.user import User


class AuthService:
    @staticmethod
    def login(email, password):
        """Проверка логина и пароля"""
        if not email or not password:
            return None

        # Хэшируем введенный пароль
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        query = """
        SELECT user_id, email, role 
        FROM users 
        WHERE email = %s AND password_hash = %s AND is_active = TRUE
        """

        try:
            result = db.execute_query(query, (email, password_hash))

            if result and len(result) > 0:
                row = result[0]
                return User(
                    user_id=row[0],
                    email=row[1],
                    role=row[2]
                )
        except Exception as e:
            print(f"Ошибка авторизации: {e}")

        return None

    @staticmethod
    def check_table_exists():
        """Проверяет существует ли таблица users"""
        try:
            result = db.execute_query("SHOW TABLES LIKE 'users'")
            return bool(result)
        except:
            return False
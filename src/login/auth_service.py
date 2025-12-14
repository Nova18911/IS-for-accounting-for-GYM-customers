import json
from pathlib import Path

class AuthService:
    USERS_FILE = Path("src/login/users.json")

    @staticmethod
    def load_users():
        if not AuthService.USERS_FILE.exists():
            return []
        with open(AuthService.USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def login(email, password):
        """Авторизация без шифрования"""
        if not email or not password:
            return None

        users = AuthService.load_users()

        for u in users:
            if (
                u["email"] == email
                and u["password"] == password
                and u["is_active"]
            ):
                return u  # user dict: user_id, email, role

        return None

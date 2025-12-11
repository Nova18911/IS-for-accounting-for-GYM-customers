from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import pyqtSignal
from src.ui.login_window import Ui_LoginWindow
from src.database.connector import db
import hashlib


class LoginWindow(QMainWindow):
    # Сигнал успешной авторизации с данными пользователя
    login_successful = pyqtSignal(int, str, str)  # user_id, email, role

    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)

        # Устанавливаем заголовок
        self.setWindowTitle("Авторизация - Фитнес-клуб")

        # Настраиваем поле пароля
        self.ui.password.setEchoMode(self.ui.password.EchoMode.Password)

        # Подключаем кнопку входа
        self.ui.Input.clicked.connect(self.login)

        # Подключаем Enter для входа
        self.ui.password.returnPressed.connect(self.login)


    def login(self):
        try:
            # Получаем данные из полей
            email = self.ui.Email.text().strip()
            password = self.ui.password.text().strip()

            # Проверяем заполненность полей
            if not email:
                QMessageBox.warning(self, "Ошибка", "Введите email")
                self.ui.Email.setFocus()
                return
            if not password:
                QMessageBox.warning(self, "Ошибка", "Введите пароль")
                self.ui.password.setFocus()
                return

            # Проверяем подключение к БД
            if not db.connect():
                QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных")
                return

            # Хэшируем пароль для проверки
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            query = """
            SELECT user_id, email, role 
            FROM users 
            WHERE email = %s AND password_hash = %s AND is_active = TRUE
            """
            result = db.execute_query(query, (email, password_hash))

            if result and len(result) > 0:
                user_id, user_email, role = result[0]

                # Очищаем поля
                self.ui.Email.clear()
                self.ui.password.clear()

                # Отправляем сигнал с данными пользователя
                self.login_successful.emit(user_id, user_email, role)

                # Закрываем окно авторизации
                self.close()

            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Неверный email или пароль"
                )
                # Очищаем поле пароля
                self.ui.password.clear()
                self.ui.password.setFocus()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "Ошибка программы",
                f"Произошла ошибка:\n{str(e)}"
            )

    def closeEvent(self, event):
        event.accept()
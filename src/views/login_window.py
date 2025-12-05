from PyQt6.QtWidgets import QMainWindow, QMessageBox
from src.ui.login_window import Ui_LoginWindow
from src.database.connector import db
import hashlib


class LoginWindow(QMainWindow):

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

        # Устанавливаем тестовые данные
        self.ui.Email.setText("admin@fitness.ru")
        self.ui.password.setText("admin123")

        # Подключаем Enter для входа
        self.ui.password.returnPressed.connect(self.login)

        print("✅ Окно авторизации инициализировано")

    def login(self):
        """Обработка входа в систему"""
        try:
            print("\n" + "=" * 40)
            print("🔄 Попытка авторизации...")

            # Получаем данные из полей (QLineEdit использует .text())
            email = self.ui.Email.text().strip()
            password = self.ui.password.text().strip()

            print(f"📧 Email: {email}")
            print(f"🔑 Пароль: {'*' * len(password)}")

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
            print("🔌 Подключение к БД...")
            if not db.connect():
                QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных")
                print("❌ Нет подключения к БД")
                return

            print("✅ Подключение к БД успешно")

            # Хэшируем пароль для проверки
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            print(f"🔐 Хэш пароля: {password_hash[:20]}...")

            # Проверяем пользователя в БД
            query = """
            SELECT user_id, email, role 
            FROM users 
            WHERE email = %s AND password_hash = %s AND is_active = TRUE
            """

            print("📊 Выполняем запрос к БД...")
            result = db.execute_query(query, (email, password_hash))

            if result and len(result) > 0:
                user_id, user_email, role = result[0]
                print(f"✅ Успешная авторизация!")
                print(f"   ID: {user_id}")
                print(f"   Email: {user_email}")
                print(f"   Роль: {role}")

                # Показываем сообщение об успехе
                QMessageBox.information(
                    self, "✅ Успех",
                    f"Авторизация успешна!\n\n"
                    f"Добро пожаловать, {user_email}!\n"
                    f"Роль: {role}"
                )

                # Очищаем поля
                self.ui.Email.clear()
                self.ui.password.clear()

                # Закрываем окно авторизации
                print("👋 Закрываем окно авторизации...")
                self.close()

                # Здесь позже будет открытие главного окна
                # self.open_main_window(user_id, user_email, role)

            else:
                print("❌ Неверные данные для входа")
                QMessageBox.critical(
                    self, "❌ Ошибка",
                    "Неверный email или пароль\n\n"
                    "Доступные пользователи:\n"
                    "• admin@fitness.ru / admin123\n"
                    "• reception@fitness.ru / reception123"
                )

                # Очищаем поле пароля
                self.ui.password.clear()
                self.ui.password.setFocus()

        except Exception as e:
            print(f"💥 Ошибка: {e}")
            import traceback
            traceback.print_exc()

            QMessageBox.critical(
                self, "💥 Ошибка программы",
                f"Произошла ошибка:\n{str(e)}"
            )

        if result and len(result) > 0:
            user_id, user_email, role = result[0]
            print(f"✅ Успешная авторизация!")

            QMessageBox.information(
                self, "✅ Успех",
                f"Авторизация успешна!\n\n"
                f"Добро пожаловать, {user_email}!"
            )

            # Очищаем поля
            self.ui.Email.clear()
            self.ui.password.clear()

            # Закрываем окно авторизации
            print("👋 Закрываем окно авторизации...")
            self.close()

            # Открываем главное окно
            self.open_main_window(user_id, user_email, role)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        print("👋 Окно закрывается...")
        print("=" * 40)
        event.accept()




# Для тестирования
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    print("🚀 ЗАПУСК ТЕСТА АВТОРИЗАЦИИ")
    print("=" * 50)

    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())
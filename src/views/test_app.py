import sys
from PyQt6.QtWidgets import QApplication
from src.views.login_window import LoginWindow
from src.views.main_window import MainWindow


class FitnessApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.main_window = None

        # Подключаем сигнал успешной авторизации
        self.login_window.login_successful.connect(self.on_login_success)

    def on_login_success(self, user_id, user_email, user_role):
        # Создаем и показываем main_window (он будет мгновенно открыт и закрыт)
        self.main_window = MainWindow(user_id, user_email, user_role)
        self.main_window.show()  # Показываем на мгновение (прозрачное окно)

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    fitness_app = FitnessApp()
    fitness_app.run()
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import pyqtSignal
from src.login.login_window_form import Ui_LoginWindow
from src.login.auth_service import AuthService


class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(int, str, str)

    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Авторизация - Фитнес-клуб")

        self.ui.password.setEchoMode(self.ui.password.EchoMode.Password)

        self.ui.Input.clicked.connect(self.login)
        self.ui.password.returnPressed.connect(self.login)

    def login(self):
        email = self.ui.Email.text().strip()
        password = self.ui.password.text().strip()

        if not email:
            QMessageBox.warning(self, "Ошибка", "Введите email")
            return

        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            return

        user = AuthService.login(email, password)

        if user:
            self.login_successful.emit(
                user["user_id"],
                user["email"],
                user["role"]
            )
            self.close()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный email или пароль")
            self.ui.password.clear()
            self.ui.password.setFocus()

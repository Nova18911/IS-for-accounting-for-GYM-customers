from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer
from src.database.connector import db


class MainWindow(QMainWindow):
    def __init__(self, user_id, user_email, user_role):
        super().__init__()

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Устанавливаем заголовок
        self.setWindowTitle(f"Фитнес-клуб - {user_email} ({user_role})")
        self.setGeometry(100, 100, 1200, 700)

        # Делаем окно прозрачным и без рамки (чтобы не было видно)
        self.setWindowOpacity(0)  # Полностью прозрачное
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # Без рамки

        # Таймер для автоматического закрытия и открытия service_window
        QTimer.singleShot(50, self.switch_to_service_window)

    def switch_to_service_window(self):
        """Закрываем это окно и открываем service_window"""
        from src.views.service_window import ServiceForm

        # Создаем и показываем окно услуг
        self.service_window = ServiceForm()
        self.service_window.show()

        # Закрываем это окно
        self.close()
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt
from src.database.connector import db


class MainWindow(QMainWindow):
    def __init__(self, user_id, user_email, user_role):
        super().__init__()

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        self.setWindowTitle(f"Фитнес-клуб - {user_email} ({user_role})")
        self.setGeometry(100, 100, 1200, 700)

        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса с боковой панелью"""
        # Главный виджет
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== ЛЕВАЯ ПАНЕЛЬ (НАВИГАЦИЯ) =====
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
            }
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Заголовок "Админ-панель"
        admin_label = QLabel("Админ-панель")
        admin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        admin_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                background-color: #34495e;
                border-bottom: 2px solid #1abc9c;
            }
        """)
        admin_label.setFixedHeight(70)
        sidebar_layout.addWidget(admin_label)

        # Информация о пользователе
        user_info = QLabel(f"{self.user_email}\n{self.user_role}")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 12px;
                padding: 10px;
                border-bottom: 1px solid #34495e;
            }
        """)
        sidebar_layout.addWidget(user_info)

        # Кнопки навигации
        nav_buttons = [
            ("🏋️ Залы", "halls"),
            ("💪 Услуги", "services"),
            ("👤 Клиенты", "clients"),
            ("🏃 Тренеры", "trainers"),
            ("📅 Расписание", "schedule"),
            ("🎫 Абонементы", "subscriptions"),
            ("📊 Отчеты", "reports")
        ]

        for text, page_name in nav_buttons:
            btn = QPushButton(text)
            btn.setObjectName(f"btn_{page_name}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    text-align: left;
                    padding: 15px 20px;
                    border: none;
                    font-size: 14px;
                    border-left: 4px solid transparent;
                }
                QPushButton:hover {
                    background-color: #34495e;
                    border-left: 4px solid #1abc9c;
                }
                QPushButton:pressed {
                    background-color: #16a085;
                }
            """)
            btn.clicked.connect(lambda checked, name=page_name: self.switch_page(name))
            sidebar_layout.addWidget(btn)

        # Растягивающийся спейсер
        sidebar_layout.addStretch()

        # Кнопка выхода
        exit_btn = QPushButton("🚪 Выход")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 15px;
                margin: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(exit_btn)

        sidebar.setLayout(sidebar_layout)

        # ===== ПРАВАЯ ЧАСТЬ (КОНТЕНТ) =====
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #ecf0f1;
            }
        """)

        # Создаем страницы контента
        self.pages = {}
        self.create_pages()

        # Добавляем в главный layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_stack, 1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def create_pages(self):
        """Создает страницы для каждой вкладки"""
        # Страница заглушка (по умолчанию)
        default_page = QLabel("👈 Выберите раздел в меню слева")
        default_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_page.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        self.content_stack.addWidget(default_page)

        # Здесь позже будут настоящие окна
        # self.pages['halls'] = HallsWindow()
        # self.content_stack.addWidget(self.pages['halls'])

    def switch_page(self, page_name):
        """Переключает страницы"""
        if page_name in self.pages:
            self.content_stack.setCurrentWidget(self.pages[page_name])
        else:
            # Временно показываем сообщение
            msg = QLabel(f"Раздел '{page_name}' в разработке")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet("font-size: 18px; color: #2c3e50; padding: 50px;")

            # Удаляем старый виджет если есть
            for i in range(self.content_stack.count()):
                if self.content_stack.widget(i) != self.content_stack.widget(0):
                    self.content_stack.removeWidget(self.content_stack.widget(i))

            self.content_stack.addWidget(msg)
            self.content_stack.setCurrentWidget(msg)
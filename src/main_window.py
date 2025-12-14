# src/main_window.py
from PyQt6.QtWidgets import QMainWindow
from src.ui.main_window import Ui_MainWindow
from src.views.client_page import ClientPageController
from src.views.hall_page import HallPageController
from src.views.service_page import ServicePageController
from src.views.trainer_page import TrainerPageController
from src.views.schedule_page import SchedulePageController
from src.views.report_page import ReportsPageController

class MainWindow(QMainWindow):
    def __init__(self, user_id, user_email, user_role):
        super().__init__()

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Заголовок окна
        self.setWindowTitle(f"Фитнес-клуб — {user_email} ({user_role})")

        # Создаём контроллеры страниц
        self.hall_controller = HallPageController(self.ui)
        self.service_controller = ServicePageController(self.ui)
        self.trainer_controller = TrainerPageController(self.ui)
        self.schedule_controller = SchedulePageController(self.ui)
        self.client_controller = ClientPageController(self.ui)
        self.report_controller = ReportsPageController(self.ui)

        # Страница по умолчанию — услуги
        self.ui.stackedWidget.setCurrentWidget(self.ui.ServicePage)

        self._connect_buttons()

    def _connect_buttons(self):
        self.ui.ServiceButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.ServicePage)
        )

        self.ui.ScheduleButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.SchedulePage)
        )

        self.ui.ClientsButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.ClientPage)
        )

        self.ui.TrainerButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.TrainerPage)
        )

        self.ui.HallButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.HallPage)
        )

        self.ui.ReportButton.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.ReportPage)
        )

        self.ui.ExitButton.clicked.connect(self.close)

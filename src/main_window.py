from PyQt6.QtCore import Qt
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

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

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
        self.show_services()  # Сразу вызываем метод с обновлением

        self._connect_buttons()

    def _connect_buttons(self):
        # Привязываем кнопки к методам обновления и показа
        self.ui.ServiceButton.clicked.connect(self.show_services)
        self.ui.ScheduleButton.clicked.connect(self.show_schedule)
        self.ui.ClientsButton.clicked.connect(self.show_clients)
        self.ui.TrainerButton.clicked.connect(self.show_trainers)
        self.ui.HallButton.clicked.connect(self.show_halls)
        self.ui.ReportButton.clicked.connect(self.show_reports)
        self.ui.ExitButton.clicked.connect(self.close)


    def show_services(self):
        self.service_controller.load_halls()  # Обновляет ComboBox
        self.service_controller.load_services()  # Обновляет саму таблицу
        self.ui.stackedWidget.setCurrentWidget(self.ui.ServicePage)

    def show_schedule(self):
        if hasattr(self.schedule_controller, 'load_trainers'):
            self.schedule_controller.load_trainers()
        if hasattr(self.schedule_controller, 'load_services'):
            self.schedule_controller.load_services()
        if hasattr(self.schedule_controller, 'load_group_trainings'):
            self.schedule_controller.load_group_trainings()

        self.ui.stackedWidget.setCurrentWidget(self.ui.SchedulePage)

    def show_clients(self):
        if hasattr(self.client_controller, 'load_clients'):
            self.client_controller.load_clients()
        if hasattr(self.client_controller, 'load_subscriptions'):
            self.client_controller.load_subscriptions()

        self.ui.stackedWidget.setCurrentWidget(self.ui.ClientPage)

    def show_trainers(self):
        if hasattr(self.trainer_controller, 'load_trainers'):
            self.trainer_controller.load_trainers()
        if hasattr(self.trainer_controller, 'load_trainer_types'):
            self.trainer_controller.load_trainer_types()

        self.ui.stackedWidget.setCurrentWidget(self.ui.TrainerPage)

    def show_halls(self):
        # Метод load_halls в HallPageController обновляет главную таблицу залов
        self.hall_controller.load_halls()
        self.ui.stackedWidget.setCurrentWidget(self.ui.HallPage)

    def show_reports(self):
        if hasattr(self.report_controller, 'load_report_data'):
            self.report_controller.load_report_data()
        self.ui.stackedWidget.setCurrentWidget(self.ui.ReportPage)
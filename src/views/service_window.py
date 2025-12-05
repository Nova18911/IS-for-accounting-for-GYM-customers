from PyQt6.QtWidgets import QMainWindow, QMessageBox
from src.ui.generated_ui.service_window import Ui_ServiceWindow
from src.ui.generated_ui.main_window import Ui_MainWindow  # Для других окон
from src.database.connector import db


class ServiceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ServiceWindow()
        self.ui.setupUi(self)

        # Инициализация
        self.db = db()

        # Загружаем данные в таблицу
        self.load_services()

        # Подключаем кнопки
        self.ui.pushButton.clicked.connect(self.add_service)
        self.ui.ExitButton.clicked.connect(self.close)

        # Подключаем кнопки навигации
        self.ui.ServiceButton.clicked.connect(self.show_services)
        self.ui.ClientsButton.clicked.connect(self.show_clients)
        self.ui.TrainerButton.clicked.connect(self.show_trainers)
        self.ui.HallButton.clicked.connect(self.show_halls)
        self.ui.ScheduleButton.clicked.connect(self.show_schedule)
        self.ui.ReportButton.clicked.connect(self.show_reports)

        # Делаем кнопку "Услуги" неактивной (мы уже в услугах)
        self.ui.ServiceButton.setEnabled(False)

    def load_services(self):
        """Загрузка услуг из БД в таблицу"""
        # Очищаем таблицу
        self.ui.TableService.setRowCount(0)

        # Запрос к БД (пример)
        query = """
        SELECT s.name, h.name, h.max_capacity, s.price 
        FROM services s 
        JOIN halls h ON s.hall_id = h.id
        """

        try:
            services = self.db.execute_query(query, fetch_all=True)

            for row_num, service in enumerate(services):
                self.ui.TableService.insertRow(row_num)

                for col_num, value in enumerate(service):
                    item = QTableWidgetItem(str(value))
                    self.ui.TableService.setItem(row_num, col_num, item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить услуги: {str(e)}")

    def add_service(self):
        """Открытие окна для добавления новой услуги"""
        from src.views.service_dialog import ServiceDialog
        dialog = ServiceDialog(self)
        if dialog.exec():
            self.load_services()  # Обновляем таблицу

    def show_services(self):
        """Показываем услуги (уже показываем)"""
        # Ничего не делаем, мы уже в услугах
        pass

    def show_clients(self):
        """Открываем окно клиентов"""
        from src.views.clients_window import ClientsWindow
        self.clients_window = ClientsWindow()
        self.clients_window.show()
        self.hide()  # Скрываем текущее окно

    def show_trainers(self):
        """Открываем окно тренеров"""
        from src.views.trainers_window import TrainersWindow
        self.trainers_window = TrainersWindow()
        self.trainers_window.show()
        self.hide()

    def show_halls(self):
        """Открываем окно залов"""
        from src.views.halls_window import HallsWindow
        self.halls_window = HallsWindow()
        self.halls_window.show()
        self.hide()

    def show_schedule(self):
        """Открываем окно расписания"""
        from src.views.schedule_window import ScheduleWindow
        self.schedule_window = ScheduleWindow()
        self.schedule_window.show()
        self.hide()

    def show_reports(self):
        """Открываем окно отчетов"""
        from src.views.reports_window import ReportsWindow
        self.reports_window = ReportsWindow()
        self.reports_window.show()
        self.hide()
# src/views/reports_page.py
from PyQt6.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from datetime import date, datetime
from src.database.connector import db
from datetime import date
from src.models.client import client_get_all
from src.models.subscriptions import subscription_get_by_id, subscription_calculate_end
from src.models.subscription_prices import subscription_price_get_by_id
from src.models.trainers import trainer_get_all

class ReportsPageController:
    """Контроллер вкладки 'Отчеты'."""

    def __init__(self, ui):
        self.ui = ui
        self.connect_buttons()

    # ---------------- connect ----------------
    def connect_buttons(self):
        self.ui.ReportClientBtn.clicked.connect(self.report_clients)
        self.ui.ReportMMRbtn.clicked.connect(self.report_mmr)
        self.ui.ReportSalaryFundBtn.clicked.connect(self.report_salary)
        self.ui.ReportTrainerBtn.clicked.connect(self.report_trainers)

    # ---------------- utilities ----------------
    def clear_table(self):
        self.ui.ReportTable.clear()
        self.ui.ReportTable.setRowCount(0)
        self.ui.ReportTable.setColumnCount(0)

    # ---------------------------
    # Количество персональных тренировок тренера за месяц
    # ---------------------------
    def get_personal_trainings_count(self, trainer_id, month, year):
        rows = db.execute_query("""
            SELECT COUNT(*) 
            FROM personal_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        return rows[0][0] if rows else 0

    # ---------------------------
    # Количество групповых тренировок тренера за месяц
    # ---------------------------
    def get_group_trainings_count(self, trainer_id, month, year):
        rows = db.execute_query("""
            SELECT COUNT(*) 
            FROM group_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        return rows[0][0] if rows else 0

    # ---------------------------
    # Выручка тренера за месяц
    # ---------------------------
    def get_trainer_revenue(self, trainer_id, month, year):
        # Персональные тренировки
        personal = db.execute_query("""
            SELECT COALESCE(SUM(price), 0)
            FROM personal_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        personal_sum = personal[0][0] if personal else 0

        # Групповые тренировки (цена берётся из услуги)
        group = db.execute_query("""
            SELECT COALESCE(SUM(s.price), 0)
            FROM group_trainings gt
            JOIN services s ON gt.service_id = s.service_id
            JOIN group_attendances ga ON gt.group_training_id = ga.group_training_id
            WHERE gt.trainer_id=%s AND MONTH(gt.training_date)=%s AND YEAR(gt.training_date)=%s
        """, (trainer_id, month, year))
        group_sum = group[0][0] if group else 0

        return personal_sum + group_sum

    # ---------------------------
    # Количество клиентов, которых тренер тренировал за месяц
    # ---------------------------
    def get_clients_trained(self, trainer_id, month, year):
        rows = db.execute_query("""
            SELECT COUNT(DISTINCT client_id)
            FROM (
                SELECT client_id, training_date FROM personal_trainings
                WHERE trainer_id=%s
                UNION ALL
                SELECT ga.client_id, gt.training_date
                FROM group_trainings gt
                JOIN group_attendances ga ON gt.group_training_id = ga.group_training_id
                WHERE gt.trainer_id=%s
            ) AS combined
            WHERE MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, trainer_id, month, year))
        return rows[0][0] if rows else 0

    # ---------------------------
    # Количество ушедших клиентов тренера за месяц
    # ---------------------------
    def get_churned_clients(self, trainer_id, month, year):
        # Предположим, что ушедшие клиенты — это те, кто был на тренировках тренера до начала месяца,
        # но не посещал тренировки в текущем месяце
        first_day_of_month = date(year, month, 1)
        rows = db.execute_query("""
            SELECT COUNT(DISTINCT client_id)
            FROM (
                SELECT client_id FROM personal_trainings
                WHERE trainer_id=%s AND training_date < %s
                UNION
                SELECT ga.client_id
                FROM group_trainings gt
                JOIN group_attendances ga ON gt.group_training_id = ga.group_training_id
                WHERE gt.trainer_id=%s AND gt.training_date < %s
            ) AS prev_clients
            WHERE client_id NOT IN (
                SELECT client_id FROM personal_trainings
                WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
                UNION
                SELECT ga.client_id
                FROM group_trainings gt
                JOIN group_attendances ga ON gt.group_training_id = ga.group_training_id
                WHERE gt.trainer_id=%s AND MONTH(gt.training_date)=%s AND YEAR(gt.training_date)=%s
            )
        """, (trainer_id, first_day_of_month, trainer_id, first_day_of_month,
              trainer_id, month, year, trainer_id, month, year))
        return rows[0][0] if rows else 0


    # ---------------- MMR ----------------
    def report_mmr(self):
        total_mmr = 0
        new_revenue = 0
        today = date.today()
        current_month = today.month
        current_year = today.year

        # Получаем всех клиентов
        clients = client_get_all()
        for client in clients:
            sub_id = client.get("subscription_id")
            if not sub_id:
                continue
            sub = subscription_get_by_id(sub_id)
            if not sub:
                continue

            price = subscription_price_get_by_id(sub["subscription_price_id"])
            if not price:
                continue

            # Приводим цену к числу
            price_value = int(price["price"])

            # Считаем MMR (всех активных)
            total_mmr += price_value

            # Проверка, новый доход — если активация в этом месяце
            start_date = sub["start_date"]
            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

            if start_date.month == current_month and start_date.year == current_year:
                new_revenue += price_value

        # Заполняем таблицу отчета
        self.ui.ReportTable.setRowCount(3)
        self.ui.ReportTable.setColumnCount(2)
        self.ui.ReportTable.setItem(0, 0, QTableWidgetItem("Текущий MMR"))
        self.ui.ReportTable.setItem(0, 1, QTableWidgetItem(str(total_mmr)))
        self.ui.ReportTable.setItem(1, 0, QTableWidgetItem("Новый MMR за месяц"))
        self.ui.ReportTable.setItem(1, 1, QTableWidgetItem(str(new_revenue)))
        self.ui.ReportTable.setItem(2, 0, QTableWidgetItem("Изменение по сравнению с прошлым месяцем"))
        self.ui.ReportTable.setItem(2, 1, QTableWidgetItem("0"))

    # ---------------- Clients ----------------
    def report_clients(self):
        today = date.today()
        all_clients = client_get_all()

        start_year_clients = [c for c in all_clients if c.get("subscription_id")]
        new_clients = []
        churned_clients = []

        for c in all_clients:
            sub = subscription_get_by_id(c.get("subscription_id"))
            if not sub:
                continue
            price = subscription_price_get_by_id(sub["subscription_price_id"])
            if not price:
                continue
            start_date = sub["start_date"]
            end_date = subscription_calculate_end(start_date, price["duration"])
            if start_date.year == today.year and start_date.month == today.month:
                new_clients.append(c)
            elif end_date.year == today.year and end_date.month == today.month and end_date < today:
                churned_clients.append(c)

        retention = ((len(all_clients) - len(new_clients)) / max(len(start_year_clients), 1)) * 100

        self.clear_table()
        self.ui.ReportTable.setColumnCount(2)
        self.ui.ReportTable.setRowCount(4)
        self.ui.ReportTable.setHorizontalHeaderLabels(["Показатель", "Значение"])
        self.ui.ReportTable.setItem(0, 0, QTableWidgetItem("Общее число клиентов"))
        self.ui.ReportTable.setItem(0, 1, QTableWidgetItem(str(len(all_clients))))
        self.ui.ReportTable.setItem(1, 0, QTableWidgetItem("Новые клиенты за месяц"))
        self.ui.ReportTable.setItem(1, 1, QTableWidgetItem(str(len(new_clients))))
        self.ui.ReportTable.setItem(2, 0, QTableWidgetItem("Отток клиентов за месяц"))
        self.ui.ReportTable.setItem(2, 1, QTableWidgetItem(str(len(churned_clients))))
        self.ui.ReportTable.setItem(3, 0, QTableWidgetItem("Уровень удержания, %"))
        self.ui.ReportTable.setItem(3, 1, QTableWidgetItem(f"{retention:.2f}"))

    # ---------------- Salary Rund ----------------
    def report_salary(self):
        today = date.today()
        month = today.month
        year = today.year

        trainers = trainer_get_all()
        self.clear_table()
        self.ui.ReportTable.setColumnCount(4)
        self.ui.ReportTable.setHorizontalHeaderLabels(["Тренер", "Должность", "Зарплата", "Выручка"])
        self.ui.ReportTable.setRowCount(len(trainers))

        for row, tr in enumerate(trainers):
            # Получаем количество и выручку
            personal_trainings = self.get_personal_trainings_count(tr["trainer_id"], month, year)
            group_trainings = self.get_group_trainings_count(tr["trainer_id"], month, year)
            revenue = self.get_trainer_revenue(tr["trainer_id"], month, year)

            # Рассчитываем зарплату по типу тренера
            rate = tr.get("rate", 0)  # на всякий случай проверяем наличие
            if tr["trainer_type_name"] == "Персональный тренер":
                salary = personal_trainings * rate
            elif tr["trainer_type_name"] == "Групповой тренер":
                salary = group_trainings * rate
            else:  # Общий тренер
                salary = personal_trainings * rate + group_trainings * rate

            # Заполняем таблицу
            self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(f"{tr['last_name']} {tr['first_name']}"))
            self.ui.ReportTable.setItem(row, 1, QTableWidgetItem(tr["trainer_type_name"]))
            self.ui.ReportTable.setItem(row, 2, QTableWidgetItem(str(salary)))
            self.ui.ReportTable.setItem(row, 3, QTableWidgetItem(str(revenue)))

    # ---------------- Trainer Report ----------------
    def report_trainers(self):
        today = date.today()
        month = today.month
        year = today.year

        trainers = trainer_get_all()
        self.clear_table()
        self.ui.ReportTable.setColumnCount(5)
        self.ui.ReportTable.setHorizontalHeaderLabels([
            "Тренер", "Выручка", "Кол-во тренировок", "Кол-во клиентов", "Ушедшие клиенты"
        ])
        self.ui.ReportTable.setRowCount(len(trainers))

        for row, tr in enumerate(trainers):
            revenue = self.get_trainer_revenue(tr["trainer_id"], month, year)
            trainings_count = self.get_personal_trainings_count(tr["trainer_id"], month, year) + self.get_group_trainings_count(tr["trainer_id"], month, year)
            clients_count = self.get_clients_trained(tr["trainer_id"], month, year)
            churned_count = self.get_churned_clients(tr["trainer_id"], month, year)

            self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(f"{tr['last_name']} {tr['first_name']}"))
            self.ui.ReportTable.setItem(row, 1, QTableWidgetItem(str(revenue)))
            self.ui.ReportTable.setItem(row, 2, QTableWidgetItem(str(trainings_count)))
            self.ui.ReportTable.setItem(row, 3, QTableWidgetItem(str(clients_count)))
            self.ui.ReportTable.setItem(row, 4, QTableWidgetItem(str(churned_count)))

from PyQt6.QtWidgets import QTableWidgetItem
from src.database.connector import db
from datetime import date
from src.models.trainers import trainer_get_all

class ReportsPageController:

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
        today = date.today()
        # SQL запрос сразу считает общий MMR и доход от новых активаций за текущий месяц
        sql = """
            SELECT 
                SUM(sp.price) as total_mmr,
                SUM(CASE 
                    WHEN MONTH(s.start_date) = %s AND YEAR(s.start_date) = %s 
                    THEN sp.price ELSE 0 
                END) as new_revenue
            FROM subscriptions s
            JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
            JOIN clients c ON c.subscription_id = s.subscription_id
        """
        result = db.execute_query(sql, (today.month, today.year))
        total_mmr, new_revenue = result[0] if result else (0, 0)

        self.clear_table()
        self.ui.ReportTable.setRowCount(2)
        self.ui.ReportTable.setColumnCount(2)
        self.ui.ReportTable.setHorizontalHeaderLabels(["Показатель", "Сумма (₽)"])
        self.ui.ReportTable.setItem(0, 0, QTableWidgetItem("Текущий прогнозируемый MMR"))
        self.ui.ReportTable.setItem(0, 1, QTableWidgetItem(f"{total_mmr or 0}"))
        self.ui.ReportTable.setItem(1, 0, QTableWidgetItem("Новые продажи за месяц"))
        self.ui.ReportTable.setItem(1, 1, QTableWidgetItem(f"{new_revenue or 0}"))

    # ---------------- Clients ----------------
    def report_clients(self):
        today = date.today()
        # Считаем всё одним запросом через подзапросы
        sql = """
            SELECT
                (SELECT COUNT(*) FROM clients) as total,
                (SELECT COUNT(*) FROM clients c 
                 JOIN subscriptions s ON c.subscription_id = s.subscription_id 
                 WHERE MONTH(s.start_date) = %s AND YEAR(s.start_date) = %s) as new_clients,
                (SELECT COUNT(*) FROM clients c 
                 JOIN subscriptions s ON c.subscription_id = s.subscription_id
                 JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
                 WHERE (s.start_date + INTERVAL (CASE sp.duration 
                    WHEN '1 месяц' THEN 30 
                    WHEN '3 месяца' THEN 90 
                    WHEN 'полгода' THEN 180 
                    WHEN 'год' THEN 365 END) DAY) < %s) as expired_total
        """
        res = db.execute_query(sql, (today.month, today.year, today))
        total, new, expired = res[0] if res else (0,0,0)

        retention = ((total - new) / max(total, 1)) * 100

        self.clear_table()
        self.ui.ReportTable.setColumnCount(2)
        self.ui.ReportTable.setRowCount(4)
        self.ui.ReportTable.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self.ui.ReportTable.setItem(0, 0, QTableWidgetItem("База клиентов (всего)"))
        self.ui.ReportTable.setItem(0, 1, QTableWidgetItem(str(total)))
        self.ui.ReportTable.setItem(1, 0, QTableWidgetItem("Прирост (новые)"))
        self.ui.ReportTable.setItem(1, 1, QTableWidgetItem(str(new)))
        self.ui.ReportTable.setItem(2, 0, QTableWidgetItem("Уровень удержания (Retention)"))
        self.ui.ReportTable.setItem(2, 1, QTableWidgetItem(f"{retention:.1f}%"))

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
        self.ui.ReportTable.setColumnCount(4)
        self.ui.ReportTable.setHorizontalHeaderLabels([
            "Тренер", "Кол-во тренировок", "Кол-во клиентов", "Ушедшие клиенты"
        ])
        self.ui.ReportTable.setRowCount(len(trainers))

        for row, tr in enumerate(trainers):
            trainings_count = self.get_personal_trainings_count(tr["trainer_id"], month, year) + self.get_group_trainings_count(tr["trainer_id"], month, year)
            clients_count = self.get_clients_trained(tr["trainer_id"], month, year)
            churned_count = self.get_churned_clients(tr["trainer_id"], month, year)

            self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(f"{tr['last_name']} {tr['first_name']}"))
            self.ui.ReportTable.setItem(row, 2, QTableWidgetItem(str(trainings_count)))
            self.ui.ReportTable.setItem(row, 3, QTableWidgetItem(str(clients_count)))
            self.ui.ReportTable.setItem(row, 4, QTableWidgetItem(str(churned_count)))

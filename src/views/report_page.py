from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem
from src.database.connector import db
from datetime import date
from src.models.trainers import trainer_get_all

class ReportsPageController:
    def __init__(self, ui):
        self.ui = ui
        self.connect_buttons()

    def connect_buttons(self):
        self.ui.ReportClientBtn.clicked.connect(self.report_clients)
        self.ui.ReportMMRbtn.clicked.connect(self.report_mmr)
        self.ui.ReportSalaryFundBtn.clicked.connect(self.report_salary)
        self.ui.ReportTrainerBtn.clicked.connect(self.report_trainers)

    def clear_table(self):
        self.ui.ReportTable.clear()
        self.ui.ReportTable.setRowCount(0)
        self.ui.ReportTable.setColumnCount(0)

    # Количество персональных тренировок тренера за месяц
    def get_personal_trainings_count(self, trainer_id, month, year):
        rows = db.execute_query("""
            SELECT COUNT(*) 
            FROM personal_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        return rows[0][0] if rows else 0

    # Количество групповых тренировок тренера за месяц
    def get_group_trainings_count(self, trainer_id, month, year):
        rows = db.execute_query("""
            SELECT COUNT(*) 
            FROM group_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        return rows[0][0] if rows else 0

    # Выручка тренера за месяц
    def get_trainer_revenue(self, trainer_id, month, year):
        # Персональные тренировки
        personal = db.execute_query("""
            SELECT COALESCE(SUM(price), 0)
            FROM personal_trainings
            WHERE trainer_id=%s AND MONTH(training_date)=%s AND YEAR(training_date)=%s
        """, (trainer_id, month, year))
        personal_sum = personal[0][0] if personal else 0

        # Групповые тренировки
        group = db.execute_query("""
            SELECT COALESCE(SUM(s.price), 0)
            FROM group_trainings gt
            JOIN services s ON gt.service_id = s.service_id
            JOIN group_attendances ga ON gt.group_training_id = ga.group_training_id
            WHERE gt.trainer_id=%s AND MONTH(gt.training_date)=%s AND YEAR(gt.training_date)=%s
        """, (trainer_id, month, year))
        group_sum = group[0][0] if group else 0

        return personal_sum + group_sum

    # Количество клиентов, которых тренер тренировал за месяц
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


    # Количество ушедших клиентов тренера за месяц
    def get_churned_clients(self, trainer_id, month, year):
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

    # MMR
    def report_mmr(self):
        today = date.today()
        # Вычисляем первый день текущего месяца и первый день прошлого месяца
        first_day_current = today.replace(day=1)
        if today.month == 1:
            first_day_prev = today.replace(year=today.year - 1, month=12, day=1)
        else:
            first_day_prev = today.replace(month=today.month - 1, day=1)

        sql = """
            SELECT 
                (SELECT SUM(sp.price) 
                 FROM subscriptions s 
                 JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
                 JOIN clients c ON c.subscription_id = s.subscription_id) as total_mmr,

                (SELECT SUM(sp.price) 
                 FROM subscriptions s 
                 JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
                 WHERE MONTH(s.start_date) = %s AND YEAR(s.start_date) = %s) as new_revenue,

                (SELECT SUM(sp.price) 
                 FROM subscriptions s 
                 JOIN subscription_prices sp ON s.subscription_price_id = sp.subscription_price_id
                 WHERE s.start_date < %s) as prev_mmr
        """

        result = db.execute_query(sql, (today.month, today.year, first_day_current))
        total_mmr, new_revenue, prev_mmr = result[0] if result else (0, 0, 0)

        total_mmr = total_mmr or 0
        new_revenue = new_revenue or 0
        prev_mmr = prev_mmr or 0

        change = total_mmr - prev_mmr
        change_text = f"+{change}" if change > 0 else str(change)

        self.clear_table()
        self.ui.ReportTable.setRowCount(3)
        self.ui.ReportTable.setColumnCount(2)
        self.ui.ReportTable.setHorizontalHeaderLabels(["Метрика", "Значение (₽)"])

        data = [
            ("Текущий MMR", f"{total_mmr}"),
            ("Новый MMR (за месяц)", f"{new_revenue}"),
            ("Изменение к прошлому месяцу", change_text)
        ]

        for i, (label, val) in enumerate(data):
            self.ui.ReportTable.setItem(i, 0, QTableWidgetItem(label))
            item_val = QTableWidgetItem(val)
            # Подсветим изменение цветом
            if i == 2:
                if change > 0:
                    item_val.setForeground(Qt.GlobalColor.green)
                elif change < 0:
                    item_val.setForeground(Qt.GlobalColor.red)
            self.ui.ReportTable.setItem(i, 1, item_val)


    def report_clients(self):
        try:
            today = date.today()
            # Начало текущего месяца
            first_day_month = today.replace(day=1)
            # Начало текущего года
            first_day_year = date(today.year, 1, 1)

            sql = """
                SELECT
                    -- 1. Всего клиентов в базе (вообще всех)
                    (SELECT COUNT(*) FROM clients) as total_end,

                    -- 2. Новые клиенты (кто купил абонемент в этом месяце)
                    (SELECT COUNT(*) FROM subscriptions 
                     WHERE start_date >= %s) as new_clients,

                    -- 3. Клиенты, которые были в базе ДО начала этого года
                    (SELECT COUNT(*) FROM subscriptions 
                     WHERE start_date < %s) as total_start_year
            """

            res = db.execute_query(sql, (first_day_month, first_day_year))
            total_end, new_month, total_start_year = res[0] if res else (0, 0, 0)

            if total_start_year == 0:
                retention = 100.0 if total_end > 0 else 0.0
            else:
                retention = ((total_end - new_month) / total_start_year) * 100

            self.clear_table()
            self.ui.ReportTable.setColumnCount(2)
            self.ui.ReportTable.setRowCount(3)
            self.ui.ReportTable.setHorizontalHeaderLabels(["Показатель", "Значение"])

            report_data = [
                ("Общее количество клиентов", str(total_end)),
                ("Новые клиенты (за месяц)", str(new_month)),
                ("Коэффициент удержания", f"{retention:.2f}%")
            ]

            for row, (label, value) in enumerate(report_data):
                self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(label))
                self.ui.ReportTable.setItem(row, 1, QTableWidgetItem(value))

            self.ui.ReportTable.horizontalHeader().setStretchLastSection(True)

        except Exception as e:
            print(f"Ошибка в отчете: {e}")

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
            rate = tr.get("rate", 0)
            if tr["trainer_type_name"] == "Персональный тренер":
                salary = personal_trainings * rate
            elif tr["trainer_type_name"] == "Групповой тренер":
                salary = group_trainings * rate
            else:  # Общий тренер
                salary = personal_trainings * rate + group_trainings * rate

            self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(f"{tr['last_name']} {tr['first_name']}"))
            self.ui.ReportTable.setItem(row, 1, QTableWidgetItem(tr["trainer_type_name"]))
            self.ui.ReportTable.setItem(row, 2, QTableWidgetItem(str(salary)))
            self.ui.ReportTable.setItem(row, 3, QTableWidgetItem(str(revenue)))

    # Отчет по тренерам
    def report_trainers(self):
        today = date.today()
        month = today.month
        year = today.year

        trainers = trainer_get_all()
        self.clear_table()
        self.ui.ReportTable.setColumnCount(3)
        self.ui.ReportTable.setHorizontalHeaderLabels([
            "Тренер", "Кол-во клиентов", "Ушедшие клиенты"
        ])
        self.ui.ReportTable.setRowCount(len(trainers))

        for row, tr in enumerate(trainers):
            clients_count = self.get_clients_trained(tr["trainer_id"], month, year)
            churned_count = self.get_churned_clients(tr["trainer_id"], month, year)

            self.ui.ReportTable.setItem(row, 0, QTableWidgetItem(f"{tr['last_name']} {tr['first_name']}"))
            self.ui.ReportTable.setItem(row, 1, QTableWidgetItem(str(clients_count)))
            self.ui.ReportTable.setItem(row, 2, QTableWidgetItem(str(churned_count)))

        self.ui.ReportTable.horizontalHeader().setStretchLastSection(True)
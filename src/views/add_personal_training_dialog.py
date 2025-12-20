from PyQt6.QtWidgets import QDialog, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from datetime import date, time

from src.ui.add_personal_training_dialog import Ui_AddPersonalTrainingDialog
from src.models.personal_trainings import (
    personal_training_create,
    personal_training_get_by_trainer_and_date,
    personal_training_get_by_id,
    personal_training_update,
    personal_training_delete
)

from src.models.trainers import trainer_get_all


class AddPersonalTrainingDialog(QDialog):
    def __init__(self, client: dict, parent=None):
        super().__init__(parent)
        self.ui = Ui_AddPersonalTrainingDialog()
        self.ui.setupUi(self)

        self.client = client  # dict
        self.trainers = trainer_get_all(only_personal=True)
        self.current_training_id = None

        self.setup_interface()
        self.setup_signals()
        self.load_default_date()


    def setup_interface(self):
        full_name = f"{self.client['last_name']} {self.client['first_name']} {self.client.get('middle_name', '')}".strip()
        self.ui.Client.setText(full_name)

        self.ui.TrainerComboBox.clear()
        for t in self.trainers:
            self.ui.TrainerComboBox.addItem(
                f"{t['last_name']} {t['first_name']}",
                t
            )

        self.update_price_from_trainer()
        self.update_free_time_list()

    def setup_signals(self):
        # При смене тренера обновляем и список времени, и стоимость
        self.ui.TrainerComboBox.currentIndexChanged.connect(self.update_free_time_list)
        self.ui.TrainerComboBox.currentIndexChanged.connect(self.update_price_from_trainer)

        # Следим за изменением даты для обновления свободного времени
        self.ui.DayPersonalTrainingEdit.textChanged.connect(self.update_free_time_list)
        self.ui.MonthPersonalTrainingEdit.textChanged.connect(self.update_free_time_list)
        self.ui.YearPersonalTrainingEdit.textChanged.connect(self.update_free_time_list)

        self.ui.SavePersonalTrainingBtn.clicked.connect(self.save_training)
        self.ui.DeletePersonalTrainingBtn.clicked.connect(self.delete_training)

    # ---------------- helpers ----------------
    def get_selected_trainer_id(self):
        data = self.ui.TrainerComboBox.currentData()
        if isinstance(data, dict):
            return data.get('trainer_id')
        return data

    def get_training_date(self):
        try:
            day = int(self.ui.DayPersonalTrainingEdit.text())
            month = int(self.ui.MonthPersonalTrainingEdit.text())
            year = int(self.ui.YearPersonalTrainingEdit.text())
            return date(year, month, day)
        except Exception:
            return None

    # ---------------- free time ----------------
    def update_free_time_list(self):
        self.ui.FreeTimelistWidget.clear()
        trainer_id = self.get_selected_trainer_id()
        training_date = self.get_training_date()
        if not trainer_id or not training_date:
            return

        booked_times = personal_training_get_by_trainer_and_date(trainer_id, training_date)
        all_times = [f"{h:02d}:00" for h in range(9, 21)]

        for t in all_times:
            is_booked = False
            for bt in booked_times:
                st = bt['start_time']
                if isinstance(st, time):
                    st_time = st.strftime("%H:%M")
                else:  # timedelta
                    total_seconds = st.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    st_time = time(hours, minutes).strftime("%H:%M")
                if st_time == t:
                    is_booked = True
                    break
            if not is_booked:
                self.ui.FreeTimelistWidget.addItem(QListWidgetItem(t))

    # ---------------- default date ----------------
    def load_default_date(self):
        today = date.today()
        self.ui.DayPersonalTrainingEdit.setText(str(today.day))
        self.ui.MonthPersonalTrainingEdit.setText(str(today.month))
        self.ui.YearPersonalTrainingEdit.setText(str(today.year))

    # ---------------- load existing ----------------
    def load_existing_training(self, training_id):
        self.current_training_id = training_id
        training = personal_training_get_by_id(training_id)
        if not training:
            QMessageBox.warning(self, "Ошибка", "Тренировка не найдена")
            return

        trainer_id = training['trainer_id']
        idx = self.ui.TrainerComboBox.findData(trainer_id)
        if idx >= 0:
            self.ui.TrainerComboBox.setCurrentIndex(idx)

        t_date = training['training_date']
        if hasattr(t_date, "date"):
            t_date = t_date.date()
        self.ui.DayPersonalTrainingEdit.setText(str(t_date.day))
        self.ui.MonthPersonalTrainingEdit.setText(str(t_date.month))
        self.ui.YearPersonalTrainingEdit.setText(str(t_date.year))

        self.update_free_time_list()
        start_time = training['start_time']
        if isinstance(start_time, time):
            start_time_str = start_time.strftime("%H:%M")
        else:
            total_seconds = start_time.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            start_time_str = time(hours, minutes).strftime("%H:%M")

        items = self.ui.FreeTimelistWidget.findItems(start_time_str, Qt.MatchFlag.MatchExactly)
        if items:
            self.ui.FreeTimelistWidget.setCurrentItem(items[0])

        self.ui.PricePersonalTrainingEdit.setText(str(training.get('price') or ""))
        self.ui.DeletePersonalTrainingBtn.setVisible(True)

    def update_price_from_trainer(self):
        """Обновляет поле цены ставкой выбранного тренера из его типа"""
        trainer_data = self.ui.TrainerComboBox.currentData()
        if trainer_data and 'rate' in trainer_data:
            try:
                price_val = int(float(trainer_data['rate']))
                self.ui.PricePersonalTrainingEdit.setText(str(price_val))
            except (ValueError, TypeError):
                self.ui.PricePersonalTrainingEdit.clear()
        else:
            self.ui.PricePersonalTrainingEdit.clear()

    # ---------------- validation ----------------
    def validate_form(self):
        if not self.get_selected_trainer_id():
            QMessageBox.warning(self, "Ошибка", "Выберите тренера!")
            return False

        t_date = self.get_training_date()
        # Разрешаем запись на сегодня и будущее (убрали запрет на текущий день)
        if not t_date or t_date < date.today():
            QMessageBox.warning(self, "Ошибка", "Выберите корректную дату!")
            return False

        if not self.ui.FreeTimelistWidget.selectedItems():
            QMessageBox.warning(self, "Ошибка", "Выберите время!")
            return False

        # Улучшенная валидация цены (поддерживает 1000.00)
        price_text = self.ui.PricePersonalTrainingEdit.text().strip()
        try:
            price_val = float(price_text)
            if price_val <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "У тренера не указана корректная стоимость!")
            return False

        return True

    # ---------------- save ----------------
    def save_training(self):
        if not self.validate_form():
            return

        trainer_id = self.get_selected_trainer_id()
        t_date = self.get_training_date()
        start_time_str = self.ui.FreeTimelistWidget.selectedItems()[0].text()
        start_time = time(int(start_time_str.split(":")[0]), int(start_time_str.split(":")[1]))

        # Финальная конвертация перед сохранением в БД
        price = int(float(self.ui.PricePersonalTrainingEdit.text().strip()))

        if self.current_training_id:
            personal_training_update(
                self.current_training_id,
                self.client['client_id'],
                trainer_id,
                t_date,
                start_time,
                price
            )
        else:
            personal_training_create(
                client_id=self.client['client_id'],
                trainer_id=trainer_id,
                training_date=t_date,
                start_time=start_time,
                price=price
            )
        self.accept()

    # ---------------- delete ----------------
    def delete_training(self):
        if not self.current_training_id:
            return
        reply = QMessageBox.question(
            self,
            "Удаление",
            "Удалить тренировку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            personal_training_delete(self.current_training_id)
            self.accept()

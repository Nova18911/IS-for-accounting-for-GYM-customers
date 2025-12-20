# src/views/add_group_training_dialog.py
from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from datetime import datetime, date, time, timedelta

from src.ui.add_group_training_dialog import Ui_AddGroupTrainingDialog
from src.models.group_trainings import GroupTraining
from src.models.group_attendances import (
    group_attendance_create,
    group_attendance_get_count_by_training,
    group_attendance_check_client_on_training,
    group_attendance_get_by_id,
    group_attendance_delete
)


class AddGroupTrainingDialog(QDialog):
    """Диалог для записи клиента на групповую тренировку."""

    def __init__(self, client: dict, parent=None):
        super().__init__(parent)

        self.ui = Ui_AddGroupTrainingDialog()
        self.ui.setupUi(self)

        self.client = client
        self.current_training = None
        self.matching_trainings = []  # Список тренировок в выбранном слоте

        self.time_slots = [
            "07:00", "08:00", "09:00", "10:00", "11:00",
            "13:00", "14:00", "15:00", "16:00", "18:00", "19:00"
        ]

        self.current_week_start = self._get_monday_of_week(date.today())

        # ---- connections ----
        self.ui.ScheduleTable.cellClicked.connect(self.on_cell_clicked)
        self.ui.AddGroupTrainingBtn.clicked.connect(self.save_attendance)

        # НОВОЕ: Обработка смены тренировки в комбобоксе
        self.ui.GroupTrainingComboBox.currentIndexChanged.connect(self.on_training_combo_changed)

        self.attendance_id = None  # Добавляем для отслеживания режима редактирования

        # Подключаем кнопку удаления
        self.ui.DeleteGroupTrainingBtn.clicked.connect(self.delete_attendance)

        self.ui.LeftButton_2.clicked.connect(self.previous_week)
        self.ui.RightButton_2.clicked.connect(self.next_week)

        # клиент
        full_name = f"{self.client['last_name']} {self.client['first_name']} {self.client.get('middle_name', '')}".strip()
        self.ui.ClientE.setText(full_name)

        self.update_week_label()
        self.load_schedule()

    # ---------------- utilities ----------------

    def _get_monday_of_week(self, input_date):
        return input_date - timedelta(days=input_date.weekday())

    def get_week_dates(self):
        return [self.current_week_start + timedelta(days=i) for i in range(7)]

    def get_time_index(self, time_obj):
        t_str = None

        if isinstance(time_obj, str):
            try:
                t = datetime.strptime(time_obj, "%H:%M:%S").time()
            except ValueError:
                t = datetime.strptime(time_obj, "%H:%M").time()
            t_str = t.strftime("%H:%M")

        elif isinstance(time_obj, time):
            t_str = time_obj.strftime("%H:%M")

        elif isinstance(time_obj, timedelta):
            total_seconds = int(time_obj.total_seconds())
            hh = total_seconds // 3600
            mm = (total_seconds % 3600) // 60
            t_str = f"{hh:02}:{mm:02}"

        else:
            t_str = str(time_obj)[:5]

        return self.time_slots.index(t_str) if t_str in self.time_slots else -1

    # ---------------- week navigation ----------------

    def update_week_label(self):
        week = self.get_week_dates()
        start, end = week[0], week[-1]

        months = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]

        if start.month == end.month:
            text = f"{start.day}-{end.day} {months[start.month - 1]} {start.year} г."
        else:
            text = (
                f"{start.day} {months[start.month - 1]} – "
                f"{end.day} {months[end.month - 1]} {start.year} г."
            )

        self.ui.DateL_3.setText(text)

    def on_training_combo_changed(self, index):
        if index < 0:
            return

        # Получаем объект тренировки из данных выбранного пункта
        selected_tr = self.ui.GroupTrainingComboBox.itemData(index)
        if selected_tr:
            self.current_training = selected_tr
            self.update_training_info()

    def previous_week(self):
        self.current_week_start -= timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    def next_week(self):
        self.current_week_start += timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    # ---------------- schedule ----------------

    def clear_table(self):
        for r in range(self.ui.ScheduleTable.rowCount()):
            for c in range(self.ui.ScheduleTable.columnCount()):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.ui.ScheduleTable.setItem(r, c, item)

    def load_schedule(self):
        self.clear_table()

        week = self.get_week_dates()
        start_date, end_date = week[0], week[-1]

        trainings = GroupTraining.get_all_in_week(start_date, end_date)

        for tr in trainings:
            if not tr.training_date:
                continue

            day_idx = (tr.training_date - start_date).days
            if not 0 <= day_idx <= 6:
                continue

            time_idx = self.get_time_index(tr.start_time)
            if time_idx < 0:
                continue

            text = f"{tr.service_name or 'Не указано'}\n({tr.trainer_name or 'Тренер не указан'})"
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.ui.ScheduleTable.setItem(time_idx, day_idx, item)

    def format_time_to_slot(self, t):
        """Возвращает строку 'HH:MM' для сравнения с time_slots."""
        if isinstance(t, str):
            try:
                dt = datetime.strptime(t, "%H:%M:%S").time()
            except ValueError:
                dt = datetime.strptime(t, "%H:%M").time()
            return dt.strftime("%H:%M")
        elif isinstance(t, time):
            return t.strftime("%H:%M")
        elif isinstance(t, timedelta):
            total_seconds = int(t.total_seconds())
            hh = total_seconds // 3600
            mm = (total_seconds % 3600) // 60
            return f"{hh:02}:{mm:02}"
        return str(t)[:5]


    def on_cell_clicked(self, row, column):
        week = self.get_week_dates()
        selected_date = week[column]
        time_str = self.time_slots[row]

        # Получаем все тренировки на этот день
        trainings = GroupTraining.get_all_in_week(selected_date, selected_date)
        # Фильтруем те, что попадают в выбранное время
        self.matching_trainings = [t for t in trainings if self.format_time_to_slot(t.start_time) == time_str]

        if not self.matching_trainings:
            QMessageBox.warning(self, "Ошибка", "В этом слоте нет тренировок")
            self.current_training = None
            self.ui.GroupTrainingComboBox.clear()
            self.clear_training_info()
            return

        # Заполняем ComboBox списком найденных тренировок
        self.ui.GroupTrainingComboBox.blockSignals(True) # Блокируем, чтобы не вызывать on_training_combo_changed раньше времени
        self.ui.GroupTrainingComboBox.clear()
        for tr in self.matching_trainings:
            # Отображаем название услуги и тренера в выпадающем списке
            display_text = f"{tr.service_name} ({tr.trainer_name})"
            self.ui.GroupTrainingComboBox.addItem(display_text, tr)
        self.ui.GroupTrainingComboBox.blockSignals(False)

        # По умолчанию выбираем первую
        self.current_training = self.matching_trainings[0]
        self.ui.GroupTrainingComboBox.setCurrentIndex(0)
        self.update_training_info()

    def load_existing_attendance(self, attendance_id):
        """Загрузка данных при редактировании записи"""
        self.attendance_id = attendance_id
        attendance = group_attendance_get_by_id(attendance_id)
        if not attendance:
            return

        # Находим саму тренировку
        target_training_id = attendance['group_training_id']
        tr = GroupTraining.get_by_id(target_training_id)
        if not tr:
            return

        # Переключаем календарь на неделю этой тренировки
        self.current_week_start = self._get_monday_of_week(tr.training_date)
        self.update_week_label()
        self.load_schedule()

        # Эмулируем клик по ячейке, чтобы заполнить ComboBox и поля
        row = self.get_time_index(tr.start_time)
        col = tr.training_date.weekday()
        self.on_cell_clicked(row, col)

        # Выбираем именно эту тренировку в ComboBox (если в слоте их несколько)
        for i in range(self.ui.GroupTrainingComboBox.count()):
            item_tr = self.ui.GroupTrainingComboBox.itemData(i)
            if item_tr and item_tr.group_training_id == target_training_id:
                self.ui.GroupTrainingComboBox.setCurrentIndex(i)
                break

        # Настраиваем UI для режима редактирования
        self.ui.AddGroupTrainingBtn.setText("Обновить")
        self.ui.DeleteGroupTrainingBtn.setVisible(True)
        self.setWindowTitle("Редактирование записи")

    def clear_training_info(self):
        self.ui.DayE.clear()
        self.ui.MonthE.clear()
        self.ui.YearE.clear()
        self.ui.TimeE.clear()
        self.ui.HallE.clear()
        self.ui.MaxE.clear()
        self.ui.TrainerE.clear()

    # ---------------- info panel ----------------

    def update_training_info(self):
        tr = self.current_training
        if not tr:
            return

        td = tr.training_date

        self.ui.DayE.setText(str(td.day))
        self.ui.MonthE.setText(str(td.month))
        self.ui.YearE.setText(str(td.year))

        self.ui.TimeE.setText(
            tr.start_time.strftime("%H:%M")
            if isinstance(tr.start_time, time)
            else str(tr.start_time)[:5]
        )

        self.ui.HallE.setText(tr.hall_name or "")
        self.ui.MaxE.setText(str(tr.capacity) if tr.capacity else "")
        self.ui.TrainerE.setText(tr.trainer_name or "")

    # ---------------- save attendance ----------------

    def save_attendance(self):
        if not self.current_training:
            QMessageBox.warning(self, "Ошибка", "Выберите тренировку")
            return

        tr = self.current_training

        # ------------------ запрет записи на сегодня и в прошлое ------------------
        if tr.training_date <= date.today() + timedelta(days=1):
            QMessageBox.warning(self, "Ошибка", "Нельзя записываться на тренировку в этот день или в прошлое!")
            return
        # -------------------------------------------------------------------------

        if group_attendance_check_client_on_training(
                tr.group_training_id, self.client["client_id"]
        ):
            QMessageBox.warning(self, "Ошибка", "Вы уже записаны на эту тренировку")
            return

        current_count = group_attendance_get_count_by_training(tr.group_training_id)
        if current_count >= (tr.capacity or 0):
            QMessageBox.warning(
                self, "Ошибка", "Превышена максимальная вместимость тренировки!"
            )
            return

        group_attendance_create(tr.group_training_id, self.client["client_id"])

        QMessageBox.information(self, "Успех", "Вы успешно записаны на тренировку")
        self.accept()

        if self.attendance_id:
            group_attendance_delete(self.attendance_id)

            # Создаем новую запись (или перезаписываем)
        group_attendance_create(tr.group_training_id, self.client["client_id"])
        QMessageBox.information(self, "Успех", "Запись обновлена" if self.attendance_id else "Клиент записан")
        self.accept()

    def delete_attendance(self):
        """Удаление записи о посещении"""
        if not self.attendance_id:
            return

        reply = QMessageBox.question(
            self, "Удаление", "Отменить запись клиента на эту тренировку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if group_attendance_delete(self.attendance_id):
                QMessageBox.information(self, "Успех", "Запись отменена")
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить запись")
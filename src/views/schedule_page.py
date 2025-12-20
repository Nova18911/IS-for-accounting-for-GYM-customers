from PyQt6.QtWidgets import (
    QTableWidgetItem, QMessageBox, QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt
from src.models.group_trainings import GroupTraining
from src.models.services import Service
import src.models.trainers as trainer_model
import src.models.trainer_types as trainer_types_model
from src.models.halls import Hall
from datetime import datetime, timedelta, date, time

from src.views.schedule_cell_dialog import ScheduleCellDialog


class SchedulePageController:
    """Контроллер для страницы расписания групповых тренировок."""

    def __init__(self, ui, user_id=None, user_email=None, user_role=None):
        self.ui = ui
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        self.hall_colors = self._create_hall_colors()
        self.current_week_start = self._get_monday_of_week(date.today())
        self.time_slots = [
            "07:00", "08:00", "09:00", "10:00", "11:00",
            "13:00", "14:00", "15:00", "16:00", "18:00", "19:00"
        ]
        self.current_training = None

        # Настройка таблицы и формы
        self._setup_interface()
        self.load_services()
        self.load_group_trainers()
        self.update_week_label()
        self.load_schedule()
        self.connect_buttons()
        self.reset_form()
        self.ui.widget_schedule.setVisible(False)

    # ---------------------------
    # Utilities
    # ---------------------------
    def _create_hall_colors(self):
        return {
            1: "#FFB6C1", 2: "#87CEFA", 3: "#98FB98", 4: "#DDA0DD",
            5: "#FFD700", 6: "#F0E68C", 7: "#ADD8E6", 8: "#90EE90"
        }

    def _get_monday_of_week(self, input_date):
        return input_date - timedelta(days=input_date.weekday())

    def get_week_dates(self):
        return [self.current_week_start + timedelta(days=i) for i in range(7)]

    def get_time_index(self, time_obj):
        """
        Возвращает индекс времени в self.time_slots.
        Поддерживаются: str ("HH:MM" или "HH:MM:SS"), datetime.time, datetime.timedelta
        """
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

    # ---------------------------
    # UI setup / loading
    # ---------------------------
    def _setup_interface(self):
        self.ui.ScheduleTable.horizontalHeader().setDefaultSectionSize(110)
        self.ui.ScheduleTable.verticalHeader().setDefaultSectionSize(40)
        self.ui.ScheduleTable.setEditTriggers(self.ui.ScheduleTable.EditTrigger.NoEditTriggers)
        self.ui.ScheduleTable.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def load_services(self):
        self.ui.ServiceComboBox.clear()
        self.ui.ServiceComboBox.addItem("Выберите тренировку", None)
        for s in Service.get_all() or []:
            self.ui.ServiceComboBox.addItem(s.service_name, s.service_id)

    def load_group_trainers(self):
        self.ui.TrainerComboBox.clear()
        self.ui.TrainerComboBox.addItem("Выберите тренера", None)
        trainers = trainer_model.trainer_get_all() or []
        for tr in trainers:
            trainer_type_id = tr.get('trainer_type_id')
            if trainer_type_id:
                tt = trainer_types_model.trainer_type_get_by_id(trainer_type_id)
                if tt and tt.get('trainer_type_name') == "Персональный тренер":
                    continue
            name = f"{tr.get('last_name', '')} {tr.get('first_name', '')}"
            if tr.get('middle_name'):
                name += f" {tr.get('middle_name')}"
            self.ui.TrainerComboBox.addItem(name, tr.get('trainer_id'))

    def update_week_label(self):
        week = self.get_week_dates()
        start, end = week[0], week[-1]
        months = ["января","февраля","марта","апреля","мая","июня","июля",
                  "августа","сентября","октября","ноября","декабря"]
        if start.month == end.month:
            text = f"{start.day}-{end.day} {months[start.month-1]} {start.year} г."
        else:
            text = f"{start.day} {months[start.month-1]} - {end.day} {months[end.month-1]} {start.year} г."
        self.ui.DateL.setText(text)

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

        # Словарь для группировки тренировок по (row, col)
        cells_data = {}

        for tr in trainings:
            day_idx = (tr.training_date - start_date).days
            if day_idx < 0 or day_idx > 6: continue

            time_idx = self.get_time_index(tr.start_time)
            if time_idx < 0: continue

            key = (time_idx, day_idx)
            if key not in cells_data:
                cells_data[key] = []
            cells_data[key].append(tr)

        for (r, c), tr_list in cells_data.items():
            count = len(tr_list)
            if count == 1:
                tr = tr_list[0]
                text = f"{tr.service_name}\n({tr.trainer_name})"
                color = self.get_hall_color(tr.hall_id)
            else:
                # Если тренировок несколько, пишем количество
                text = f"Занято слотов: {count}\n(Кликните для выбора)"
                color = "#E0E0E0"  # Нейтральный цвет для группы

            new_item = QTableWidgetItem(text)
            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            new_item.setBackground(self._qcolor_from_hex(color))
            new_item.setToolTip("\n---\n".join([f"{t.service_name} ({t.hall_name})" for t in tr_list]))
            self.ui.ScheduleTable.setItem(r, c, new_item)

    def get_hall_color(self, hall_id):
        return self.hall_colors.get(hall_id, "#FFFFFF")

    def _qcolor_from_hex(self, hexcolor):
        from PyQt6.QtGui import QColor
        return QColor(hexcolor)

    # ---------------------------
    # Cell double click / dialogs
    # ---------------------------
    def on_cell_double_clicked(self, row, column):
        week = self.get_week_dates()
        selected_date = week[column]
        time_slot = self.time_slots[row]

        dlg = ScheduleCellDialog(
            self.ui.centralwidget,
            selected_date,
            time_slot
        )

        if dlg.exec():
            if dlg.selected_training:
                self.edit_training(dlg.selected_training)
            else:
                self.create_new_training(row, column)



    # ---------------------------
    # Form panel
    # ---------------------------
    def show_edit_panel(self):
        self.ui.widget_schedule.setVisible(True)

    def reset_form(self):
        self.current_training = None
        self.ui.DayEdit.clear()
        self.ui.MonthEdit.clear()
        self.ui.YearEdit.clear()
        self.ui.TimeEdit.clear()
        self.ui.ServiceComboBox.setCurrentIndex(0)
        self.ui.TrainerComboBox.setCurrentIndex(0)
        self.ui.HallE.clear()
        self.ui.MaxE.clear()
        self.ui.SaveGroupTrainingBtn.setText("Сохранить")
        self.ui.DeleteGroupTrainingBtn.setEnabled(False)
        self.ui.GroupTrainingL.setText("Групповая тренировка")

    def create_new_training(self, row, column):
        week = self.get_week_dates()
        sel_date = week[column]

        # Запрет создания тренировок в прошлом
        if sel_date < date.today():
            QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Нельзя создать тренировку в прошлом!")
            return

        self.reset_form()
        self.ui.DayEdit.setText(str(sel_date.day))
        self.ui.MonthEdit.setText(str(sel_date.month))
        self.ui.YearEdit.setText(str(sel_date.year))
        self.ui.TimeEdit.setText(self.time_slots[row])
        self.show_edit_panel()
        self.ui.GroupTrainingL.setText("Новая групповая тренировка")

    def edit_training(self, training):
        self.current_training = training
        if training.training_date:
            td = training.training_date
            if isinstance(td, str):
                td = datetime.strptime(td, "%Y-%m-%d").date()
            self.ui.DayEdit.setText(str(td.day))
            self.ui.MonthEdit.setText(str(td.month))
            self.ui.YearEdit.setText(str(td.year))
        if training.start_time:
            try:
                time_str = training.start_time.strftime("%H:%M")
            except Exception:
                time_str = str(training.start_time)[:5]
            self.ui.TimeEdit.setText(time_str)
        if training.service_id:
            idx = self.ui.ServiceComboBox.findData(training.service_id)
            if idx >= 0:
                self.ui.ServiceComboBox.setCurrentIndex(idx)
        if training.trainer_id:
            idx = self.ui.TrainerComboBox.findData(training.trainer_id)
            if idx >= 0:
                self.ui.TrainerComboBox.setCurrentIndex(idx)
        self.show_edit_panel()
        self.ui.SaveGroupTrainingBtn.setText("Обновить")
        self.ui.DeleteGroupTrainingBtn.setEnabled(True)
        self.ui.GroupTrainingL.setText("Редактирование тренировки")


    def save_training(self):
        # 1. Сбор данных из полей ввода
        day = self.ui.DayEdit.text().strip()
        month = self.ui.MonthEdit.text().strip()
        year = self.ui.YearEdit.text().strip()
        time_str = self.ui.TimeEdit.text().strip()
        service_id = self.ui.ServiceComboBox.currentData()
        trainer_id = self.ui.TrainerComboBox.currentData()

        if not (day and month and year and time_str):
            QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Введите дату и время!")
            return

        if not service_id:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Выберите тип тренировки!")
            return

        if not trainer_id:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Выберите тренера!")
            return

        try:
            training_date = date(int(year), int(month), int(day))

            # Приведение времени к формату HH:MM:SS для парсинга
            if len(time_str) == 5:
                time_str_full = time_str + ":00"
            else:
                time_str_full = time_str
            start_time = datetime.strptime(time_str_full, "%H:%M:%S").time()
        except ValueError:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Некорректный формат даты или времени!")
            return


        exclude_id = self.current_training.group_training_id if self.current_training else None


        trainer_busy = not GroupTraining.check_trainer_availability(
            trainer_id, training_date, start_time, exclude_id
        )


        service_exists = GroupTraining.check_service_existence(
            service_id, training_date, start_time, exclude_id
        )


        if trainer_busy and service_exists:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка",
                                "Такая тренировка уже существует (совпадает и тренер, и тип занятия)!")
            return
        elif trainer_busy:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка",
                                "Тренер уже занят в это время!")
            return
        elif service_exists:
            QMessageBox.warning(self.ui.centralwidget, "Ошибка",
                                "Вы уже добавляли в это время эту тренировку!")
            return

        service_obj = Service.get_by_id(service_id)
        if service_obj and service_obj.hall_id:
            hall_available = GroupTraining.check_hall_availability(
                service_obj.hall_id, training_date, start_time, exclude_id
            )
            if not hall_available:
                QMessageBox.warning(self.ui.centralwidget, "Ошибка",
                                    "Зал, в котором проводится эта тренировка, уже занят!")
                return


        try:
            if self.current_training:
                self.current_training.training_date = training_date
                self.current_training.start_time = start_time
                self.current_training.service_id = service_id
                self.current_training.trainer_id = trainer_id
                success = self.current_training.save()
            else:
                new_tr = GroupTraining(
                    training_date=training_date,
                    start_time=start_time,
                    trainer_id=trainer_id,
                    service_id=service_id
                )
                success = new_tr.save()

            if success:
                QMessageBox.information(self.ui.centralwidget, "Успех", "Расписание успешно обновлено")
                self.load_schedule()
                self.reset_form()
                self.ui.widget_schedule.setVisible(False)
            else:
                QMessageBox.critical(self.ui.centralwidget, "Ошибка", "Не удалось сохранить данные в БД")

        except Exception as e:
            QMessageBox.critical(self.ui.centralwidget, "Критическая ошибка", f"Произошел сбой при сохранении: {e}")

    def delete_training(self):
        if not self.current_training:
            QMessageBox.warning(self.ui, "Ошибка", "Нет выбранной тренировки")
            return
        reply = QMessageBox.question(self.ui, "Подтверждение", "Удалить тренировку?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok = self.current_training.delete()
        if ok:
            QMessageBox.information(self.ui, "Успех", "Удалено")
        else:
            QMessageBox.critical(self.ui, "Ошибка", "Не удалось удалить")
        self.load_schedule()
        self.reset_form()

    # ---------------------------
    # Buttons
    # ---------------------------
    def connect_buttons(self):
        self.ui.LeftButton.clicked.connect(self.previous_week)
        self.ui.RightButton.clicked.connect(self.next_week)
        self.ui.SaveGroupTrainingBtn.clicked.connect(self.save_training)
        self.ui.DeleteGroupTrainingBtn.clicked.connect(self.delete_training)
        self.ui.ServiceComboBox.currentIndexChanged.connect(self.on_service_changed)

    def previous_week(self):
        self.current_week_start -= timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    def next_week(self):
        self.current_week_start += timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    def on_service_changed(self, index):
        if index <= 0:
            self.ui.HallE.clear()
            self.ui.MaxE.clear()
            self.ui.HallE.setStyleSheet("")
            return
        service_id = self.ui.ServiceComboBox.currentData()
        service = Service.get_by_id(service_id)
        hall = Hall.get_by_id(service.hall_id) if service and service.hall_id else None
        if hall:
            self.ui.HallE.setText(hall.hall_name)
            self.ui.MaxE.setText(str(hall.capacity))
            color = self.get_hall_color(hall.hall_id)
            self.ui.HallE.setStyleSheet(f"background-color: {color}; padding: 2px; border: 1px solid #000;")
        else:
            self.ui.HallE.clear()
            self.ui.MaxE.clear()
            self.ui.HallE.setStyleSheet("")

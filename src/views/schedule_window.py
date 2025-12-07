# views/schedule_window.py
import sys
from datetime import datetime, timedelta, date
from PyQt6.QtWidgets import (QMainWindow, QTableWidgetItem, QMessageBox,
                             QApplication, QComboBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from src.ui.schedule_window import Ui_ScheduleForm
from src.models.group_trainings import GroupTraining
from src.models.services import Service
from src.models.trainers import Trainer
from src.models.trainer_types import TrainerType
from src.models.halls import Hall



class ScheduleWindow(QMainWindow):
    """Окно управления расписанием групповых тренировок"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_ScheduleForm()
        self.ui.setupUi(self)

        # Данные пользователя
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Текущая редактируемая тренировка
        self.current_training = None

        # Словарь цветов для залов (из service_window)
        self.hall_colors = self.create_hall_colors()

        # Текущая отображаемая неделя (начало недели - понедельник)
        self.current_week_start = self.get_monday_of_week(date.today())

        # Временные интервалы для таблицы (из вертикальных заголовков)
        self.time_slots = [
            "7:00", "8:00", "9:00", "10:00", "11:00",
            "13:00", "14:00", "15:00", "16:00", "18:00", "19:00"
        ]

        # Устанавливаем заголовок окна
        self.setWindowTitle("Фитнес-Менеджер - Расписание групповых тренировок")

        # Настраиваем интерфейс
        self.setup_interface()

        # Загружаем данные
        self.load_services()  # Загружаем услуги в ComboBox
        self.load_group_trainers()  # Загружаем тренеров для групповых тренировок
        self.load_schedule()  # Загружаем расписание

        # Подключаем кнопки
        self.connect_buttons()

        # Скрываем правую панель при запуске
        self.hide_edit_panel()

        # Сбрасываем форму добавления/редактирования
        self.reset_form()

        # Обновляем дату недели
        self.update_week_label()

        # Делаем кнопку "Расписание" неактивной
        self.ui.ScheduleBtn.setEnabled(False)

    def create_hall_colors(self):
        """Создание словаря цветов для залов"""
        return {
            1: "#FFB6C1",  # Light Pink
            2: "#87CEFA",  # Light Sky Blue
            3: "#98FB98",  # Pale Green
            4: "#DDA0DD",  # Plum
            5: "#FFD700",  # Gold
            6: "#F0E68C",  # Khaki
            7: "#ADD8E6",  # Light Blue
            8: "#90EE90",  # Light Green
            9: "#FFA07A",  # Light Salmon
            10: "#20B2AA",  # Light Sea Green
            11: "#B0C4DE",  # Light Steel Blue
            12: "#FFDEAD",  # Navajo White
            13: "#AFEEEE",  # Pale Turquoise
            14: "#E6E6FA",  # Lavender
            15: "#FFF0F5",  # Lavender Blush
            16: "#F5FFFA",  # Mint Cream
            17: "#FFFACD",  # Lemon Chiffon
            18: "#FAFAD2",  # Light Goldenrod Yellow
            19: "#F0FFF0",  # Honeydew
            20: "#F5F5DC",  # Beige
        }

    def get_monday_of_week(self, input_date):
        """Получить понедельник недели для указанной даты"""
        # weekday() возвращает: 0-понедельник, 6-воскресенье
        return input_date - timedelta(days=input_date.weekday())

    def get_week_dates(self):
        """Получить список дат текущей недели (с понедельника по воскресенье)"""
        week_dates = []
        for i in range(7):
            current_date = self.current_week_start + timedelta(days=i)
            week_dates.append(current_date)
        return week_dates

    def setup_interface(self):
        """Настройка интерфейса"""
        # Настраиваем таблицу
        self.ui.ScheduleTable.horizontalHeader().setDefaultSectionSize(110)

        # Устанавливаем ширину вертикальных заголовков
        self.ui.ScheduleTable.verticalHeader().setDefaultSectionSize(40)

        # Отключаем редактирование ячеек напрямую
        self.ui.ScheduleTable.setEditTriggers(
            self.ui.ScheduleTable.EditTrigger.NoEditTriggers
        )

        # Подключаем клик по таблице
        self.ui.ScheduleTable.cellClicked.connect(self.on_table_cell_clicked)

    def show_edit_panel(self):
        """Показать правую панель для добавления/редактирования"""
        self.ui.widget.setVisible(True)

    def hide_edit_panel(self):
        """Скрыть правую панель для добавления/редактирования"""
        self.ui.widget.setVisible(False)

    def load_services(self):
        """Загрузка услуг (групповых тренировок) в ComboBox"""
        try:
            self.ui.ServiceComboBox.clear()
            self.ui.ServiceComboBox.addItem("Выберите тренировку", None)

            # Используем модель Service для получения данных
            # В реальном приложении можно фильтровать только групповые услуги
            services = Service.get_all()

            if services:
                for service in services:
                    self.ui.ServiceComboBox.addItem(
                        service.service_name,
                        service.service_id
                    )

        except Exception as e:
            print(f"Ошибка загрузки услуг: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список услуг: {str(e)}")

    def load_group_trainers(self):
        """Загрузка тренеров для групповых тренировок"""
        try:
            self.ui.TrainercomboBox.clear()
            self.ui.TrainercomboBox.addItem("Выберите тренера", None)

            # Получаем всех тренеров
            trainers = Trainer.get_all()

            # Фильтруем: только групповые и общие тренеры (исключаем персональных)
            if trainers:
                for trainer in trainers:
                    # Проверяем тип тренера через модель TrainerType
                    if hasattr(trainer, 'trainer_type_id') and trainer.trainer_type_id:
                        trainer_type = TrainerType.get_by_id(trainer.trainer_type_id)
                        if trainer_type:
                            # Персональный тренер = 3 (по данным SQL)
                            if trainer_type.trainer_type_name != "Персональный тренер":
                                full_name = f"{trainer.last_name} {trainer.first_name}"
                                if trainer.middle_name:
                                    full_name += f" {trainer.middle_name}"
                                self.ui.TrainercomboBox.addItem(
                                    full_name,
                                    trainer.trainer_id
                                )

        except Exception as e:
            print(f"Ошибка загрузки тренеров: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список тренеров: {str(e)}")

    def load_schedule(self):
        """Загрузка расписания на текущую неделю"""
        try:
            # Очищаем таблицу
            for row in range(self.ui.ScheduleTable.rowCount()):
                for col in range(self.ui.ScheduleTable.columnCount()):
                    self.ui.ScheduleTable.setItem(row, col, QTableWidgetItem(""))

            # Получаем даты недели
            week_dates = self.get_week_dates()
            start_date = week_dates[0]  # Понедельник
            end_date = week_dates[6]  # Воскресенье

            # Используем модель GroupTraining для получения данных
            trainings = GroupTraining.get_all_in_week(start_date, end_date)

            # Группируем тренировки по дате и времени
            schedule_dict = {}
            for training in trainings:
                key = (training.training_date, str(training.start_time))
                if key not in schedule_dict:
                    schedule_dict[key] = []
                schedule_dict[key].append(training)

            # Заполняем таблицу
            for time_slot in self.time_slots:
                for day_idx, week_date in enumerate(week_dates):
                    # Ищем тренировки для этого времени и дня
                    trainings_for_slot = []
                    for training_time, training_date in schedule_dict:
                        if str(training_date) == str(week_date):
                            # Сравниваем время (без секунд)
                            time_obj = datetime.strptime(str(training_time), "%H:%M:%S")
                            display_time = time_obj.strftime("%H:%M")
                            if display_time == time_slot:
                                trainings_for_slot.extend(schedule_dict[(training_date, training_time)])

                    if trainings_for_slot:
                        # Создаем текст для ячейки
                        cell_text = ""
                        for training in trainings_for_slot:
                            if hasattr(training, 'service_name'):
                                cell_text += f"• {training.service_name}\n"

                        item = QTableWidgetItem(cell_text.strip())

                        # Устанавливаем цвет в зависимости от зала (если есть информация)
                        if hasattr(trainings_for_slot[0], 'service_id'):
                            # Можно добавить логику для определения цвета по залу
                            pass

                        item.setData(Qt.ItemDataRole.UserRole, trainings_for_slot)
                        self.ui.ScheduleTable.setItem(
                            self.time_slots.index(time_slot),
                            day_idx,
                            item
                        )

        except Exception as e:
            print(f"Ошибка загрузки расписания: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить расписание: {str(e)}")

    def connect_buttons(self):
        """Подключение обработчиков кнопок"""
        # Кнопки навигации по неделям
        self.ui.LeftButton.clicked.connect(self.previous_week)
        self.ui.RightButton.clicked.connect(self.next_week)

        # Кнопки формы
        self.ui.SaveGroupTrainingBtn.clicked.connect(self.save_training)
        self.ui.DeleteGroupTrainingBtn.clicked.connect(self.delete_training)

        # Кнопка "Выход"
        self.ui.ExitBtn.clicked.connect(self.close)

        # Кнопки навигации
        self.ui.ServiceBtn.clicked.connect(self.open_services)
        self.ui.ScheduleBtn.clicked.connect(self.on_schedule_clicked)
        self.ui.ClientsBtn.clicked.connect(self.open_clients)
        self.ui.TrainerBtn.clicked.connect(self.open_trainers)
        self.ui.HallBtn.clicked.connect(self.open_halls)
        self.ui.ReportBtn.clicked.connect(self.open_reports)

        # Подключаем изменение выбранной услуги
        self.ui.ServiceComboBox.currentIndexChanged.connect(self.on_service_changed)

    def reset_form(self):
        """Сброс формы добавления/редактирования"""
        self.current_training = None
        self.ui.DayEdit.clear()
        self.ui.MonthEdit.clear()
        self.ui.YearEdit.clear()
        self.ui.TimeEdit.clear()
        self.ui.ServiceComboBox.setCurrentIndex(0)
        self.ui.TrainercomboBox.setCurrentIndex(0)
        self.ui.HallE.clear()
        self.ui.MaxE.clear()

        self.ui.SaveGroupTrainingBtn.setText("Сохранить")
        self.ui.DeleteGroupTrainingBtn.setEnabled(False)
        self.ui.GroupTrainingL.setText("Групповая тренировка")

    def update_week_label(self):
        """Обновление метки с датами недели"""
        week_dates = self.get_week_dates()

        # Форматируем даты
        start_date = week_dates[0]
        end_date = week_dates[6]

        # Пример: "1-7 декабря 2025 г."
        month_names = ["января", "февраля", "марта", "апреля", "мая", "июня",
                       "июля", "августа", "сентября", "октября", "ноября", "декабря"]

        if start_date.month == end_date.month and start_date.year == end_date.year:
            # Один месяц
            date_text = f"{start_date.day}-{end_date.day} {month_names[start_date.month - 1]} {start_date.year} г."
        else:
            # Разные месяцы
            date_text = f"{start_date.day} {month_names[start_date.month - 1]} - {end_date.day} {month_names[end_date.month - 1]} {start_date.year} г."

        self.ui.DateL.setText(date_text)

    def previous_week(self):
        """Перейти на предыдущую неделю"""
        self.current_week_start -= timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    def next_week(self):
        """Перейти на следующую неделю"""
        self.current_week_start += timedelta(days=7)
        self.update_week_label()
        self.load_schedule()

    def on_service_changed(self, index):
        """Обработчик изменения выбранной услуги"""
        if index > 0:  # index 0 это "Выберите тренировку"
            service_id = self.ui.ServiceComboBox.currentData()
            if service_id:
                try:
                    # Используем модель Service для получения данных
                    service = Service.get_by_id(service_id)

                    if service and service.hall_id:
                        # Получаем информацию о зале
                        hall = Hall.get_by_id(service.hall_id)

                        if hall:
                            self.ui.HallE.setText(hall.hall_name)
                            self.ui.MaxE.setText(str(hall.capacity))

                            # Устанавливаем цвет зала
                            if hall.hall_id in self.hall_colors:
                                color = self.hall_colors[hall.hall_id]
                                # Можно установить цвет текста или фона
                        else:
                            self.ui.HallE.setText("Не указан")
                            self.ui.MaxE.clear()
                    else:
                        self.ui.HallE.clear()
                        self.ui.MaxE.clear()

                except Exception as e:
                    print(f"Ошибка получения данных услуги: {e}")
                    self.ui.HallE.clear()
                    self.ui.MaxE.clear()
        else:
            self.ui.HallE.clear()
            self.ui.MaxE.clear()

    def on_table_cell_clicked(self, row, column):
        """Обработчик клика по ячейке таблицы"""
        try:
            item = self.ui.ScheduleTable.item(row, column)
            if item:
                # Получаем данные из ячейки
                trainings = item.data(Qt.ItemDataRole.UserRole)

                if trainings and len(trainings) > 0:
                    # Если в ячейке несколько тренировок, показываем диалог выбора
                    if len(trainings) > 1:
                        self.show_training_selection_dialog(trainings, row, column)
                    else:
                        # Иначе редактируем единственную тренировку
                        self.edit_training(trainings[0])
                else:
                    # Если ячейка пустая, создаем новую тренировку
                    self.create_new_training(row, column)

        except Exception as e:
            print(f"Ошибка при обработке клика по таблице: {e}")

    def create_new_training(self, row, column):
        """Создание новой тренировки для выбранной ячейки"""
        try:
            # Получаем дату и время для ячейки
            week_dates = self.get_week_dates()
            selected_date = week_dates[column]
            time_slot = self.time_slots[row]

            # Устанавливаем дату и время в форму
            self.ui.DayEdit.setText(str(selected_date.day))
            self.ui.MonthEdit.setText(str(selected_date.month))
            self.ui.YearEdit.setText(str(selected_date.year))
            self.ui.TimeEdit.setText(time_slot)

            # Показываем панель редактирования
            self.show_edit_panel()
            self.reset_form()

            # Устанавливаем дату и время обратно (reset_form очистила их)
            self.ui.DayEdit.setText(str(selected_date.day))
            self.ui.MonthEdit.setText(str(selected_date.month))
            self.ui.YearEdit.setText(str(selected_date.year))
            self.ui.TimeEdit.setText(time_slot)

            self.ui.GroupTrainingL.setText("Новая групповая тренировка")

        except Exception as e:
            print(f"Ошибка создания новой тренировки: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать новую тренировку: {str(e)}")

    def edit_training(self, training):
        """Редактирование существующей тренировки"""
        try:
            self.current_training = training

            # Заполняем форму данными тренировки
            if training.training_date:
                training_date = datetime.strptime(str(training.training_date), "%Y-%m-%d")
                self.ui.DayEdit.setText(str(training_date.day))
                self.ui.MonthEdit.setText(str(training_date.month))
                self.ui.YearEdit.setText(str(training_date.year))

            if training.start_time:
                # Преобразуем время в строку HH:MM
                if isinstance(training.start_time, str):
                    time_str = training.start_time[:5]  # Берем только часы и минуты
                else:
                    time_str = str(training.start_time)[:5]
                self.ui.TimeEdit.setText(time_str)

            # Устанавливаем услугу
            if training.service_id:
                index = self.ui.ServiceComboBox.findData(training.service_id)
                if index >= 0:
                    self.ui.ServiceComboBox.setCurrentIndex(index)

            # Устанавливаем тренера
            if training.trainer_id:
                index = self.ui.TrainercomboBox.findData(training.trainer_id)
                if index >= 0:
                    self.ui.TrainercomboBox.setCurrentIndex(index)

            # Показываем панель редактирования
            self.show_edit_panel()
            self.ui.SaveGroupTrainingBtn.setText("Обновить")
            self.ui.DeleteGroupTrainingBtn.setEnabled(True)
            self.ui.GroupTrainingL.setText("Редактирование тренировки")

        except Exception as e:
            print(f"Ошибка редактирования тренировки: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные тренировки: {str(e)}")

    def show_training_selection_dialog(self, trainings, row, column):
        """Показать диалог выбора тренировки из нескольких"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите тренировку")
        dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()

        list_widget = QListWidget()
        for training in trainings:
            if hasattr(training, 'service_name'):
                item_text = f"{training.service_name} - {training.trainer_name if hasattr(training, 'trainer_name') else 'Тренер не указан'}"
                list_widget.addItem(item_text)

        layout.addWidget(list_widget)

        select_button = QPushButton("Выбрать")
        cancel_button = QPushButton("Отмена")

        def on_select():
            selected_index = list_widget.currentRow()
            if selected_index >= 0:
                dialog.accept()
                self.edit_training(trainings[selected_index])

        select_button.clicked.connect(on_select)
        cancel_button.clicked.connect(dialog.reject)

        button_layout = QVBoxLayout()
        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def save_training(self):
        """Сохранение/обновление тренировки"""
        try:
            # Получаем данные из формы
            day = self.ui.DayEdit.text().strip()
            month = self.ui.MonthEdit.text().strip()
            year = self.ui.YearEdit.text().strip()
            time_str = self.ui.TimeEdit.text().strip()
            service_id = self.ui.ServiceComboBox.currentData()
            trainer_id = self.ui.TrainercomboBox.currentData()

            # Валидация
            if not day or not month or not year:
                QMessageBox.warning(self, "Ошибка", "Введите полную дату!")
                return

            if not time_str:
                QMessageBox.warning(self, "Ошибка", "Введите время начала!")
                self.ui.TimeEdit.setFocus()
                return

            if not service_id:
                QMessageBox.warning(self, "Ошибка", "Выберите тренировку!")
                return

            if not trainer_id:
                QMessageBox.warning(self, "Ошибка", "Выберите тренера!")
                return

            # Формируем дату
            try:
                training_date = date(int(year), int(month), int(day))
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректная дата!")
                return

            # Форматируем время
            try:
                # Добавляем секунды если нужно
                if len(time_str) == 5:  # Формат HH:MM
                    time_str += ":00"
                start_time = datetime.strptime(time_str, "%H:%M:%S").time()
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректное время! Используйте формат ЧЧ:ММ")
                return

            # Проверяем доступность тренера
            exclude_id = self.current_training.group_training_id if self.current_training else None
            if not GroupTraining.check_trainer_availability(trainer_id, training_date, start_time, exclude_id):
                QMessageBox.warning(self, "Ошибка", "Тренер уже занят в это время!")
                return

            # Проверяем доступность зала
            service = Service.get_by_id(service_id)
            if service and service.hall_id:
                if not GroupTraining.check_hall_availability(service.hall_id, training_date, start_time, exclude_id):
                    QMessageBox.warning(self, "Ошибка", "Зал уже занят в это время!")
                    return

            if self.current_training:  # Редактирование
                self.current_training.training_date = training_date
                self.current_training.start_time = start_time
                self.current_training.service_id = service_id
                self.current_training.trainer_id = trainer_id

                if self.current_training.save():
                    QMessageBox.information(self, "Успех", "Тренировка успешно обновлена!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить тренировку")

            else:  # Добавление
                new_training = GroupTraining(
                    training_date=training_date,
                    start_time=start_time,
                    service_id=service_id,
                    trainer_id=trainer_id
                )

                if new_training.save():
                    QMessageBox.information(self, "Успех", "Тренировка успешно добавлена!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить тренировку")

            # Обновляем таблицу и скрываем панель
            self.load_schedule()
            self.hide_edit_panel()
            self.reset_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить тренировку: {str(e)}")
            print(f"Ошибка сохранения тренировки: {e}")

    def delete_training(self):
        """Удаление текущей тренировки"""
        if not self.current_training:
            QMessageBox.warning(self, "Ошибка", "Нет выбранной тренировки для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить эту тренировку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_training.delete():
                    QMessageBox.information(self, "Успех", "Тренировка удалена!")

                    # Обновляем таблицу и скрываем панель
                    self.load_schedule()
                    self.hide_edit_panel()
                    self.reset_form()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить тренировку")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тренировку: {str(e)}")

    # Методы навигации
    # УДАЛИТЕ этот импорт из начала файла:
    # from src.views.service_window import ServiceForm  # <-- УДАЛИТЬ

    # Вместо этого, внутри метода open_services используйте локальный импорт:
    def open_services(self):
        """Открыть окно услуг"""
        try:
            # Импортируем локально
            from src.views.service_window import ServiceForm
            self.service_window = ServiceForm(self.user_id, self.user_email, self.user_role)
            self.service_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта: {e}")
            QMessageBox.warning(self, "В разработке", "Окно услуг находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна услуг: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно услуг: {str(e)}")

    def on_schedule_clicked(self):
        """Обработчик кнопки 'Расписание'"""
        pass

    def open_clients(self):
        """Открыть окно клиентов"""
        try:
            # Импортируем локально
            from src.views.client_window import ClientWindow
            self.client_window = ClientWindow(self.user_id, self.user_email, self.user_role)
            self.client_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта: {e}")
            QMessageBox.warning(self, "В разработке", "Окно услуг находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна услуг: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно услуг: {str(e)}")

    def open_trainers(self):
        """Открыть окно тренеров"""
        try:
            from src.views.trainer_window import TrainerWindow
            self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
            self.trainer_window.show()
            self.close()
        except Exception as e:
            print(f"Ошибка открытия окна тренеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно тренеров: {str(e)}")

    def open_halls(self):
        """Открыть окно залов"""
        try:
            from src.views.hall_window import HallWindow
            self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
            self.hall_window.show()
            self.close()
        except Exception as e:
            print(f"Ошибка открытия окна залов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно залов: {str(e)}")

    def open_reports(self):
        """Открыть окно отчетов"""
        QMessageBox.information(self, "В разработке", "Окно отчетов находится в разработке")


def main():

    app = QApplication(sys.argv)
    window = ScheduleWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
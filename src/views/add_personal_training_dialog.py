# views/add_personal_training_dialog.py
from PyQt6.QtWidgets import QDialog, QMessageBox, QListWidgetItem
from PyQt6.QtCore import Qt, QTime
from datetime import datetime, timedelta
import re

from src.ui.add_personal_training_dialog import Ui_AddPersonalTrainingDialog
from src.database.connector import db
from src.models.trainers import Trainer
from src.models.trainer_types import TrainerType


class AddPersonalTrainingDialog(QDialog):
    """Диалог записи на персональную тренировку"""

    # Рабочие часы тренеров
    WORK_START_HOUR = 8  # 8:00
    WORK_END_HOUR = 19  # 19:00
    TRAINING_DURATION = 60  # Длительность тренировки в минутах

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.ui = Ui_AddPersonalTrainingDialog()
        self.ui.setupUi(self)

        # Клиент
        self.client = client
        self.current_training_id = None  # Для редактирования существующей записи

        # Устанавливаем заголовок
        self.setWindowTitle("Запись на персональную тренировку")

        # Настраиваем интерфейс
        self.setup_interface()

        # Подключаем обработчики
        self.connect_handlers()

        # Загружаем данные
        self.load_data()

        # Устанавливаем текущую дату по умолчанию
        self.set_current_date()

        # Для новой записи скрываем кнопку удаления
        self.ui.DeletePersonalTrainingBtn.setVisible(False)

    def setup_interface(self):
        """Настройка интерфейса"""
        # Отображаем имя клиента
        self.ui.Client.setText(self.client.get_full_name())

        # Настраиваем валидаторы для полей даты
        self.ui.DayPersonalTrainingEdit.setMaxLength(2)
        self.ui.MonthPersonalTrainingEdit.setMaxLength(2)
        self.ui.YearPersonalTrainingEdit.setMaxLength(4)

        # Настраиваем валидатор для цены
        self.ui.PricePersonalTrainingEdit.setMaxLength(6)

        # Устанавливаем плейсхолдеры
        today = datetime.now()
        self.ui.DayPersonalTrainingEdit.setPlaceholderText(str(today.day))
        self.ui.MonthPersonalTrainingEdit.setPlaceholderText(str(today.month))
        self.ui.YearPersonalTrainingEdit.setPlaceholderText(str(today.year))
        self.ui.PricePersonalTrainingEdit.setPlaceholderText("1000")

    def connect_handlers(self):
        """Подключение обработчиков событий"""
        # Кнопки
        self.ui.SavePersonalTrainingBtn.clicked.connect(self.save_training)
        self.ui.DeletePersonalTrainingBtn.clicked.connect(self.delete_training)

        # Изменение выбранного тренера
        self.ui.TrainerComboBox.currentIndexChanged.connect(self.on_trainer_changed)

        # Изменение даты
        self.ui.DayPersonalTrainingEdit.textChanged.connect(self.on_date_changed)
        self.ui.MonthPersonalTrainingEdit.textChanged.connect(self.on_date_changed)
        self.ui.YearPersonalTrainingEdit.textChanged.connect(self.on_date_changed)

        # Выбор времени из списка
        self.ui.FreeTimelistWidget.itemClicked.connect(self.on_time_selected)

    def load_data(self):
        """Загрузка данных тренеров"""
        try:
            self.ui.TrainerComboBox.clear()
            self.ui.TrainerComboBox.addItem("Выберите тренера", None)

            # Получаем всех тренеров (персональных и общих)
            trainers = Trainer.get_all()

            for trainer in trainers:
                # Проверяем тип тренера (персональный или общий)
                if trainer.trainer_type_id in [1, 3]:  # 1 - Общий, 3 - Персональный
                    display_text = f"{trainer.get_full_name()} ({trainer.trainer_type_name})"
                    self.ui.TrainerComboBox.addItem(display_text, trainer.trainer_id)

        except Exception as e:
            print(f"Ошибка загрузки тренеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список тренеров: {str(e)}")

    def set_current_date(self):
        """Установка текущей даты"""
        today = datetime.now()
        self.ui.DayPersonalTrainingEdit.setText(str(today.day))
        self.ui.MonthPersonalTrainingEdit.setText(str(today.month))
        self.ui.YearPersonalTrainingEdit.setText(str(today.year))

    def get_selected_trainer_id(self):
        """Получить ID выбранного тренера"""
        return self.ui.TrainerComboBox.currentData()

    def get_selected_date(self):
        """Получить выбранную дату"""
        try:
            day = self.ui.DayPersonalTrainingEdit.text().strip()
            month = self.ui.MonthPersonalTrainingEdit.text().strip()
            year = self.ui.YearPersonalTrainingEdit.text().strip()

            # Если поля пустые, используем текущую дату
            if not day or not month or not year:
                today = datetime.now()
                return today.date()

            # Проверяем корректность даты
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Проверяем, что дата не в прошлом
            if selected_date < datetime.now().date():
                QMessageBox.warning(self, "Предупреждение",
                                    "Нельзя записаться на прошедшую дату!")
                return datetime.now().date()

            return selected_date

        except ValueError:
            # Некорректная дата
            return None
        except Exception as e:
            print(f"Ошибка получения даты: {e}")
            return None

    def get_occupied_times(self, trainer_id, training_date):
        """Получить занятое время тренера на указанную дату"""
        occupied_times = []

        try:
            # Получаем все записи тренера на указанную дату
            query = """
            SELECT start_time 
            FROM personal_trainings 
            WHERE trainer_id = %s AND training_date = %s
            ORDER BY start_time
            """
            result = db.execute_query(query, (trainer_id, training_date))

            if result:
                for row in result:
                    occupied_times.append(str(row[0]))

        except Exception as e:
            print(f"Ошибка получения занятого времени: {e}")

        return occupied_times

    def generate_available_times(self, occupied_times):
        """Сгенерировать список доступного времени"""
        available_times = []

        # Генерируем все возможные слоты времени
        current_time = QTime(self.WORK_START_HOUR, 0)
        end_time = QTime(self.WORK_END_HOUR, 0)

        while current_time < end_time:
            time_str = current_time.toString("HH:mm")

            # Проверяем, не занято ли это время
            is_occupied = False
            for occupied in occupied_times:
                # Сравниваем время (без секунд)
                occupied_time = datetime.strptime(occupied, "%H:%M:%S").time()
                if current_time.hour() == occupied_time.hour and \
                        current_time.minute() == occupied_time.minute:
                    is_occupied = True
                    break

            if not is_occupied:
                available_times.append(time_str)

            # Добавляем длительность тренировки
            current_time = current_time.addSecs(self.TRAINING_DURATION * 60)

        return available_times

    def load_available_times(self):
        """Загрузка доступного времени"""
        # Очищаем список
        self.ui.FreeTimelistWidget.clear()

        # Получаем данные
        trainer_id = self.get_selected_trainer_id()
        training_date = self.get_selected_date()

        if not trainer_id:
            return

        if not training_date:
            QMessageBox.warning(self, "Предупреждение",
                                "Введите корректную дату!")
            return

        try:
            # Получаем занятое время
            occupied_times = self.get_occupied_times(trainer_id, training_date)

            # Генерируем доступное время
            available_times = self.generate_available_times(occupied_times)

            # Добавляем в список
            for time_str in available_times:
                item = QListWidgetItem(time_str)
                self.ui.FreeTimelistWidget.addItem(item)

            # Устанавливаем количество доступных слотов
            if available_times:
                self.ui.FreeTimelistWidget.setCurrentRow(0)
            else:
                QMessageBox.information(self, "Информация",
                                        "На выбранную дату у тренера нет свободного времени.")

        except Exception as e:
            print(f"Ошибка загрузки доступного времени: {e}")
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось загрузить доступное время: {str(e)}")

    def on_trainer_changed(self):
        """Обработчик изменения выбранного тренера"""
        self.load_available_times()

    def on_date_changed(self):
        """Обработчик изменения даты"""
        self.load_available_times()

    def on_time_selected(self, item):
        """Обработчик выбора времени"""
        # Автоматически устанавливаем цену при выборе времени
        self.set_default_price()

    def set_default_price(self):
        """Установить цену по умолчанию"""
        try:
            trainer_id = self.get_selected_trainer_id()
            if trainer_id:
                # Получаем данные тренера
                trainer = Trainer.get_by_id(trainer_id)
                if trainer and hasattr(trainer, 'rate'):
                    # Устанавливаем цену как ставку тренера
                    self.ui.PricePersonalTrainingEdit.setText(str(trainer.rate))
        except Exception as e:
            print(f"Ошибка установки цены: {e}")

    def validate_form(self):
        """Валидация формы"""
        # Проверяем тренера
        trainer_id = self.get_selected_trainer_id()
        if not trainer_id:
            QMessageBox.warning(self, "Ошибка", "Выберите тренера!")
            return False

        # Проверяем дату
        training_date = self.get_selected_date()
        if not training_date:
            QMessageBox.warning(self, "Ошибка", "Введите корректную дату!")
            return False

        # Проверяем время
        selected_items = self.ui.FreeTimelistWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите время тренировки!")
            return False

        # Проверяем цену
        price_text = self.ui.PricePersonalTrainingEdit.text().strip()
        if not price_text:
            QMessageBox.warning(self, "Ошибка", "Введите стоимость тренировки!")
            self.ui.PricePersonalTrainingEdit.setFocus()
            return False

        try:
            price = int(price_text)
            if price <= 0:
                QMessageBox.warning(self, "Ошибка", "Стоимость должна быть положительным числом!")
                return False
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную стоимость!")
            return False

        return True

    def save_training(self):
        """Сохранение записи на тренировку"""
        if not self.validate_form():
            return

        try:
            # Получаем данные из формы
            trainer_id = self.get_selected_trainer_id()
            training_date = self.get_selected_date()

            selected_item = self.ui.FreeTimelistWidget.currentItem()
            start_time = selected_item.text()

            price = int(self.ui.PricePersonalTrainingEdit.text().strip())

            # Формируем время в формате HH:MM:SS
            if ':' in start_time and len(start_time) == 5:
                start_time += ":00"

            if self.current_training_id:  # Редактирование
                query = """
                UPDATE personal_trainings 
                SET trainer_id = %s, training_date = %s, 
                    start_time = %s, price = %s
                WHERE personal_training_id = %s
                """
                params = (trainer_id, training_date, start_time,
                          price, self.current_training_id)
            else:  # Новая запись
                query = """
                INSERT INTO personal_trainings 
                (client_id, trainer_id, training_date, start_time, price)
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (self.client.client_id, trainer_id, training_date,
                          start_time, price)

            result = db.execute_query(query, params)

            if result:
                QMessageBox.information(self, "Успех",
                                        "Запись на тренировку сохранена!")
                self.accept()  # Закрываем диалог с успехом
            else:
                QMessageBox.critical(self, "Ошибка",
                                     "Не удалось сохранить запись!")

        except Exception as e:
            print(f"Ошибка сохранения тренировки: {e}")
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось сохранить запись: {str(e)}")

    def delete_training(self):
        """Удаление записи на тренировку"""
        if not self.current_training_id:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить запись на тренировку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM personal_trainings WHERE personal_training_id = %s"
                result = db.execute_query(query, (self.current_training_id,))

                if result:
                    QMessageBox.information(self, "Успех", "Запись удалена!")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить запись!")

            except Exception as e:
                print(f"Ошибка удаления тренировки: {e}")
                QMessageBox.critical(self, "Ошибка",
                                     f"Не удалось удалить запись: {str(e)}")

    def load_existing_training(self, training_id):
        """Загрузка существующей записи для редактирования"""
        try:
            self.current_training_id = training_id

            # Получаем данные тренировки
            query = """
            SELECT trainer_id, training_date, start_time, price
            FROM personal_trainings 
            WHERE personal_training_id = %s
            """
            result = db.execute_query(query, (training_id,))

            if result and len(result) > 0:
                trainer_id, training_date, start_time, price = result[0]

                # Устанавливаем тренера
                index = self.ui.TrainerComboBox.findData(trainer_id)
                if index >= 0:
                    self.ui.TrainerComboBox.setCurrentIndex(index)

                # Устанавливаем дату
                if training_date:
                    date_obj = training_date if isinstance(training_date, datetime) else \
                        datetime.strptime(str(training_date), "%Y-%m-%d")
                    self.ui.DayPersonalTrainingEdit.setText(str(date_obj.day))
                    self.ui.MonthPersonalTrainingEdit.setText(str(date_obj.month))
                    self.ui.YearPersonalTrainingEdit.setText(str(date_obj.year))

                # Устанавливаем время
                if start_time:
                    # Загружаем доступное время
                    self.load_available_times()

                    # Ищем и выбираем время в списке
                    time_str = str(start_time)[:5]  # Берем только HH:MM
                    items = self.ui.FreeTimelistWidget.findItems(time_str, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.ui.FreeTimelistWidget.setCurrentItem(items[0])

                # Устанавливаем цену
                self.ui.PricePersonalTrainingEdit.setText(str(price) if price else "")

                # Показываем кнопку удаления
                self.ui.DeletePersonalTrainingBtn.setVisible(True)

        except Exception as e:
            print(f"Ошибка загрузки существующей записи: {e}")
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось загрузить данные тренировки: {str(e)}")

    @staticmethod
    def add_training(client, parent=None):
        """Статический метод для добавления новой тренировки"""
        dialog = AddPersonalTrainingDialog(client, parent)
        if dialog.exec():
            return True
        return False

    @staticmethod
    def edit_training(training_id, client, parent=None):
        """Статический метод для редактирования существующей тренировки"""
        dialog = AddPersonalTrainingDialog(client, parent)
        dialog.load_existing_training(training_id)
        if dialog.exec():
            return True
        return False
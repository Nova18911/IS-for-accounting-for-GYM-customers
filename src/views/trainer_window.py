# views/trainer_window.py
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QApplication, QFileDialog
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QImage

from src.ui.trainer_window import Ui_TrainerForm
from src.models.trainers import Trainer
from src.models.trainer_types import TrainerType
from src.views.hall_window import HallWindow


class TrainerWindow(QMainWindow):
    """Окно управления тренерами"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_TrainerForm()
        self.ui.setupUi(self)

        # Данные пользователя
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Текущий редактируемый тренер
        self.current_trainer = None

        # Путь к фото тренера (храним временно)
        self.current_photo_path = None
        # Бинарные данные фото (для сохранения в БД)
        self.current_photo_data = None

        # Устанавливаем заголовок окна
        self.setWindowTitle("Фитнес-Менеджер - Тренеры")

        # Настраиваем интерфейс
        self.setup_interface()

        # Загружаем данные
        self.load_trainer_types()  # Загружаем типы тренеров в ComboBox
        self.load_trainers()  # Загружаем тренеров в таблицу

        # Подключаем кнопки
        self.connect_buttons()

        # Скрываем правую панель при запуске
        self.hide_edit_panel()

        # Сбрасываем форму добавления/редактирования
        self.reset_form()

        # Делаем кнопку "Тренеры" неактивной
        self.ui.TrainerButton.setEnabled(False)

    def setup_interface(self):
        """Настройка интерфейса"""
        # Настраиваем таблицу
        self.ui.TrainerTableWidget.setColumnWidth(0, 120)  # Фамилия
        self.ui.TrainerTableWidget.setColumnWidth(1, 100)  # Имя
        self.ui.TrainerTableWidget.setColumnWidth(2, 120)  # Отчество
        self.ui.TrainerTableWidget.setColumnWidth(3, 150)  # Телефон

        # Разрешаем выделение строк
        self.ui.TrainerTableWidget.setSelectionBehavior(
            self.ui.TrainerTableWidget.SelectionBehavior.SelectRows
        )

        # Отключаем редактирование ячеек
        self.ui.TrainerTableWidget.setEditTriggers(
            self.ui.TrainerTableWidget.EditTrigger.NoEditTriggers
        )

        # Подключаем двойной клик по таблице
        self.ui.TrainerTableWidget.doubleClicked.connect(self.on_table_double_click)

        # Подключаем одиночный клик по таблице
        self.ui.TrainerTableWidget.itemClicked.connect(self.on_table_item_clicked)

        # Подключаем поиск
        self.ui.SearchLastNameEdit.textChanged.connect(self.on_search_last_name_changed)
        self.ui.SearchPhoneEdit.textChanged.connect(self.on_search_phone_changed)

        # Делаем label для фото кликабельным
        self.ui.PhotoTrainerE.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.PhotoTrainerE.mousePressEvent = self.on_photo_label_clicked

        # Устанавливаем рамку для фото
        self.ui.PhotoTrainerE.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)

    def on_photo_label_clicked(self, event):
        """Обработчик клика на label с фото"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.load_photo()

    def load_photo(self):
        """Загрузка фото для тренера"""
        try:
            # Открываем диалог выбора файла
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите фото тренера",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
            )

            if file_path:
                # Проверяем размер файла (максимум 5 MB)
                file_size = os.path.getsize(file_path)
                if file_size > 5 * 1024 * 1024:  # 5 MB
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "Размер файла слишком большой. Максимальный размер - 5 MB."
                    )
                    return

                # Загружаем фото
                pixmap = QPixmap(file_path)

                # Масштабируем фото для отображения (максимум 150x150)
                if not pixmap.isNull():
                    # Сохраняем путь к файлу
                    self.current_photo_path = file_path

                    # Сохраняем бинарные данные для БД
                    with open(file_path, 'rb') as file:
                        self.current_photo_data = file.read()

                    # Отображаем миниатюру
                    scaled_pixmap = pixmap.scaled(
                        150, 150,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.ui.PhotoTrainerE.setPixmap(scaled_pixmap)

                    # Меняем стиль, чтобы показать что фото загружено
                    self.ui.PhotoTrainerE.setStyleSheet("""
                        QLabel {
                            border: 2px solid #4CAF50;
                            border-radius: 5px;
                            padding: 5px;
                        }
                    """)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить фото: {str(e)}")

    def clear_photo(self):
        """Очистка фото тренера"""
        self.ui.PhotoTrainerE.clear()
        self.ui.PhotoTrainerE.setText("Фото")
        self.current_photo_path = None
        self.current_photo_data = None

        # Возвращаем стиль по умолчанию
        self.ui.PhotoTrainerE.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)

    def show_edit_panel(self):
        """Показать правую панель для добавления/редактирования"""
        self.ui.widget_2.setVisible(True)

    def hide_edit_panel(self):
        """Скрыть правую панель для добавления/редактирования"""
        self.ui.widget_2.setVisible(False)

    def make_table_readonly(self):
        """Делает таблицу полностью нередактируемой"""
        for row in range(self.ui.TrainerTableWidget.rowCount()):
            for col in range(self.ui.TrainerTableWidget.columnCount()):
                item = self.ui.TrainerTableWidget.item(row, col)
                if item:
                    current_flags = item.flags()
                    new_flags = current_flags & ~Qt.ItemFlag.ItemIsEditable
                    item.setFlags(new_flags)

    def load_trainer_types(self):
        """Загрузка типов тренеров в ComboBox"""
        try:
            self.ui.TrainerTypeComboBox.clear()
            self.ui.TrainerTypeComboBox.addItem("Выберите тип", None)

            # Используем модель TrainerType для получения данных
            trainer_types = TrainerType.get_all()

            if trainer_types:
                for trainer_type in trainer_types:
                    self.ui.TrainerTypeComboBox.addItem(
                        trainer_type.trainer_type_name,
                        trainer_type.trainer_type_id
                    )

        except Exception as e:
            print(f"Ошибка загрузки типов тренеров: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить типы тренеров: {str(e)}")

    def load_trainers(self):
        """Загрузка тренеров из БД в таблицу"""
        try:
            self.ui.TrainerTableWidget.setRowCount(0)

            # Используем модель Trainer для получения данных
            trainers = Trainer.get_all()

            if trainers:
                for row_num, trainer in enumerate(trainers):
                    self.ui.TrainerTableWidget.insertRow(row_num)

                    # Создаем ячейки ТОЛЬКО ДЛЯ ЧТЕНИЯ
                    item_last_name = QTableWidgetItem(str(trainer.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, trainer.trainer_id)

                    item_first_name = QTableWidgetItem(str(trainer.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(trainer.middle_name) if trainer.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(trainer.phone) if trainer.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Устанавливаем ячейки
                    self.ui.TrainerTableWidget.setItem(row_num, 0, item_last_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 1, item_first_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 3, item_phone)

            self.make_table_readonly()

        except Exception as e:
            print(f"Ошибка загрузки тренеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить тренеров: {str(e)}")

    def connect_buttons(self):
        """Подключение обработчиков кнопок"""
        # Кнопка "Добавить"
        self.ui.Add_clientBtn.clicked.connect(self.add_trainer)

        # Кнопка "Сохранить"
        self.ui.SaveTrainerBtn.clicked.connect(self.save_trainer)

        # Кнопка "Удалить"
        self.ui.DeleteTrainerBtn.clicked.connect(self.delete_trainer)

        # Кнопка "Выход"
        self.ui.ExitButton.clicked.connect(self.close)

        # Кнопки навигации
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.ClientsButton.clicked.connect(self.open_clients)
        self.ui.TrainerButton.clicked.connect(self.on_trainers_clicked)
        self.ui.HallButton.clicked.connect(self.open_halls)
        self.ui.ReportButton.clicked.connect(self.open_reports)

        # Подключаем изменение выбранного типа тренера
        self.ui.TrainerTypeComboBox.currentIndexChanged.connect(self.on_trainer_type_changed)

    def reset_form(self):
        """Сброс формы добавления/редактирования"""
        self.current_trainer = None
        self.ui.LastNameTrainerEdit.clear()
        self.ui.FirstNameTrainerEdit.clear()
        self.ui.MidleNameTrainerEdit.clear()
        self.ui.PhoneTrainer.clear()
        self.ui.EmailTrainerEdit.clear()
        self.ui.TrainerTypeComboBox.setCurrentIndex(0)
        self.ui.RateE.clear()
        self.ui.IdTrainerE.clear()

        # Очищаем фото
        self.clear_photo()

        self.ui.SaveTrainerBtn.setText("Сохранить")
        self.ui.DeleteTrainerBtn.setEnabled(False)
        self.ui.Add_clientBtn.setEnabled(True)

    def on_trainer_type_changed(self, index):
        """Обработчик изменения выбранного типа тренера"""
        if index > 0:  # index 0 это "Выберите тип"
            trainer_type_id = self.ui.TrainerTypeComboBox.currentData()
            if trainer_type_id:
                try:
                    # Используем модель TrainerType для получения данных
                    trainer_type = TrainerType.get_by_id(trainer_type_id)

                    if trainer_type:
                        self.ui.RateE.setText(f"{trainer_type.rate} руб.")
                    else:
                        self.ui.RateE.clear()

                except Exception as e:
                    print(f"Ошибка получения данных типа тренера: {e}")
                    self.ui.RateE.clear()
        else:
            self.ui.RateE.clear()

    def add_trainer(self):
        """Кнопка 'Добавить' - сброс формы для нового тренера"""
        self.show_edit_panel()
        self.reset_form()
        self.ui.LastNameTrainerEdit.setFocus()

    def get_selected_trainer_id(self):
        """Получение ID выбранного тренера из таблицы"""
        selected_row = self.ui.TrainerTableWidget.currentRow()
        if selected_row >= 0:
            item = self.ui.TrainerTableWidget.item(selected_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def on_table_double_click(self, index):
        """Обработка двойного клика по таблице - редактирование"""
        trainer_id = self.get_selected_trainer_id()
        if trainer_id:
            self.edit_trainer(trainer_id)

    def on_table_item_clicked(self, item):
        """Обработка клика по элементу таблицы"""
        trainer_id = self.get_selected_trainer_id()
        if trainer_id:
            self.edit_trainer(trainer_id)

    def edit_trainer(self, trainer_id=None):
        """Редактирование выбранного тренера"""
        if not trainer_id:
            trainer_id = self.get_selected_trainer_id()

        if trainer_id:
            try:
                # Используем модель Trainer для загрузки данных
                self.current_trainer = Trainer.get_by_id(trainer_id)

                if self.current_trainer:
                    # Показываем панель редактирования
                    self.show_edit_panel()

                    # Заполняем форму
                    self.ui.LastNameTrainerEdit.setText(self.current_trainer.last_name)
                    self.ui.FirstNameTrainerEdit.setText(self.current_trainer.first_name)
                    self.ui.MidleNameTrainerEdit.setText(
                        self.current_trainer.middle_name if self.current_trainer.middle_name else "")
                    self.ui.PhoneTrainer.setText(self.current_trainer.phone if self.current_trainer.phone else "")

                    # Устанавливаем ID карты (номер карты)
                    self.ui.IdTrainerE.setText(str(self.current_trainer.trainer_id))

                    # Устанавливаем выбранный тип тренера
                    if self.current_trainer.trainer_type_id:
                        index = self.ui.TrainerTypeComboBox.findData(self.current_trainer.trainer_type_id)
                        if index >= 0:
                            self.ui.TrainerTypeComboBox.setCurrentIndex(index)

                    # Загружаем фото тренера, если оно есть
                    if self.current_trainer.photo:
                        try:
                            # Предполагаем, что фото хранится в БД как BLOB
                            pixmap = QPixmap()
                            pixmap.loadFromData(self.current_trainer.photo)

                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(
                                    150, 150,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation
                                )
                                self.ui.PhotoTrainerE.setPixmap(scaled_pixmap)
                                self.ui.PhotoTrainerE.setStyleSheet("""
                                    QLabel {
                                        border: 2px solid #4CAF50;
                                        border-radius: 5px;
                                        padding: 5px;
                                    }
                                """)
                            else:
                                self.clear_photo()
                        except Exception as e:
                            print(f"Ошибка загрузки фото из БД: {e}")
                            self.clear_photo()
                    else:
                        self.clear_photo()

                    # Активируем кнопку удаления
                    self.ui.DeleteTrainerBtn.setEnabled(True)
                    self.ui.SaveTrainerBtn.setText("Обновить")
                    self.ui.Add_clientBtn.setEnabled(False)
                else:
                    QMessageBox.warning(self, "Ошибка", "Тренер не найден!")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные тренера: {str(e)}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите тренера для редактирования")

    def save_trainer(self):
        """Сохранение/обновление тренера через модель"""
        try:
            # Получаем данные из формы
            last_name = self.ui.LastNameTrainerEdit.text().strip()
            first_name = self.ui.FirstNameTrainerEdit.text().strip()
            middle_name = self.ui.MidleNameTrainerEdit.text().strip()
            phone = self.ui.PhoneTrainer.text().strip()
            trainer_type_id = self.ui.TrainerTypeComboBox.currentData()

            # Валидация
            if not last_name:
                QMessageBox.warning(self, "Ошибка", "Введите фамилию тренера!")
                self.ui.LastNameTrainerEdit.setFocus()
                return

            if not first_name:
                QMessageBox.warning(self, "Ошибка", "Введите имя тренера!")
                self.ui.FirstNameTrainerEdit.setFocus()
                return

            if not trainer_type_id:
                QMessageBox.warning(self, "Ошибка", "Выберите тип тренера!")
                return

            if not phone:
                QMessageBox.warning(self, "Ошибка", "Введите телефон тренера!")
                self.ui.PhoneTrainer.setFocus()
                return

            if self.current_trainer:  # Редактирование существующего тренера
                self.current_trainer.last_name = last_name
                self.current_trainer.first_name = first_name
                self.current_trainer.middle_name = middle_name
                self.current_trainer.phone = phone
                self.current_trainer.trainer_type_id = trainer_type_id

                # Обновляем фото, если было выбрано новое
                if self.current_photo_data:
                    self.current_trainer.photo = self.current_photo_data
                # Если фото не было выбрано новое, но было в БД, оставляем старое
                # (фото остается как есть, если self.current_photo_data is None)

                if self.current_trainer.save():
                    QMessageBox.information(self, "Успех", "Данные тренера успешно обновлены!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить данные тренера")

            else:  # Добавление нового тренера
                # Создаем нового тренера
                new_trainer = Trainer(
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    phone=phone,
                    trainer_type_id=trainer_type_id
                )

                # Добавляем фото, если оно было загружено
                if self.current_photo_data:
                    new_trainer.photo = self.current_photo_data

                if new_trainer.save():
                    QMessageBox.information(self, "Успех", "Тренер успешно добавлен!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить тренера")

            # Обновляем таблицу и скрываем панель
            self.load_trainers()
            self.hide_edit_panel()
            self.reset_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные тренера: {str(e)}")

    def delete_trainer(self):
        """Удаление текущего тренера через модель"""
        if not self.current_trainer:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного тренера для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить тренера '{self.current_trainer.get_full_name()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_trainer.delete():
                    QMessageBox.information(self, "Успех", "Тренер удален!")

                    # Обновляем таблицу и скрываем панель
                    self.load_trainers()
                    self.hide_edit_panel()
                    self.reset_form()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить тренера")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тренера: {str(e)}")

    def on_search_last_name_changed(self, text):
        """Обработчик изменения поля поиска по фамилии"""
        if text.strip():
            self.search_trainers_by_last_name(text.strip())
        else:
            self.load_trainers()  # Если поле пустое, показываем всех

    def on_search_phone_changed(self, text):
        """Обработчик изменения поля поиска по телефону"""
        if text.strip():
            self.search_trainers_by_phone(text.strip())
        else:
            self.load_trainers()  # Если поле пустое, показываем всех

    def search_trainers_by_last_name(self, last_name):
        """Поиск тренеров по фамилии"""
        try:
            self.ui.TrainerTableWidget.setRowCount(0)

            # Используем метод поиска модели Trainer
            trainers = Trainer.search_by_last_name(last_name)

            if trainers:
                for row_num, trainer in enumerate(trainers):
                    self.ui.TrainerTableWidget.insertRow(row_num)

                    item_last_name = QTableWidgetItem(str(trainer.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, trainer.trainer_id)

                    item_first_name = QTableWidgetItem(str(trainer.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(trainer.middle_name) if trainer.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(trainer.phone) if trainer.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.ui.TrainerTableWidget.setItem(row_num, 0, item_last_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 1, item_first_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 3, item_phone)

            self.make_table_readonly()

        except Exception as e:
            print(f"Ошибка поиска тренеров: {e}")

    def search_trainers_by_phone(self, phone):
        """Поиск тренеров по телефону"""
        try:
            self.ui.TrainerTableWidget.setRowCount(0)

            # Используем метод поиска модели Trainer
            trainers = Trainer.search_by_phone(phone)

            if trainers:
                for row_num, trainer in enumerate(trainers):
                    self.ui.TrainerTableWidget.insertRow(row_num)

                    item_last_name = QTableWidgetItem(str(trainer.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, trainer.trainer_id)

                    item_first_name = QTableWidgetItem(str(trainer.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(trainer.middle_name) if trainer.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(trainer.phone) if trainer.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.ui.TrainerTableWidget.setItem(row_num, 0, item_last_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 1, item_first_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.TrainerTableWidget.setItem(row_num, 3, item_phone)

            self.make_table_readonly()

        except Exception as e:
            print(f"Ошибка поиска тренеров: {e}")

    # Методы навигации
    def open_services(self):
        """Открыть окно услуг"""
        try:
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

    def open_schedule(self):
        """Открыть окно расписания"""
        try:
            from src.views.schedule_window import ScheduleWindow
            self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
            self.schedule_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта ScheduleWindow: {e}")
            QMessageBox.warning(self, "В разработке", "Окно расписания находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна расписания: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно расписания: {str(e)}")

    def open_clients(self):
        """Открыть окно клиентов"""
        QMessageBox.information(self, "В разработке", "Окно клиентов находится в разработке")

    def on_trainers_clicked(self):
        """Обработчик кнопки 'Тренеры'"""
        pass

    def open_halls(self):
        """Открыть окно залов"""
        try:
            self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
            self.hall_window.show()
            self.close()
        except Exception as e:
            print(f"Ошибка открытия окна залов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окна залов: {str(e)}")

    def open_reports(self):
        """Открыть окно отчетов"""
        QMessageBox.information(self, "В разработке", "Окно отчетов находится в разработке")
# views/client_window.py
import sys
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QApplication, QFileDialog, QHeaderView
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap

from src.ui.client_window import Ui_client_window
from src.models.client import Client
from src.models.subscriptions import Subscription
from src.views.trainer_window import TrainerWindow


class ClientWindow(QMainWindow):
    """Окно управления клиентами"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_client_window()
        self.ui.setupUi(self)

        # Данные пользователя
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Текущий редактируемый клиент и абонемент
        self.current_client = None
        self.current_subscription = None

        # Путь к фото клиента (храним временно)
        self.current_photo_path = None
        self.current_photo_data = None

        # Устанавливаем заголовок окна
        self.setWindowTitle("Фитнес-Менеджер - Клиенты")

        # Настраиваем интерфейс
        self.setup_interface()

        # Загружаем данные
        self.load_clients()  # Загружаем клиентов в таблицу
        self.load_long_time_options()  # Загружаем опции продолжительности абонемента

        # Подключаем кнопки
        self.connect_buttons()

        # Сбрасываем форму
        self.reset_form()

        # Делаем кнопку "Клиенты" неактивной
        self.ui.ClientsButton.setEnabled(False)

        # Скрываем правую панель при запуске
        self.hide_edit_panel()

        self.disable_subscription_and_training_tabs()

    def setup_interface(self):
        """Настройка интерфейса"""
        # Настраиваем таблицу клиентов
        self.ui.ClientsTabWidget.setColumnWidth(0, 120)  # Фамилия
        self.ui.ClientsTabWidget.setColumnWidth(1, 100)  # Имя
        self.ui.ClientsTabWidget.setColumnWidth(2, 120)  # Отчество
        self.ui.ClientsTabWidget.setColumnWidth(3, 150)  # Телефон
        self.ui.ClientsTabWidget.setColumnWidth(4, 100)  # № Карты
        self.ui.ClientsTabWidget.setColumnWidth(5, 50)  # Актив.

        # Разрешаем выделение строк
        self.ui.ClientsTabWidget.setSelectionBehavior(
            self.ui.ClientsTabWidget.SelectionBehavior.SelectRows
        )

        # Отключаем редактирование ячеек
        self.ui.ClientsTabWidget.setEditTriggers(
            self.ui.ClientsTabWidget.EditTrigger.NoEditTriggers
        )

        # Подключаем двойной клик по таблице
        self.ui.ClientsTabWidget.doubleClicked.connect(self.on_table_double_click)

        # Подключаем одиночный клик по таблице
        self.ui.ClientsTabWidget.itemClicked.connect(self.on_table_item_clicked)

        # Подключаем поиск
        self.ui.SearchLastNameEdit.textChanged.connect(self.on_search_last_name_changed)
        self.ui.SearchPhoneEdit.textChanged.connect(self.on_search_phone_changed)

        # Делаем label для фото кликабельным
        self.ui.Photo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.Photo.mousePressEvent = self.on_photo_label_clicked

        # Устанавливаем рамку для фото
        self.ui.Photo.setStyleSheet("""
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

        # Настраиваем таблицы тренировок
        self.ui.PersonalTrainingTabWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.GroupTrainingTabWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Скрываем заголовки таблиц тренировок (они и так скрыты в UI)
        self.ui.PersonalTrainingTabWidget.horizontalHeader().setVisible(False)
        self.ui.GroupTrainingTabWidget.horizontalHeader().setVisible(False)

        # Подключаем обработчики для полей даты оформления абонемента
        self.ui.Day_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.Month_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.Year_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.LongTimeComboBox.currentIndexChanged.connect(self.calculate_end_date)

        self.ui.ClientTabWidget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """Обработчик смены вкладок"""
        if index == 1:  # Вкладка "Карта"
            if not self.current_client:
                QMessageBox.warning(self, "Предупреждение", "Сначала выберите или создайте клиента!")
                self.ui.ClientTabWidget.setCurrentIndex(0)  # Возвращаемся на вкладку "Клиент"
                return

        elif index == 2:  # Вкладка "Тренировки"
            if not self.current_client:
                QMessageBox.warning(self, "Предупреждение", "Сначала выберите или создайте клиента!")
                self.ui.ClientTabWidget.setCurrentIndex(0)  # Возвращаемся на вкладку "Клиент"
                return
            else:
                # Обновляем данные тренировок при переходе на вкладку
                self.load_trainings_data()

    def disable_subscription_and_training_tabs(self):
        """Сделать вкладки 'Карта' и 'Тренировки' недоступными"""
        # Делаем вкладки неактивными
        self.ui.ClientTabWidget.setTabEnabled(1, False)  # Вкладка "Карта" (индекс 1)
        self.ui.ClientTabWidget.setTabEnabled(2, False)  # Вкладка "Тренировки" (индекс 2)

        # Меняем стиль, чтобы показать, что вкладки недоступны
        style = """
        QTabBar::tab:disabled {
            color: #999;
            background-color: #f0f0f0;
        }
        """
        self.ui.ClientTabWidget.setStyleSheet(style)

    def enable_subscription_and_training_tabs(self):
        """Сделать вкладки 'Карта' и 'Тренировки' доступными"""
        # Делаем вкладки активными
        self.ui.ClientTabWidget.setTabEnabled(1, True)  # Вкладка "Карта"
        self.ui.ClientTabWidget.setTabEnabled(2, True)  # Вкладка "Тренировки"

        # Возвращаем стандартный стиль
        self.ui.ClientTabWidget.setStyleSheet("")

    def show_subscription_tab_only(self):
        """Показать только вкладку 'Карта' (если есть активный абонемент)"""
        self.enable_subscription_and_training_tabs()
        # Можно также скрыть вкладку "Тренировки", если нужно
        # self.ui.ClientTabWidget.setTabEnabled(2, False)

    def show_edit_panel(self):
        """Показать правую панель для добавления/редактирования"""
        self.ui.ClientTabWidget.setVisible(True)

    def hide_edit_panel(self):
        """Скрыть правую панель для добавления/редактирования"""
        self.ui.ClientTabWidget.setVisible(False)

    def on_photo_label_clicked(self, event):
        """Обработчик клика на label с фото"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.load_photo()

    def load_photo(self):
        """Загрузка фото для клиента"""
        try:
            # Открываем диалог выбора файла
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите фото клиента",
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

                # Масштабируем фото для отображения
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
                    self.ui.Photo.setPixmap(scaled_pixmap)

                    # Меняем стиль, чтобы показать что фото загружено
                    self.ui.Photo.setStyleSheet("""
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
        """Очистка фото клиента"""
        self.ui.Photo.clear()
        self.ui.Photo.setText("Фото")
        self.current_photo_path = None
        self.current_photo_data = None

        # Возвращаем стиль по умолчанию
        self.ui.Photo.setStyleSheet("""
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

    def load_clients(self):
        """Загрузка клиентов из БД в таблицу"""
        try:
            self.ui.ClientsTabWidget.setRowCount(0)

            # Используем модель Client для получения данных
            clients = Client.get_all()

            if clients:
                for row_num, client in enumerate(clients):
                    self.ui.ClientsTabWidget.insertRow(row_num)

                    # Создаем ячейки ТОЛЬКО ДЛЯ ЧТЕНИЯ
                    item_last_name = QTableWidgetItem(str(client.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, client.client_id)

                    item_first_name = QTableWidgetItem(str(client.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(client.middle_name) if client.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(client.phone) if client.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_card = QTableWidgetItem(str(client.card_number) if client.card_number else "")
                    item_card.setFlags(item_card.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_active = QTableWidgetItem("✓" if client.is_active else "✗")
                    item_active.setFlags(item_active.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Устанавливаем ячейки
                    self.ui.ClientsTabWidget.setItem(row_num, 0, item_last_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 1, item_first_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 3, item_phone)
                    self.ui.ClientsTabWidget.setItem(row_num, 4, item_card)
                    self.ui.ClientsTabWidget.setItem(row_num, 5, item_active)

        except Exception as e:
            print(f"Ошибка загрузки клиентов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить клиентов: {str(e)}")

    def load_long_time_options(self):
        """Загрузка опций продолжительности абонемента"""
        try:
            self.ui.LongTimeComboBox.clear()

            # ТОЛЬКО стандартные варианты из ТЗ
            options = [
                ("1 месяц", 30),
                ("3 месяца", 90),
                ("6 месяцев", 180),
                ("12 месяцев", 365)
            ]

            for name, days in options:
                self.ui.LongTimeComboBox.addItem(name, days)

        except Exception as e:
            print(f"Ошибка загрузки опций продолжительности: {e}")

    def connect_buttons(self):
        """Подключение обработчиков кнопок"""
        # Кнопка "Добавить"
        self.ui.Add_clientBtn.clicked.connect(self.add_client)

        # Кнопки вкладки "Клиент"
        self.ui.Save_clientBtn.clicked.connect(self.save_client)
        self.ui.Delete_clientBtn.clicked.connect(self.delete_client)

        # Кнопки вкладки "Карта"
        self.ui.SaveSubBtn.clicked.connect(self.save_subscription)
        self.ui.DeleteSubBtn.clicked.connect(self.delete_subscription)

        # Кнопки вкладки "Тренировки"
        self.ui.PersonalTrainingBtn.clicked.connect(self.open_personal_training)
        self.ui.GroupTrainingBtn.clicked.connect(self.open_group_training)

        # Кнопка "Выход"
        self.ui.ExitButton.clicked.connect(self.close)

        # Кнопки навигации
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.ClientsButton.clicked.connect(self.on_clients_clicked)
        self.ui.TrainerButton.clicked.connect(self.open_trainers)
        self.ui.HallButton.clicked.connect(self.open_halls)
        self.ui.ReportButton.clicked.connect(self.open_reports)

    def reset_form(self):
        """Сброс формы добавления/редактирования"""
        self.current_client = None
        self.current_subscription = None

        # Сбрасываем вкладку "Клиент"
        self.ui.Last_nameEdit.clear()
        self.ui.First_nameEdit.clear()
        self.ui.Midle_nameEdit.clear()
        self.ui.PhoneEdit.clear()
        self.ui.EmailEdit.clear()

        # Очищаем фото
        self.clear_photo()

        # Сбрасываем вкладку "Карта"
        self.ui.id_subsrciption.clear()
        self.ui.Day_subEdit.clear()
        self.ui.Month_subEdit.clear()
        self.ui.Year_subEdit.clear()
        self.ui.LongTimeComboBox.setCurrentIndex(0)
        self.ui.DayEndLable.clear()
        self.ui.MonthEndLabel.clear()
        self.ui.YearEndLabel.clear()
        self.ui.PriceLabel.clear()

        # Сбрасываем вкладку "Тренировки"
        self.ui.PersonalTrainingTabWidget.setRowCount(0)
        self.ui.GroupTrainingTabWidget.setRowCount(0)

        self.ui.Delete_clientBtn.setEnabled(False)
        self.ui.DeleteSubBtn.setEnabled(False)

        self.disable_subscription_and_training_tabs()
        # Скрываем правую панель
        self.hide_edit_panel()  # Добавить эту строку

    def add_client(self):
        """Кнопка 'Добавить' - сброс формы для нового клиента"""
        self.reset_form()
        self.show_edit_panel()
        self.enable_subscription_and_training_tabs()
        self.ui.ClientTabWidget.setCurrentIndex(0)  # Переключаемся на вкладку "Клиент"
        self.ui.Last_nameEdit.setFocus()

    def get_selected_client_id(self):
        """Получение ID выбранного клиента из таблицы"""
        selected_row = self.ui.ClientsTabWidget.currentRow()
        if selected_row >= 0:
            item = self.ui.ClientsTabWidget.item(selected_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def on_table_double_click(self, index):
        """Обработка двойного клика по таблице - редактирование"""
        client_id = self.get_selected_client_id()
        if client_id:
            self.edit_client(client_id)

    def on_table_item_clicked(self, item):
        """Обработка клика по элементу таблицы"""
        client_id = self.get_selected_client_id()
        if client_id:
            self.edit_client(client_id)

    def edit_client(self, client_id=None):
        """Редактирование выбранного клиента"""
        if not client_id:
            client_id = self.get_selected_client_id()

        if client_id:
            try:
                # Загружаем клиента из БД
                self.current_client = Client.get_by_id(client_id)

                if self.current_client:
                    # Заполняем вкладку "Клиент"
                    self.ui.Last_nameEdit.setText(self.current_client.last_name)
                    self.ui.First_nameEdit.setText(self.current_client.first_name)
                    self.ui.Midle_nameEdit.setText(
                        self.current_client.middle_name if self.current_client.middle_name else "")
                    self.ui.PhoneEdit.setText(self.current_client.phone if self.current_client.phone else "")
                    self.ui.EmailEdit.setText(self.current_client.email if self.current_client.email else "")

                    # Загружаем фото клиента, если оно есть
                    if self.current_client.photo:
                        try:
                            pixmap = QPixmap()
                            pixmap.loadFromData(self.current_client.photo)

                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(
                                    150, 150,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation
                                )
                                self.ui.Photo.setPixmap(scaled_pixmap)
                                self.ui.Photo.setStyleSheet("""
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

                    # Загружаем данные абонемента
                    self.load_subscription_data()

                    # Загружаем тренировки
                    self.load_trainings_data()

                    # Делаем вкладки "Карта" и "Тренировки" доступными
                    self.enable_subscription_and_training_tabs()

                    # Показываем правую панель
                    self.show_edit_panel()  # Добавить эту строку

                    # Активируем кнопку удаления
                    self.ui.Delete_clientBtn.setEnabled(True)
                    self.ui.ClientTabWidget.setCurrentIndex(0)  # Показываем вкладку "Клиент"
                else:
                    QMessageBox.warning(self, "Ошибка", "Клиент не найден!")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные клиента: {str(e)}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для редактирования")

    def load_subscription_data(self):
        """Загрузка данных абонемента"""
        if not self.current_client:
            return

        try:
            # Получаем активный абонемент
            self.current_subscription = self.current_client.get_active_subscription()

            if self.current_subscription:
                # Заполняем поля абонемента
                self.ui.id_subsrciption.setText(str(self.current_subscription.subscription_id))

                # Дата оформления
                start_date = self.current_subscription.start_date
                if start_date:
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, "%Y-%m-%d")

                    self.ui.Day_subEdit.setText(str(start_date.day))
                    self.ui.Month_subEdit.setText(str(start_date.month))
                    self.ui.Year_subEdit.setText(str(start_date.year))

                # Продолжительность
                duration = self.current_subscription.duration_days
                if duration:
                    # Находим соответствующий индекс в ComboBox
                    for i in range(self.ui.LongTimeComboBox.count()):
                        if self.ui.LongTimeComboBox.itemData(i) == duration:
                            self.ui.LongTimeComboBox.setCurrentIndex(i)
                            break

                # Дата окончания и цена
                if self.current_subscription.end_date:
                    if isinstance(self.current_subscription.end_date, str):
                        end_date = datetime.strptime(self.current_subscription.end_date, "%Y-%m-%d")
                    else:
                        end_date = self.current_subscription.end_date

                    self.ui.DayEndLable.setText(str(end_date.day))
                    self.ui.MonthEndLabel.setText(str(end_date.month))
                    self.ui.YearEndLabel.setText(str(end_date.year))

                if self.current_subscription.price:
                    self.ui.PriceLabel.setText(f"{self.current_subscription.price} руб.")

                self.ui.DeleteSubBtn.setEnabled(True)
            else:
                # Очищаем поля если абонемента нет
                self.ui.id_subsrciption.clear()
                self.ui.Day_subEdit.clear()
                self.ui.Month_subEdit.clear()
                self.ui.Year_subEdit.clear()
                self.ui.LongTimeComboBox.setCurrentIndex(0)
                self.ui.DayEndLable.clear()
                self.ui.MonthEndLabel.clear()
                self.ui.YearEndLabel.clear()
                self.ui.PriceLabel.clear()
                self.ui.DeleteSubBtn.setEnabled(False)

        except Exception as e:
            print(f"Ошибка загрузки данных абонемента: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные абонемента: {str(e)}")

    def load_trainings_data(self):
        """Загрузка данных тренировок"""
        if not self.current_client:
            return

        try:
            # Загружаем персональные тренировки
            personal_trainings = self.current_client.get_personal_trainings()
            self.ui.PersonalTrainingTabWidget.setRowCount(0)

            if personal_trainings:
                for row_num, training in enumerate(personal_trainings):
                    self.ui.PersonalTrainingTabWidget.insertRow(row_num)

                    # Дата
                    date = training[1]
                    if isinstance(date, str):
                        date_str = date
                    else:
                        date_str = date.strftime("%d.%m.%Y")

                    item_date = QTableWidgetItem(date_str)
                    item_date.setFlags(item_date.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Время
                    time = training[2]
                    if isinstance(time, str):
                        time_str = time
                    else:
                        time_str = time.strftime("%H:%M")

                    item_time = QTableWidgetItem(time_str)
                    item_time.setFlags(item_time.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Тренер
                    trainer_name = f"{training[3]} {training[4]}"
                    if training[5]:
                        trainer_name += f" {training[5]}"

                    item_trainer = QTableWidgetItem(trainer_name)
                    item_trainer.setFlags(item_trainer.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.ui.PersonalTrainingTabWidget.setItem(row_num, 0, item_date)
                    self.ui.PersonalTrainingTabWidget.setItem(row_num, 1, item_time)
                    self.ui.PersonalTrainingTabWidget.setItem(row_num, 2, item_trainer)

            # Загружаем групповые тренировки
            group_trainings = self.current_client.get_group_trainings()
            self.ui.GroupTrainingTabWidget.setRowCount(0)

            if group_trainings:
                for row_num, training in enumerate(group_trainings):
                    self.ui.GroupTrainingTabWidget.insertRow(row_num)

                    # Дата
                    date = training[1]
                    if isinstance(date, str):
                        date_str = date
                    else:
                        date_str = date.strftime("%d.%m.%Y")

                    item_date = QTableWidgetItem(date_str)
                    item_date.setFlags(item_date.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Время
                    time = training[2]
                    if isinstance(time, str):
                        time_str = time
                    else:
                        time_str = time.strftime("%H:%M")

                    item_time = QTableWidgetItem(time_str)
                    item_time.setFlags(item_time.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Тренер
                    trainer_name = f"{training[4]} {training[5]}"
                    if training[6]:
                        trainer_name += f" {training[6]}"

                    item_trainer = QTableWidgetItem(trainer_name)
                    item_trainer.setFlags(item_trainer.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.ui.GroupTrainingTabWidget.setItem(row_num, 0, item_date)
                    self.ui.GroupTrainingTabWidget.setItem(row_num, 1, item_time)
                    self.ui.GroupTrainingTabWidget.setItem(row_num, 2, item_trainer)

        except Exception as e:
            print(f"Ошибка загрузки данных тренировок: {e}")

    def calculate_end_date(self):
        """Расчет даты окончания абонемента и цены"""
        try:
            # Получаем данные из полей
            day = self.ui.Day_subEdit.text().strip()
            month = self.ui.Month_subEdit.text().strip()
            year = self.ui.Year_subEdit.text().strip()
            duration_days = self.ui.LongTimeComboBox.currentData()

            # Проверяем, что все поля заполнены
            if not (day and month and year and duration_days):
                self.ui.DayEndLable.clear()
                self.ui.MonthEndLabel.clear()
                self.ui.YearEndLabel.clear()
                self.ui.PriceLabel.clear()
                return

            # Преобразуем в числа
            day = int(day)
            month = int(month)
            year = int(year)

            # Проверяем корректность даты
            try:
                start_date = datetime(year, month, day)
            except ValueError:
                # Некорректная дата
                self.ui.DayEndLable.clear()
                self.ui.MonthEndLabel.clear()
                self.ui.YearEndLabel.clear()
                self.ui.PriceLabel.clear()
                return

            # Рассчитываем дату окончания
            end_date = start_date + timedelta(days=duration_days)

            # Отображаем дату окончания
            self.ui.DayEndLable.setText(str(end_date.day))
            self.ui.MonthEndLabel.setText(str(end_date.month))
            self.ui.YearEndLabel.setText(str(end_date.year))

            # Рассчитываем цену (БЕЗ СКИДОК)
            # Базовая цена: 2000 руб. за 30 дней
            price_per_day = 2000 / 30
            price = int(price_per_day * duration_days)

            self.ui.PriceLabel.setText(f"{price} руб.")

        except Exception as e:
            print(f"Ошибка расчета даты окончания: {e}")
            self.ui.DayEndLable.clear()
            self.ui.MonthEndLabel.clear()
            self.ui.YearEndLabel.clear()
            self.ui.PriceLabel.clear()

    def save_client(self):
        """Сохранение/обновление клиента"""
        try:
            # Получаем данные из формы
            last_name = self.ui.Last_nameEdit.text().strip()
            first_name = self.ui.First_nameEdit.text().strip()
            middle_name = self.ui.Midle_nameEdit.text().strip()
            phone = self.ui.PhoneEdit.text().strip()
            email = self.ui.EmailEdit.text().strip()

            # Валидация
            if not last_name:
                QMessageBox.warning(self, "Ошибка", "Введите фамилию клиента!")
                self.ui.Last_nameEdit.setFocus()
                return

            if not first_name:
                QMessageBox.warning(self, "Ошибка", "Введите имя клиента!")
                self.ui.First_nameEdit.setFocus()
                return

            if not phone:
                QMessageBox.warning(self, "Ошибка", "Введите телефон клиента!")
                self.ui.PhoneEdit.setFocus()
                return

            if self.current_client:  # Редактирование существующего клиента
                self.current_client.last_name = last_name
                self.current_client.first_name = first_name
                self.current_client.middle_name = middle_name
                self.current_client.phone = phone
                self.current_client.email = email

                # Обновляем фото, если было выбрано новое
                if self.current_photo_data:
                    self.current_client.photo = self.current_photo_data

                if self.current_client.save():
                    QMessageBox.information(self, "Успех", "Данные клиента успешно обновлены!")
                    self.enable_subscription_and_training_tabs()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить данные клиента")

            else:  # Добавление нового клиента
                # Создаем нового клиента
                new_client = Client(
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    phone=phone,
                    email=email,
                    is_active=True
                )

                # Добавляем фото, если оно было загружено
                if self.current_photo_data:
                    new_client.photo = self.current_photo_data

                if new_client.save():
                    # Генерируем номер карты
                    new_client.card_number = f"C{new_client.client_id:06d}"
                    new_client.save()  # Сохраняем номер карты
                    self.current_client = new_client
                    QMessageBox.information(self, "Успех", "Клиент успешно добавлен!")
                    self.enable_subscription_and_training_tabs()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить клиента")

            # Обновляем таблицу и сбрасываем форму
            self.load_clients()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные клиента: {str(e)}")

    def save_subscription(self):
        """Сохранение/обновление абонемента"""
        if not self.current_client:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите или создайте клиента!")
            return

        try:
            # Получаем данные из формы
            day = self.ui.Day_subEdit.text().strip()
            month = self.ui.Month_subEdit.text().strip()
            year = self.ui.Year_subEdit.text().strip()
            duration_days = self.ui.LongTimeComboBox.currentData()

            # Валидация
            if not (day and month and year):
                QMessageBox.warning(self, "Ошибка", "Заполните дату оформления абонемента!")
                return

            if not duration_days:
                QMessageBox.warning(self, "Ошибка", "Выберите продолжительность абонемента!")
                return

            # Преобразуем дату
            try:
                start_date = datetime(int(year), int(month), int(day))
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Некорректная дата оформления!")
                return

            # Проверяем, что дата не в прошлом
            if start_date.date() < datetime.now().date():
                QMessageBox.warning(self, "Ошибка", "Дата оформления не может быть в прошлом!")
                return

            # Рассчитываем дату окончания и цену
            end_date = start_date + timedelta(days=duration_days)
            price_per_day = 2000 / 30
            price = int(price_per_day * duration_days)

            if self.current_subscription:  # Обновление существующего абонемента
                self.current_subscription.start_date = start_date
                self.current_subscription.duration_days = duration_days
                self.current_subscription.end_date = end_date
                self.current_subscription.price = price

                if self.current_subscription.save():
                    QMessageBox.information(self, "Успех", "Абонемент успешно обновлен!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить абонемент")

            else:  # Создание нового абонемента
                new_subscription = Subscription(
                    client_id=self.current_client.client_id,
                    start_date=start_date,
                    duration_days=duration_days,
                    end_date=end_date,
                    price=price
                )

                if new_subscription.save():
                    QMessageBox.information(self, "Успех", "Абонемент успешно оформлен!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось оформить абонемент")

            # Обновляем данные абонемента
            self.load_subscription_data()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить абонемент: {str(e)}")

    def delete_client(self):
        """Удаление текущего клиента"""
        if not self.current_client:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного клиента для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить клиента '{self.current_client.get_full_name()}'?\n"
            "Все связанные данные (абонементы, тренировки) также будут удалены!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_client.delete():
                    QMessageBox.information(self, "Успех", "Клиент удален!")

                    # Обновляем таблицу и сбрасываем форму
                    self.load_clients()
                    self.reset_form()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить клиента")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить клиента: {str(e)}")

    def delete_subscription(self):
        """Удаление текущего абонемента"""
        if not self.current_subscription:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного абонемента для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить абонемент?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_subscription.delete():
                    QMessageBox.information(self, "Успех", "Абонемент удален!")

                    # Обновляем данные абонемента
                    self.load_subscription_data()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить абонемент")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить абонемент: {str(e)}")

    def on_search_last_name_changed(self, text):
        """Обработчик изменения поля поиска по фамилии"""
        if text.strip():
            self.search_clients_by_last_name(text.strip())
        else:
            self.load_clients()  # Если поле пустое, показываем всех
            self.hide_edit_panel()

    def on_search_phone_changed(self, text):
        """Обработчик изменения поля поиска по телефону"""
        if text.strip():
            self.search_clients_by_phone(text.strip())
        else:
            self.load_clients()  # Если поле пустое, показываем всех
            self.reset_form()

    def search_clients_by_last_name(self, last_name):
        """Поиск клиентов по фамилии"""
        try:
            self.ui.ClientsTabWidget.setRowCount(0)

            # Используем метод поиска модели Client
            clients = Client.search_by_last_name(last_name)

            if clients:
                for row_num, client in enumerate(clients):
                    self.ui.ClientsTabWidget.insertRow(row_num)

                    item_last_name = QTableWidgetItem(str(client.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, client.client_id)

                    item_first_name = QTableWidgetItem(str(client.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(client.middle_name) if client.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(client.phone) if client.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_card = QTableWidgetItem(str(client.card_number) if client.card_number else "")
                    item_card.setFlags(item_card.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_active = QTableWidgetItem("✓" if client.is_active else "✗")
                    item_active.setFlags(item_active.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.ui.ClientsTabWidget.setItem(row_num, 0, item_last_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 1, item_first_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 3, item_phone)
                    self.ui.ClientsTabWidget.setItem(row_num, 4, item_card)
                    self.ui.ClientsTabWidget.setItem(row_num, 5, item_active)

        except Exception as e:
            print(f"Ошибка поиска клиентов: {e}")

    def search_clients_by_phone(self, phone):
        """Поиск клиентов по телефону"""
        try:
            self.ui.ClientsTabWidget.setRowCount(0)

            # Используем метод поиска модели Client
            clients = Client.search_by_phone(phone)

            if clients:
                for row_num, client in enumerate(clients):
                    self.ui.ClientsTabWidget.insertRow(row_num)

                    item_last_name = QTableWidgetItem(str(client.last_name))
                    item_last_name.setFlags(item_last_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_last_name.setData(Qt.ItemDataRole.UserRole, client.client_id)

                    item_first_name = QTableWidgetItem(str(client.first_name))
                    item_first_name.setFlags(item_first_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_middle_name = QTableWidgetItem(str(client.middle_name) if client.middle_name else "")
                    item_middle_name.setFlags(item_middle_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(client.phone) if client.phone else "")
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_card = QTableWidgetItem(str(client.card_number) if client.card_number else "")
                    item_card.setFlags(item_card.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_active = QTableWidgetItem("✓" if client.is_active else "✗")
                    item_active.setFlags(item_active.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.ui.ClientsTabWidget.setItem(row_num, 0, item_last_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 1, item_first_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 2, item_middle_name)
                    self.ui.ClientsTabWidget.setItem(row_num, 3, item_phone)
                    self.ui.ClientsTabWidget.setItem(row_num, 4, item_card)
                    self.ui.ClientsTabWidget.setItem(row_num, 5, item_active)

        except Exception as e:
            print(f"Ошибка поиска клиентов: {e}")

    # Методы навигации
    def open_personal_training(self):
        """Открыть окно записи на персональную тренировку"""
        QMessageBox.information(self, "В разработке", "Запись на персональную тренировку в разработке")

    def open_group_training(self):
        """Открыть окно записи на групповую тренировку"""
        QMessageBox.information(self, "В разработке", "Запись на групповую тренировку в разработке")

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

    def on_clients_clicked(self):
        """Обработчик кнопки 'Клиенты'"""
        pass

    def open_trainers(self):
        """Открыть окно тренеров"""
        try:
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
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt

from src.ui.service_window import Ui_ServiceForm
from src.models.services import Service
from src.models.halls import Hall



class ServiceForm(QMainWindow):
    """Главное окно приложения - Услуги"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_ServiceForm()
        self.ui.setupUi(self)

        # Данные пользователя
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Текущая редактируемая услуга
        self.current_service = None

        # Словарь цветов для залов
        self.hall_colors = self.create_hall_colors()

        # Устанавливаем заголовок окна
        self.setWindowTitle("Фитнес-Менеджер - Услуги")

        # Настраиваем интерфейс
        self.setup_interface()

        # Загружаем данные
        self.load_halls()  # Загружаем залы в ComboBox
        self.load_services()  # Загружаем услуги в таблицу

        # Подключаем кнопки
        self.connect_buttons()

        # Скрываем правую панель при запуске
        self.hide_edit_panel()

        # Сбрасываем форму добавления/редактирования
        self.reset_form()

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

    def setup_interface(self):
        """Настройка интерфейса"""
        # Настраиваем таблицу
        self.ui.TableService.setColumnWidth(0, 200)  # Вид услуги
        self.ui.TableService.setColumnWidth(1, 150)  # Зал
        self.ui.TableService.setColumnWidth(2, 150)  # Макс. человек
        self.ui.TableService.setColumnWidth(3, 120)  # Стоимость

        # Разрешаем выделение строк
        self.ui.TableService.setSelectionBehavior(
            self.ui.TableService.SelectionBehavior.SelectRows
        )

        # Отключаем редактирование ячеек
        self.ui.TableService.setEditTriggers(
            self.ui.TableService.EditTrigger.NoEditTriggers
        )

        # Подключаем двойной клик по таблице
        self.ui.TableService.doubleClicked.connect(self.on_table_double_click)

        # Подключаем одиночный клик по таблице
        self.ui.TableService.itemClicked.connect(self.on_table_item_clicked)

    def show_edit_panel(self):
        """Показать правую панель для добавления/редактирования"""
        self.ui.widget_2.setVisible(True)

    def hide_edit_panel(self):
        """Скрыть правую панель для добавления/редактирования"""
        self.ui.widget_2.setVisible(False)

    def make_table_readonly(self):
        """Делает таблицу полностью нередактируемой"""
        for row in range(self.ui.TableService.rowCount()):
            for col in range(self.ui.TableService.columnCount()):
                item = self.ui.TableService.item(row, col)
                if item:
                    current_flags = item.flags()
                    new_flags = current_flags & ~Qt.ItemFlag.ItemIsEditable
                    item.setFlags(new_flags)

    def load_halls(self):
        """Загрузка списка залов из БД в ComboBox через модель"""
        try:
            self.ui.HallComboBox.clear()
            self.ui.HallComboBox.addItem("Выберите зал", None)

            # Используем модель Hall для получения данных
            halls = Hall.get_all()

            if halls:
                for hall in halls:
                    self.ui.HallComboBox.addItem(hall.hall_name, hall.hall_id)

        except Exception as e:
            print(f"Ошибка загрузки залов: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список залов: {str(e)}")

    def load_services(self):
        """Загрузка услуг из БД в таблицу через модель"""
        try:
            self.ui.TableService.setRowCount(0)

            # Используем модель Service для получения данных
            services = Service.get_all()

            if services:
                for row_num, service in enumerate(services):
                    self.ui.TableService.insertRow(row_num)

                    # Получаем информацию о зале для отображения
                    hall_info = ""
                    hall_capacity = ""

                    if service.hall_id:
                        hall = Hall.get_by_id(service.hall_id)
                        if hall:
                            hall_info = hall.hall_name
                            hall_capacity = str(hall.capacity)

                    # Создаем ячейки ТОЛЬКО ДЛЯ ЧТЕНИЯ
                    item_name = QTableWidgetItem(str(service.service_name))
                    item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_name.setData(Qt.ItemDataRole.UserRole, service.service_id)

                    item_hall = QTableWidgetItem(hall_info if hall_info else "Не указан")
                    item_hall.setFlags(item_hall.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_capacity = QTableWidgetItem(hall_capacity if hall_capacity else "Не указана")
                    item_capacity.setFlags(item_capacity.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_price = QTableWidgetItem(str(service.price) if service.price else "Не указана")
                    item_price.setFlags(item_price.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Устанавливаем ячейки
                    self.ui.TableService.setItem(row_num, 0, item_name)
                    self.ui.TableService.setItem(row_num, 1, item_hall)
                    self.ui.TableService.setItem(row_num, 2, item_capacity)
                    self.ui.TableService.setItem(row_num, 3, item_price)

            self.make_table_readonly()

        except Exception as e:
            print(f"Ошибка загрузки услуг: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить услуги: {str(e)}")

    def connect_buttons(self):
        """Подключение обработчиков кнопок"""
        # Кнопка "Добавить"
        self.ui.AddServiceBtn.clicked.connect(self.add_service)

        # Кнопка "Сохранить"
        self.ui.SaveServiceBtn.clicked.connect(self.save_service)

        # Кнопка "Удалить"
        self.ui.DeleteServiceBtn.clicked.connect(self.delete_service)

        # Кнопка "Выход"
        self.ui.ExitBtn.clicked.connect(self.close)

        # Кнопки навигации
        self.ui.ServiceBtn.clicked.connect(self.on_services_clicked)
        self.ui.ScheduleBtn.clicked.connect(self.on_schedule_clicked)
        self.ui.ClientsBtn.clicked.connect(self.on_clients_clicked)
        self.ui.TrainerBtn.clicked.connect(self.on_trainers_clicked)
        self.ui.HallBtn.clicked.connect(self.on_halls_clicked)
        self.ui.ReportBtn.clicked.connect(self.on_reports_clicked)

        # Делаем кнопку "Услуги" неактивной
        self.ui.ServiceBtn.setEnabled(False)

        # Подключаем изменение выбранного зала
        self.ui.HallComboBox.currentIndexChanged.connect(self.on_hall_changed)

    def reset_form(self):
        """Сброс формы добавления/редактирования"""
        self.current_service = None
        self.ui.TypeServiceEdit.clear()
        self.ui.HallComboBox.setCurrentIndex(0)
        self.ui.PriceEdit.clear()
        self.ui.label_MaxE.clear()
        self.ui.labelColorE.clear()
        self.ui.labelColorE.setStyleSheet("")
        self.ui.SaveServiceBtn.setText("Сохранить")
        self.ui.DeleteServiceBtn.setEnabled(False)
        self.ui.AddServiceBtn.setEnabled(True)

    def on_hall_changed(self, index):
        """Обработчик изменения выбранного зала"""
        if index > 0:  # index 0 это "Выберите зал"
            hall_id = self.ui.HallComboBox.currentData()
            if hall_id:
                try:
                    # Используем модель Hall для получения данных
                    hall = Hall.get_by_id(hall_id)

                    if hall:
                        self.ui.label_MaxE.setText(str(hall.capacity))

                        # Устанавливаем цвет из словаря
                        if hall.hall_id in self.hall_colors:
                            color = self.hall_colors[hall.hall_id]
                            self.ui.labelColorE.setText(color)
                            self.ui.labelColorE.setStyleSheet(
                                f"background-color: {color}; border: 1px solid #000;"
                            )
                        else:
                            default_color = "#FFFFFF"
                            self.ui.labelColorE.setText(default_color)
                            self.ui.labelColorE.setStyleSheet(
                                f"background-color: {default_color}; border: 1px solid #000;"
                            )
                    else:
                        self.ui.label_MaxE.clear()
                        self.ui.labelColorE.clear()
                        self.ui.labelColorE.setStyleSheet("")

                except Exception as e:
                    print(f"Ошибка получения данных зала: {e}")
                    self.ui.label_MaxE.clear()
                    self.ui.labelColorE.clear()
                    self.ui.labelColorE.setStyleSheet("")
        else:
            self.ui.label_MaxE.clear()
            self.ui.labelColorE.clear()
            self.ui.labelColorE.setStyleSheet("")

    def add_service(self):
        """Кнопка 'Добавить' - сброс формы для новой услуги"""
        self.show_edit_panel()
        self.reset_form()
        self.ui.TypeServiceEdit.setFocus()

    def get_selected_service_id(self):
        """Получение ID выбранной услуги из таблицы"""
        selected_row = self.ui.TableService.currentRow()
        if selected_row >= 0:
            item = self.ui.TableService.item(selected_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def on_table_double_click(self, index):
        """Обработка двойного клика по таблице - редактирование"""
        service_id = self.get_selected_service_id()
        if service_id:
            self.edit_service(service_id)

    def on_table_item_clicked(self, item):
        """Обработка клика по элементу таблицы"""
        service_id = self.get_selected_service_id()
        if service_id:
            self.edit_service(service_id)

    def edit_service(self, service_id=None):
        """Редактирование выбранной услуги"""
        if not service_id:
            service_id = self.get_selected_service_id()

        if service_id:
            try:
                # Используем модель Service для загрузки данных
                self.current_service = Service.get_by_id(service_id)

                if self.current_service:
                    # Показываем панель редактирования
                    self.show_edit_panel()

                    # Заполняем форму
                    self.ui.TypeServiceEdit.setText(self.current_service.service_name)
                    self.ui.PriceEdit.setText(str(self.current_service.price))

                    # Устанавливаем выбранный зал
                    if self.current_service.hall_id:
                        index = self.ui.HallComboBox.findData(self.current_service.hall_id)
                        if index >= 0:
                            self.ui.HallComboBox.setCurrentIndex(index)

                    # Активируем кнопку удаления
                    self.ui.DeleteServiceBtn.setEnabled(True)
                    self.ui.SaveServiceBtn.setText("Обновить")
                    self.ui.AddServiceBtn.setEnabled(False)
                else:
                    QMessageBox.warning(self, "Ошибка", "Услуга не найдена!")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные услуги: {str(e)}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу для редактирования")

    def save_service(self):
        """Сохранение/обновление услуги через модель"""
        try:
            # Получаем данные из формы
            name = self.ui.TypeServiceEdit.text().strip()
            price_text = self.ui.PriceEdit.text().strip()
            hall_id = self.ui.HallComboBox.currentData()

            # Валидация
            if not name:
                QMessageBox.warning(self, "Ошибка", "Введите название услуги!")
                self.ui.TypeServiceEdit.setFocus()
                return

            if not hall_id:
                QMessageBox.warning(self, "Ошибка", "Выберите зал!")
                return

            # Валидация цены
            if not price_text:
                QMessageBox.warning(self, "Ошибка", "Введите стоимость услуги!")
                self.ui.PriceEdit.setFocus()
                return

            try:
                price = int(price_text)
                if price <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Стоимость должна быть положительным числом!")
                self.ui.PriceEdit.setFocus()
                return

            if self.current_service:  # Редактирование существующей услуги
                self.current_service.service_name = name
                self.current_service.price = price
                self.current_service.hall_id = hall_id

                if self.current_service.save():
                    QMessageBox.information(self, "Успех", "Услуга успешно обновлена!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить услугу")

            else:  # Добавление новой услуги
                new_service = Service(
                    service_name=name,
                    price=price,
                    hall_id=hall_id
                )

                if new_service.save():
                    QMessageBox.information(self, "Успех", "Услуга успешно добавлена!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить услугу")

            # Обновляем таблицу и скрываем панель
            self.load_services()
            self.hide_edit_panel()
            self.reset_form()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить услугу: {str(e)}")

    def delete_service(self):
        """Удаление текущей услуги через модель"""
        if not self.current_service:
            QMessageBox.warning(self, "Ошибка", "Нет выбранной услуги для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить услугу '{self.current_service.service_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_service.delete():
                    QMessageBox.information(self, "Успех", "Услуга удалена!")

                    # Обновляем таблицу и скрываем панель
                    self.load_services()
                    self.hide_edit_panel()
                    self.reset_form()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось удалить услугу")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить услугу: {str(e)}")

    # Методы навигации (остаются без изменений)
    def on_services_clicked(self):
        pass

    def on_reports_clicked(self):
        pass

    def on_clients_clicked(self):
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
            from src.views.trainer_window import TrainerWindow  # <-- Импорт внутри метода
            self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
            self.trainer_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта TrainerWindow: {e}")
            QMessageBox.warning(self, "В разработке", "Окно тренеров находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна тренеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно тренеров: {str(e)}")

    def on_trainers_clicked(self):
        """Обработчик кнопки 'Тренеры'"""
        self.open_trainers()  # Вызываем метод

    def open_halls(self):
        """Открыть окно залов"""
        try:
            from src.views.hall_window import HallWindow  # <-- Импорт внутри метода
            self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
            self.hall_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта HallWindow: {e}")
            QMessageBox.warning(self, "В разработке", "Окно залов находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна залов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно залов: {str(e)}")

    def on_halls_clicked(self):
        """Обработчик кнопки 'Залы'"""
        self.open_halls()  # Вызываем метод

    def open_schedule(self):
        """Открыть окно расписания"""
        try:
            from src.views.schedule_window import ScheduleWindow  # <-- Импорт внутри метода
            self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
            self.schedule_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта ScheduleWindow: {e}")
            QMessageBox.warning(self, "В разработке", "Окно расписания находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна расписания: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно расписания: {str(e)}")

    def on_schedule_clicked(self):
        """Обработчик кнопки 'Расписание'"""
        self.open_schedule()  # Вызываем метод


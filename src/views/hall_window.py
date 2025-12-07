import sys
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QApplication
from PyQt6.QtCore import Qt

from src.ui.hall_window import Ui_HallForm
from src.models.halls import Hall


class HallWindow(QMainWindow):
    """Окно управления залами"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_HallForm()
        self.ui.setupUi(self)

        # Данные пользователя
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # Текущий редактируемый зал
        self.current_hall = None

        # Устанавливаем заголовок окна
        self.setWindowTitle("Фитнес-Менеджер - Залы")

        # Настраиваем интерфейс
        self.setup_interface()

        # Загружаем данные
        self.load_halls()

        # Подключаем кнопки
        self.connect_buttons()

        # Делаем кнопку "Залы" неактивной (мы уже в этом разделе)
        self.ui.HallButton.setEnabled(False)

    def setup_interface(self):
        """Настройка интерфейса"""
        # Настраиваем таблицу
        self.ui.HallTableWidget.setColumnWidth(0, 230)  # Название зала
        self.ui.HallTableWidget.setColumnWidth(1, 230)  # Вместимость

        # Разрешаем редактирование ячеек напрямую в таблице
        self.ui.HallTableWidget.setEditTriggers(
            self.ui.HallTableWidget.EditTrigger.DoubleClicked |
            self.ui.HallTableWidget.EditTrigger.SelectedClicked
        )

        # Подключаем обработчик изменения данных в таблице
        self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)

    def load_halls(self):
        """Загрузка залов из БД в таблицу через модель"""
        try:
            print("Начало загрузки залов...")

            # Отключаем сигнал itemChanged на время загрузки
            try:
                self.ui.HallTableWidget.itemChanged.disconnect(self.on_table_item_changed)
                print("Сигнал itemChanged отключен")
            except Exception as e:
                print(f"Не удалось отключить сигнал: {e}")

            # Используем модель Hall для получения данных
            halls = Hall.get_all()

            print(f"Получено записей: {len(halls) if halls else 0}")

            # Очищаем все строки (у нас фиксированно 20 строк)
            for row in range(20):
                # Создаем пустые ячейки
                item_name = QTableWidgetItem("")
                item_capacity = QTableWidgetItem("")

                # Устанавливаем данные
                item_name.setData(Qt.ItemDataRole.UserRole, None)
                item_capacity.setData(Qt.ItemDataRole.UserRole, None)

                # Устанавливаем ячейки
                self.ui.HallTableWidget.setItem(row, 0, item_name)
                self.ui.HallTableWidget.setItem(row, 1, item_capacity)

            if halls:
                # Заполняем первые N строк данными из БД
                for row_num, hall in enumerate(halls):
                    if row_num >= 20:  # Не превышаем лимит строк
                        break

                    print(
                        f"Загружаем зал {row_num}: id={hall.hall_id}, name={hall.hall_name}, capacity={hall.capacity}")

                    # Создаем ячейки
                    item_name = QTableWidgetItem(str(hall.hall_name))
                    item_name.setData(Qt.ItemDataRole.UserRole, hall.hall_id)

                    item_capacity = QTableWidgetItem(str(hall.capacity))
                    item_capacity.setData(Qt.ItemDataRole.UserRole, hall.hall_id)

                    # Устанавливаем ячейки
                    self.ui.HallTableWidget.setItem(row_num, 0, item_name)
                    self.ui.HallTableWidget.setItem(row_num, 1, item_capacity)

            # Включаем сигнал обратно
            try:
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                print("Сигнал itemChanged подключен")
            except Exception as e:
                print(f"Ошибка подключения сигнала: {e}")

            print("Загрузка залов завершена")

        except Exception as e:
            print(f"Критическая ошибка загрузки залов: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить залы: {str(e)}")

    def on_table_item_changed(self, item):
        """Обработчик изменения данных в таблице"""
        print(f"\n=== Изменение ячейки: row={item.row()}, col={item.column()}, text='{item.text()}' ===")

        # Отключаем сигнал на время обработки
        try:
            self.ui.HallTableWidget.itemChanged.disconnect(self.on_table_item_changed)
            print("Сигнал отключен для обработки")
        except:
            pass

        try:
            row = item.row()

            # Получаем данные из строки
            hall_name_item = self.ui.HallTableWidget.item(row, 0)
            capacity_item = self.ui.HallTableWidget.item(row, 1)

            if not hall_name_item or not capacity_item:
                print("Ошибка: одна из ячеек пуста")
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                return

            hall_name = hall_name_item.text().strip()
            capacity_text = capacity_item.text().strip()
            hall_id = hall_name_item.data(Qt.ItemDataRole.UserRole)

            print(f"Данные: name='{hall_name}', capacity='{capacity_text}', id={hall_id}")

            # Если оба поля пустые, ничего не делаем
            if not hall_name and not capacity_text:
                print("Оба поля пустые, пропускаем")
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                return

            # Проверяем, что оба поля заполнены
            if not hall_name:
                QMessageBox.warning(self, "Ошибка", "Название зала не может быть пустым!")
                hall_name_item.setText("")
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                return

            if not capacity_text:
                QMessageBox.warning(self, "Ошибка", "Вместимость не может быть пустой!")
                capacity_item.setText("")
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                return

            # Проверяем вместимость
            try:
                capacity = int(capacity_text)
                if capacity <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите положительное число для вместимости!")
                capacity_item.setText("")
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                return

            # Определяем: добавление или обновление
            if hall_id is None:
                # ДОБАВЛЕНИЕ НОВОГО ЗАЛА
                print("Режим: добавление нового зала")

                # Проверяем уникальность названия через модель
                if Hall.check_name_exists(hall_name):
                    print(f"Зал '{hall_name}' уже существует")
                    QMessageBox.warning(self, "Ошибка", f"Зал с названием '{hall_name}' уже существует!")
                    hall_name_item.setText("")
                    self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                    return

                # Создаем новый объект Hall
                new_hall = Hall(hall_name=hall_name, capacity=capacity)

                # Сохраняем через модель
                if new_hall.save():
                    print(f"Добавлен зал с ID: {new_hall.hall_id}")

                    # Обновляем данные в ячейках
                    hall_name_item.setData(Qt.ItemDataRole.UserRole, new_hall.hall_id)
                    capacity_item.setData(Qt.ItemDataRole.UserRole, new_hall.hall_id)

                    QMessageBox.information(self, "Успех", f"Зал '{hall_name}' успешно добавлен!")
                    print(f"Зал '{hall_name}' добавлен с ID {new_hall.hall_id}")
                else:
                    print("Не удалось добавить зал")
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить зал")

            else:
                # ОБНОВЛЕНИЕ СУЩЕСТВУЮЩЕГО ЗАЛА
                print(f"Режим: обновление зала id={hall_id}")

                # Загружаем текущий зал для проверки изменений
                current_hall = Hall.get_by_id(hall_id)

                if current_hall:
                    # Проверяем, изменилось ли название
                    if hall_name != current_hall.hall_name:
                        # Проверяем уникальность нового названия
                        if Hall.check_name_exists(hall_name, exclude_id=hall_id):
                            QMessageBox.warning(self, "Ошибка", f"Зал с названием '{hall_name}' уже существует!")

                            # Восстанавливаем старое название
                            hall_name_item.setText(current_hall.hall_name)

                            self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                            return

                # Создаем объект Hall с обновленными данными
                updated_hall = Hall(hall_id=hall_id, hall_name=hall_name, capacity=capacity)

                # Сохраняем через модель
                if updated_hall.save():
                    print(f"Обновлен зал ID: {hall_id}")
                    QMessageBox.information(self, "Успех", f"Зал '{hall_name}' успешно обновлен!")
                    print(f"Зал ID {hall_id} обновлен")
                else:
                    print("Не удалось обновить зал (возможно данные не изменились)")

            print("Обработка завершена успешно")

        except Exception as e:
            print(f"Ошибка при обработке изменения: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")

            # В случае ошибки перезагружаем данные из БД
            self.load_halls()
        finally:
            # Включаем сигнал обратно
            try:
                self.ui.HallTableWidget.itemChanged.connect(self.on_table_item_changed)
                print("Сигнал подключен обратно")
            except Exception as e:
                print(f"Ошибка подключения сигнала: {e}")

    def connect_buttons(self):
        """Подключение обработчиков кнопок"""
        # Кнопки навигации
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.ClientsButton.clicked.connect(self.open_clients)
        self.ui.TrainerButton.clicked.connect(self.open_trainers)
        self.ui.HallButton.clicked.connect(self.on_halls_clicked)
        self.ui.ReportButton.clicked.connect(self.open_reports)
        self.ui.ExitButton.clicked.connect(self.close)

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
        QMessageBox.information(self, "В разработке", "Окно расписания находится в разработке")

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
        """Обработчик кнопки 'Тренеры'"""
        try:
            from src.views.trainer_window import TrainerWindow
            self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
            self.trainer_window.show()
            self.close()
        except ImportError as e:
            print(f"Ошибка импорта TrainerWindow: {e}")
            QMessageBox.warning(self, "В разработке", "Окно тренеров находится в разработке")
        except Exception as e:
            print(f"Ошибка открытия окна тренеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно тренеров: {str(e)}")

    def on_halls_clicked(self):
        """Обработчик кнопки 'Залы' (уже в залах)"""
        pass

    def open_reports(self):
        """Открыть окно отчетов"""
        QMessageBox.information(self, "В разработке", "Окно отчетов находится в разработке")


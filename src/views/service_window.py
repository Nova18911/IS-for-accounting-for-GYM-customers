from typing import Optional

# src/views/service_window.py
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt

from src.ui.service_window import Ui_ServiceForm
from src.models import services as service_model
from src.models.halls import Hall


class ServiceForm(QMainWindow):
    """Окно управления услугами (упрощённая версия)"""

    HALL_COLOR_MAP = {
        1: "#FFB6C1", 2: "#87CEFA", 3: "#98FB98", 4: "#DDA0DD", 5: "#FFD700",
        6: "#F0E68C", 7: "#ADD8E6", 8: "#90EE90", 9: "#FFA07A", 10: "#20B2AA",
        11: "#B0C4DE", 12: "#FFDEAD", 13: "#AFEEEE", 14: "#E6E6FA", 15: "#FFF0F5",
        16: "#F5FFFA", 17: "#FFFACD", 18: "#FAFAD2", 19: "#F0FFF0", 20: "#F5F5DC",
    }

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_ServiceForm()
        self.ui.setupUi(self)

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        self.current_service_id = None

        self.setWindowTitle("Фитнес-Менеджер - Услуги")
        self.setup_interface()
        self.load_halls()
        self.load_services()
        self.connect_buttons()
        self.hide_edit_panel()
        self.reset_form()

    # ---------------- UI / INIT ----------------

    def setup_interface(self):
        self.ui.TableService.setColumnWidth(0, 200)
        self.ui.TableService.setColumnWidth(1, 150)
        self.ui.TableService.setColumnWidth(2, 150)
        self.ui.TableService.setColumnWidth(3, 120)

        self.ui.TableService.setSelectionBehavior(self.ui.TableService.SelectionBehavior.SelectRows)
        self.ui.TableService.setEditTriggers(self.ui.TableService.EditTrigger.NoEditTriggers)
        self.ui.TableService.doubleClicked.connect(lambda idx: self.edit_selected_service())
        self.ui.TableService.itemClicked.connect(lambda item: self.edit_selected_service())

    def connect_buttons(self):
        self.ui.AddServiceBtn.clicked.connect(self.add_service)
        self.ui.SaveServiceBtn.clicked.connect(self.save_service)
        self.ui.DeleteServiceBtn.clicked.connect(self.delete_service)
        self.ui.ExitBtn.clicked.connect(self.close)

        self.ui.ServiceBtn.clicked.connect(lambda: None)
        self.ui.ScheduleBtn.clicked.connect(self.on_schedule_clicked)
        self.ui.ClientsBtn.clicked.connect(self.on_clients_clicked)
        self.ui.TrainerBtn.clicked.connect(self.on_trainers_clicked)
        self.ui.HallBtn.clicked.connect(self.on_halls_clicked)
        self.ui.ReportBtn.clicked.connect(self.on_reports_clicked)

        self.ui.ServiceBtn.setEnabled(False)
        self.ui.HallComboBox.currentIndexChanged.connect(self.on_hall_changed)

    # ---------------- Helpers ----------------

    def show_edit_panel(self):
        self.ui.widget_2.setVisible(True)

    def hide_edit_panel(self):
        self.ui.widget_2.setVisible(False)

    def reset_form(self):
        self.current_service_id = None
        self.ui.TypeServiceEdit.clear()
        self.ui.HallComboBox.setCurrentIndex(0)
        self.ui.PriceEdit.clear()
        self.ui.label_MaxE.clear()
        self.ui.labelColorE.clear()
        self.ui.labelColorE.setStyleSheet("")
        self.ui.SaveServiceBtn.setText("Сохранить")
        self.ui.DeleteServiceBtn.setEnabled(False)
        self.ui.AddServiceBtn.setEnabled(True)

    def make_table_readonly(self):
        for r in range(self.ui.TableService.rowCount()):
            for c in range(self.ui.TableService.columnCount()):
                itm = self.ui.TableService.item(r, c)
                if itm:
                    itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEditable)

    # ---------------- Loading ----------------

    def load_halls(self):
        """Заполнить ComboBox залов"""
        self.ui.HallComboBox.clear()
        self.ui.HallComboBox.addItem("Выберите зал", None)
        halls = Hall.get_all()
        for h in halls:
            self.ui.HallComboBox.addItem(h.hall_name, h.hall_id)

    def load_services(self):
        """Загрузить услуги в таблицу"""
        services = service_model.get_all_services()
        self.ui.TableService.setRowCount(0)

        for row_idx, svc in enumerate(services):
            self.ui.TableService.insertRow(row_idx)

            hall_name = ""
            hall_capacity = ""
            if svc["hall_id"]:
                hall = Hall.get_by_id(svc["hall_id"])
                if hall:
                    hall_name = hall.hall_name
                    hall_capacity = str(hall.capacity)

            item_name = QTableWidgetItem(svc["service_name"])
            item_name.setData(Qt.ItemDataRole.UserRole, svc["service_id"])
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_hall = QTableWidgetItem(hall_name or "Не указан")
            item_hall.setFlags(item_hall.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_capacity = QTableWidgetItem(hall_capacity or "Не указана")
            item_capacity.setFlags(item_capacity.flags() & ~Qt.ItemFlag.ItemIsEditable)

            item_price = QTableWidgetItem(str(svc["price"]) if svc["price"] is not None else "Не указана")
            item_price.setFlags(item_price.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.ui.TableService.setItem(row_idx, 0, item_name)
            self.ui.TableService.setItem(row_idx, 1, item_hall)
            self.ui.TableService.setItem(row_idx, 2, item_capacity)
            self.ui.TableService.setItem(row_idx, 3, item_price)

        self.make_table_readonly()

    # ---------------- Interaction ----------------

    def get_selected_service_id(self) -> Optional[int]:
        row = self.ui.TableService.currentRow()
        if row >= 0:
            itm = self.ui.TableService.item(row, 0)
            if itm:
                return itm.data(Qt.ItemDataRole.UserRole)
        return None

    def edit_selected_service(self):
        svc_id = self.get_selected_service_id()
        if not svc_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу для редактирования")
            return
        svc = service_model.get_service_by_id(svc_id)
        if not svc:
            QMessageBox.warning(self, "Ошибка", "Услуга не найдена")
            return

        self.current_service_id = svc_id
        self.show_edit_panel()
        self.ui.TypeServiceEdit.setText(svc["service_name"])
        self.ui.PriceEdit.setText(str(svc["price"]) if svc["price"] is not None else "")
        if svc["hall_id"]:
            idx = self.ui.HallComboBox.findData(svc["hall_id"])
            if idx >= 0:
                self.ui.HallComboBox.setCurrentIndex(idx)
        self.ui.DeleteServiceBtn.setEnabled(True)
        self.ui.SaveServiceBtn.setText("Обновить")
        self.ui.AddServiceBtn.setEnabled(False)

    def add_service(self):
        self.reset_form()
        self.show_edit_panel()
        self.ui.TypeServiceEdit.setFocus()

    def on_hall_changed(self, index):
        if index <= 0:
            self.ui.label_MaxE.clear()
            self.ui.labelColorE.clear()
            self.ui.labelColorE.setStyleSheet("")
            return

        hall_id = self.ui.HallComboBox.currentData()
        if not hall_id:
            self.ui.label_MaxE.clear()
            self.ui.labelColorE.clear()
            self.ui.labelColorE.setStyleSheet("")
            return

        hall = Hall.get_by_id(hall_id)
        if hall:
            self.ui.label_MaxE.setText(str(hall.capacity))
            color = self.HALL_COLOR_MAP.get(hall.hall_id, "#FFFFFF")
            self.ui.labelColorE.setText(color)
            self.ui.labelColorE.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")
        else:
            self.ui.label_MaxE.clear()
            self.ui.labelColorE.clear()
            self.ui.labelColorE.setStyleSheet("")

    def save_service(self):
        name = self.ui.TypeServiceEdit.text().strip()
        price_text = self.ui.PriceEdit.text().strip()
        hall_id = self.ui.HallComboBox.currentData()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название услуги!")
            self.ui.TypeServiceEdit.setFocus()
            return

        if not hall_id:
            QMessageBox.warning(self, "Ошибка", "Выберите зал!")
            return

        if not price_text:
            QMessageBox.warning(self, "Ошибка", "Введите стоимость услуги!")
            self.ui.PriceEdit.setFocus()
            return

        if not price_text.isdigit() or int(price_text) <= 0:
            QMessageBox.warning(self, "Ошибка", "Стоимость должна быть положительным числом!")
            self.ui.PriceEdit.setFocus()
            return

        price = int(price_text)

        # Проверка уникальности имени
        if self.current_service_id:
            if service_model.name_exists(name, exclude_id=self.current_service_id):
                QMessageBox.warning(self, "Ошибка", "Услуга с таким названием уже существует!")
                return
            service_model.update_service(self.current_service_id, name, price, hall_id)
            QMessageBox.information(self, "Успех", "Услуга успешно обновлена!")
        else:
            if service_model.name_exists(name):
                QMessageBox.warning(self, "Ошибка", "Услуга с таким названием уже существует!")
                return
            new_id = service_model.create_service(name, price, hall_id)
            if new_id is None:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить услугу")
                return
            # присвоим id (если нужно)
            self.current_service_id = new_id
            QMessageBox.information(self, "Успех", "Услуга успешно добавлена!")

        self.load_services()
        self.hide_edit_panel()
        self.reset_form()

    def delete_service(self):
        if not self.current_service_id:
            QMessageBox.warning(self, "Ошибка", "Нет выбранной услуги для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить услугу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success = service_model.delete_service(self.current_service_id)
        if success:
            QMessageBox.information(self, "Успех", "Услуга удалена!")
            self.load_services()
            self.hide_edit_panel()
            self.reset_form()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить услугу")

    # ---------------- Navigation stubs (оставил вызовы, без обработчиков ошибок) ----------------

    def on_services_clicked(self):
        pass

    def on_reports_clicked(self):
        pass

    def on_clients_clicked(self):
        from src.views.client_window import ClientWindow
        self.client_window = ClientWindow(self.user_id, self.user_email, self.user_role)
        self.client_window.show()
        self.close()

    def on_trainers_clicked(self):
        from src.views.trainer_window import TrainerWindow
        self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
        self.trainer_window.show()
        self.close()

    def on_halls_clicked(self):
        from src.views.hall_window import HallWindow
        self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
        self.hall_window.show()
        self.close()

    def on_schedule_clicked(self):
        from src.views.schedule_window import ScheduleWindow
        self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
        self.schedule_window.show()
        self.close()


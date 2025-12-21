from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from src.models import services as service_model
from src.models.halls import Hall


class ServicePageController:
    HALL_COLOR_MAP = {
        1: "#FFB6C1", 2: "#87CEFA", 3: "#98FB98", 4: "#DDA0DD", 5: "#FFD700",
        6: "#F0E68C", 7: "#ADD8E6", 8: "#90EE90", 9: "#FFA07A", 10: "#20B2AA",
        11: "#B0C4DE", 12: "#FFDEAD", 13: "#AFEEEE", 14: "#E6E6FA", 15: "#FFF0F5",
        16: "#F5FFFA", 17: "#FFFACD", 18: "#FAFAD2", 19: "#F0FFF0", 20: "#F5F5DC",
    }

    def __init__(self, ui):
        self.ui = ui
        self.current_service_id = None
        self.setup_interface()
        self.load_halls()
        self.load_services()

        self.ui.widget_service.setVisible(False)

    def setup_interface(self):
        table = self.ui.TableService
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 120)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.itemDoubleClicked.connect(lambda _: self.edit_selected_service())

        self.ui.AddServiceBtn.clicked.connect(self.add_new_service)
        self.ui.SaveServiceBtn.clicked.connect(self.save_service)
        self.ui.DeleteServiceBtn.clicked.connect(self.delete_service)
        self.ui.HallComboBox.currentIndexChanged.connect(self.on_hall_changed)
        self.ui.ScheduleButton.clicked.connect(lambda: None)
        self.ui.ClientsButton.clicked.connect(lambda: None)
        self.ui.TrainerButton.clicked.connect(lambda: None)
        self.ui.HallButton.clicked.connect(lambda: None)
        self.ui.ReportButton.clicked.connect(lambda: None)

    def reset_form(self):
        self.current_service_id = None
        self.ui.TypeServiceEdit.clear()
        self.ui.PriceEdit.clear()
        self.ui.HallComboBox.setCurrentIndex(0)
        self.ui.label_MaxE.clear()
        self.ui.labelColorE.clear()
        self.ui.labelColorE.setStyleSheet("")
        self.ui.SaveServiceBtn.setText("Сохранить")
        self.ui.DeleteServiceBtn.setEnabled(False)

    def make_table_readonly(self):
        table = self.ui.TableService
        for r in range(table.rowCount()):
            for c in range(table.columnCount()):
                itm = table.item(r, c)
                if itm:
                    itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def load_halls(self):
        self.ui.HallComboBox.clear()
        self.ui.HallComboBox.addItem("Выберите зал", None)
        for h in Hall.get_all():
            self.ui.HallComboBox.addItem(h.hall_name, h.hall_id)

    def load_services(self):
        services = service_model.get_all_services()
        table = self.ui.TableService
        table.setRowCount(0)

        for row_idx, svc in enumerate(services):
            table.insertRow(row_idx)
            hall_name = hall_capacity = ""
            if svc["hall_id"]:
                hall = Hall.get_by_id(svc["hall_id"])
                if hall:
                    hall_name = hall.hall_name
                    hall_capacity = str(hall.capacity)

            item_name = QTableWidgetItem(svc["service_name"])
            item_name.setData(Qt.ItemDataRole.UserRole, svc["service_id"])
            item_hall = QTableWidgetItem(hall_name or "Не указан")
            item_capacity = QTableWidgetItem(hall_capacity or "Не указана")
            item_price = QTableWidgetItem(str(int(float(svc["price"]))) if svc["price"] else "Не указана")

            for itm in (item_name, item_hall, item_capacity, item_price):
                itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEditable)

            table.setItem(row_idx, 0, item_name)
            table.setItem(row_idx, 1, item_hall)
            table.setItem(row_idx, 2, item_capacity)
            table.setItem(row_idx, 3, item_price)

        self.make_table_readonly()
        self.reset_form()

    def get_selected_service_id(self):
        row = self.ui.TableService.currentRow()
        if row >= 0:
            itm = self.ui.TableService.item(row, 0)
            if itm:
                return itm.data(Qt.ItemDataRole.UserRole)
        return None

    def edit_selected_service(self):
        svc_id = self.get_selected_service_id()
        if not svc_id:
            return

        self.ui.widget_service.setVisible(True)

        svc = service_model.get_service_by_id(svc_id)
        if not svc:
            QMessageBox.warning(None, "Ошибка", "Услуга не найдена")
            return

        self.current_service_id = svc_id
        self.ui.TypeServiceEdit.setText(svc["service_name"])
        self.ui.PriceEdit.setText(str(int(float(svc["price"]))) if svc["price"] else "")
        if svc["hall_id"]:
            idx = self.ui.HallComboBox.findData(svc["hall_id"])
            if idx >= 0:
                self.ui.HallComboBox.setCurrentIndex(idx)
        self.ui.DeleteServiceBtn.setEnabled(True)
        self.ui.SaveServiceBtn.setText("Обновить")

    def on_hall_changed(self, index):
        hall_id = self.ui.HallComboBox.currentData()
        if hall_id:
            hall = Hall.get_by_id(hall_id)
            if hall:
                self.ui.label_MaxE.setText(str(hall.capacity))
                color = self.HALL_COLOR_MAP.get(hall.hall_id, "#FFFFFF")
                self.ui.labelColorE.setText(color)
                self.ui.labelColorE.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")
                return
        self.ui.label_MaxE.clear()
        self.ui.labelColorE.clear()
        self.ui.labelColorE.setStyleSheet("")

    def add_new_service(self):
        self.load_halls()
        self.reset_form()
        self.ui.widget_service.setVisible(True)

    def save_service(self):
        name = self.ui.TypeServiceEdit.text().strip()
        price_text = self.ui.PriceEdit.text().strip()
        hall_id = self.ui.HallComboBox.currentData()

        if not name or not hall_id or not price_text:
            QMessageBox.warning(None, "Ошибка", "Заполните все поля!")
            return

        if not price_text.isdigit() or int(price_text) <= 0:
            QMessageBox.warning(None, "Ошибка", "Стоимость должна быть положительным числом!")
            return

        price = int(price_text)

        if self.current_service_id:
            if service_model.name_exists(name, exclude_id=self.current_service_id):
                QMessageBox.warning(None, "Ошибка", "Услуга с таким названием уже существует!")
                return
            service_model.update_service(self.current_service_id, name, price, hall_id)
            QMessageBox.information(None, "Успех", "Услуга успешно обновлена!")
        else:
            if service_model.name_exists(name):
                QMessageBox.warning(None, "Ошибка", "Услуга с таким названием уже существует!")
                return
            new_id = service_model.create_service(name, price, hall_id)
            if new_id:
                self.current_service_id = new_id
                QMessageBox.information(None, "Успех", "Услуга успешно добавлена!")
            else:
                QMessageBox.critical(None, "Ошибка", "Не удалось добавить услугу")
                return

        self.load_services()
        self.ui.widget_service.setVisible(False)

    def delete_service(self):
        if not self.current_service_id:
            return
        reply = QMessageBox.question(None, "Подтверждение удаления",
                                     "Вы уверены, что хотите удалить услугу?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        if service_model.delete_service(self.current_service_id):
            QMessageBox.information(None, "Успех", "Услуга удалена!")
            self.load_services()
        else:
            QMessageBox.critical(None, "Ошибка", "Не удалось удалить услугу")

        self.ui.widget_service.setVisible(False)
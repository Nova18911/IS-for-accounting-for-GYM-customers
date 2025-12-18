from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from src.models.halls import Hall


class HallPageController:
    """Логика страницы 'Залы' с виджетом справа"""

    def __init__(self, ui):
        self.ui = ui
        self.current_hall_id = None
        self.setup_interface()
        self.load_halls()
        self.ui.widget_hall.setVisible(False)

    def setup_interface(self):
        table = self.ui.HallTableWidget
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)  # таблица read-only
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.setColumnWidth(0, 230)
        table.setColumnWidth(1, 230)
        table.itemClicked.connect(self.on_table_item_clicked)

        # Кнопки виджета
        self.ui.AddHallBtn.clicked.connect(self.add_new_hall)
        self.ui.Save_hallBtn.clicked.connect(self.on_save_clicked)
        self.ui.Delete_hallBtn.clicked.connect(self.on_delete_clicked)

        # Изначально кнопка удалить неактивна
        self.ui.Delete_hallBtn.setEnabled(False)

    def load_halls(self):
        """Загрузить все залы в таблицу"""
        table = self.ui.HallTableWidget
        table.setRowCount(0)

        halls = Hall.get_all()
        for row, hall in enumerate(halls):
            table.insertRow(row)
            item_name = QTableWidgetItem(hall.hall_name)
            item_name.setData(Qt.ItemDataRole.UserRole, hall.hall_id)
            item_capacity = QTableWidgetItem(str(hall.capacity))
            item_capacity.setData(Qt.ItemDataRole.UserRole, hall.hall_id)
            table.setItem(row, 0, item_name)
            table.setItem(row, 1, item_capacity)

        self.clear_form()

    def on_table_item_clicked(self, item):
        """Заполнить виджет справа данными выбранного зала"""
        row = item.row()
        table = self.ui.HallTableWidget
        hall_id = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        hall = Hall.get_by_id(hall_id)
        if not hall:
            return
        self.current_hall_id = hall.hall_id
        self.ui.HallEdit.setText(hall.hall_name)
        self.ui.CapacityEdit.setText(str(hall.capacity))
        self.ui.widget_hall.setVisible(True)
        self.ui.Delete_hallBtn.setEnabled(True)

    def add_new_hall(self):
        self.clear_form()
        self.ui.widget_hall.setVisible(True)

    def on_save_clicked(self):
        """Создать новый зал или обновить существующий"""
        name = self.ui.HallEdit.text().strip()
        cap_text = self.ui.CapacityEdit.text().strip()
        if not name:
            QMessageBox.warning(None, "Ошибка", "Введите название зала")
            return
        try:
            capacity = int(cap_text)
            if capacity <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(None, "Ошибка", "Вместимость должна быть положительным числом")
            return

        # Добавление нового зала
        if not self.current_hall_id:
            if Hall.name_exists(name):
                QMessageBox.warning(None, "Ошибка", "Зал с таким названием уже существует")
                return
            hall = Hall(hall_name=name, capacity=capacity)
            if hall.save():
                self.current_hall_id = hall.hall_id
            else:
                QMessageBox.critical(None, "Ошибка", "Не удалось добавить зал")
                return
        # Обновление существующего зала
        else:
            if Hall.name_exists(name, exclude_id=self.current_hall_id):
                QMessageBox.warning(None, "Ошибка", "Зал с таким названием уже существует")
                return
            hall = Hall(hall_id=self.current_hall_id, hall_name=name, capacity=capacity)
            if not hall.save():
                QMessageBox.critical(None, "Ошибка", "Не удалось обновить зал")
                return

        self.load_halls()
        self.ui.widget_hall.setVisible(False)

    def on_delete_clicked(self):
        """Удаление выбранного зала"""
        if not self.current_hall_id:
            return
        reply = QMessageBox.question(None, "Удаление",
                                     "Вы уверены, что хотите удалить зал?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        hall = Hall.get_by_id(self.current_hall_id)
        if hall and hall.delete():
            self.load_halls()
            self.ui.widget_hall.setVisible(False)
        else:
            QMessageBox.critical(None, "Ошибка", "Не удалось удалить зал")

    def clear_form(self):
        """Очистить поля виджета"""
        self.current_hall_id = None
        self.ui.HallEdit.setText("")
        self.ui.CapacityEdit.setText("")
        self.ui.Delete_hallBtn.setEnabled(False)

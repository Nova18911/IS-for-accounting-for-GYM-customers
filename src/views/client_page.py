from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from datetime import datetime, date

from src.models.client import (
    client_get_all,
    client_get_by_id,
    client_create,
    client_update,
    client_delete,
    client_search_by_last_name,
    client_search_by_phone,
)
from src.models.group_trainings import GroupTraining

from src.models.subscriptions import (
    subscription_get_by_id,
    subscription_create,
    subscription_update,
    subscription_delete,
    subscription_attach_to_client,
    subscription_detach_client,
    subscription_calculate_end,
)

from src.models.subscription_prices import subscription_price_get_all
from src.models.personal_trainings import personal_training_get_by_client
from src.models.trainers import trainer_get_by_id
from src.views.add_personal_training_dialog import AddPersonalTrainingDialog

from src.views.add_group_training_dialog import AddGroupTrainingDialog
from src.models.group_attendances import (
    group_attendance_get_by_client
)

class ClientPageController:
    """Контроллер страницы 'Клиенты'"""

    def __init__(self, ui):
        self.edit_group_training = None
        self.ui = ui

        self.current_client_id = None
        self.current_subscription_id = None
        self.current_photo_data = None


        self.subscription_prices = subscription_price_get_all()
        self.current_subscription_price = None

        self.setup_interface()
        self.load_clients()

    # ---------------- interface ----------------
    def setup_interface(self):
        table = self.ui.ClientsTabWidget
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)
        table.itemClicked.connect(self.on_client_selected)

        # Поиск
        self.ui.SearchLastNameEdit.textChanged.connect(self.search_clients)
        self.ui.SearchPhoneEdit.textChanged.connect(self.search_clients)

        # Клиент
        self.ui.Save_clientBtn_3.clicked.connect(self.save_client)
        self.ui.Delete_clientBtn_3.clicked.connect(self.delete_client)
        self.ui.Photo_3.mousePressEvent = self.select_photo
        self.ui.DeletePhotoClientBtn.clicked.connect(self.clear_photo)

        # Абонементы
        self.fill_subscription_prices()
        self.ui.LongTimeComboBox_3.currentIndexChanged.connect(
            self.on_subscription_price_changed
        )
        self.ui.SaveSubBtn_3.clicked.connect(self.save_subscription)
        self.ui.DeleteSubBtn_3.clicked.connect(self.delete_subscription)

        # Тренировки
        self.ui.PersonalTrainingBtn_3.clicked.connect(self.add_personal_training)
        self.ui.GroupTrainingBtn_3.clicked.connect(self.add_group_training)

    # ---------------- subscription UI ----------------
    def fill_subscription_prices(self):
        self.ui.LongTimeComboBox_3.clear()
        for p in self.subscription_prices:
            # В ComboBox ТОЛЬКО срок
            self.ui.LongTimeComboBox_3.addItem(p['duration'], p)

    # ---------------- clients ----------------
    def load_clients(self, clients=None):
        table = self.ui.ClientsTabWidget
        table.setRowCount(0)

        clients = clients or client_get_all()
        for row, client in enumerate(clients):
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(client['last_name']))
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, client['client_id'])
            table.setItem(row, 1, QTableWidgetItem(client['first_name']))
            table.setItem(row, 2, QTableWidgetItem(client.get('middle_name') or ""))
            table.setItem(row, 3, QTableWidgetItem(client.get('phone') or ""))
            sub_id = client.get('subscription_id')
            if sub_id:
                sub = subscription_get_by_id(sub_id)
                if sub:
                    # используем card_number, если есть, иначе id
                    card_number = sub.get('card_number', sub_id)
                    table.setItem(row, 4, QTableWidgetItem(str(card_number)))
                else:
                    table.setItem(row, 4, QTableWidgetItem(""))
            else:
                table.setItem(row, 4, QTableWidgetItem(""))

        self.clear_client_form()

    def search_clients(self):
        ln = self.ui.SearchLastNameEdit.text().strip()
        ph = self.ui.SearchPhoneEdit.text().strip()

        if ln:
            self.load_clients(client_search_by_last_name(ln))
        elif ph:
            self.load_clients(client_search_by_phone(ph))
        else:
            self.load_clients()

    def on_client_selected(self, item):
        row = item.row()
        client_id = self.ui.ClientsTabWidget.item(row, 0).data(Qt.ItemDataRole.UserRole)
        client = client_get_by_id(client_id)
        if not client:
            return

        self.current_client_id = client['client_id']
        self.current_subscription_id = client['subscription_id']
        self.current_photo_data = client.get('photo')

        self.ui.Last_nameEdit_3.setText(client['last_name'])
        self.ui.First_nameEdit_3.setText(client['first_name'])
        self.ui.Midle_nameEdit_3.setText(client.get('middle_name') or "")
        self.ui.PhoneEdit_3.setText(client.get('phone') or "")
        self.ui.EmailEdit_3.setText(client.get('email') or "")

        if client.get('photo'):
            pix = QPixmap()
            pix.loadFromData(client['photo'])
            self.ui.Photo_3.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.ui.Photo_3.setText("Фото")

        self.load_subscription()
        self.load_trainings()
        self.load_group_trainings()

    # ---------------- CRUD клиента ----------------
    def save_client(self):
        ln = self.ui.Last_nameEdit_3.text().strip()
        fn = self.ui.First_nameEdit_3.text().strip()
        phone = self.ui.PhoneEdit_3.text().strip()

        if not ln or not fn or not phone:
            QMessageBox.warning(None, "Ошибка", "Заполните обязательные поля")
            return

        middle = self.ui.Midle_nameEdit_3.text().strip()
        email = self.ui.EmailEdit_3.text().strip()

        if self.current_client_id:
            client_update(
                self.current_client_id,
                ln, fn, middle, phone, email, self.current_photo_data
            )
        else:
            client_create(
                ln, fn, middle, phone, email, self.current_photo_data
            )

        self.load_clients()

    def delete_client(self):
        if not self.current_client_id:
            return

        if QMessageBox.question(
            None, "Удаление", "Удалить клиента?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        client_delete(self.current_client_id)
        self.load_clients()

    # ---------------- photo ----------------
    def select_photo(self, event):
        path, _ = QFileDialog.getOpenFileName(None, "Выбор фото", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        pix = QPixmap(path)
        self.ui.Photo_3.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        with open(path, "rb") as f:
            self.current_photo_data = f.read()

    def clear_photo(self):
        self.ui.Photo_3.setText("Фото")
        self.current_photo_data = None

    # ---------------- subscription ----------------
    def load_subscription(self):
        today = date.today()

        if not self.current_subscription_id:
            # Если абонемента нет, показываем сегодняшнюю дату
            self.ui.Day_subEdit_3.setText(str(today.day))
            self.ui.Month_subEdit_3.setText(str(today.month))
            self.ui.Year_subEdit_3.setText(str(today.year))
            self.ui.LongTimeComboBox_3.setCurrentIndex(-1)
            self.ui.PriceLabel_3.setText("")
            self.ui.DayEndLabel_3.setText("")
            self.ui.MonthEndLabel_3.setText("")
            self.ui.YearEndLabel_3.setText("")
            self.current_subscription_price = None
            return

        sub = subscription_get_by_id(self.current_subscription_id)
        if not sub:
            return

        start = sub['start_date']
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()

        self.ui.Day_subEdit_3.setText(str(start.day))
        self.ui.Month_subEdit_3.setText(str(start.month))
        self.ui.Year_subEdit_3.setText(str(start.year))

        # Выбираем срок абонемента в ComboBox и обновляем цену
        for i in range(self.ui.LongTimeComboBox_3.count()):
            p = self.ui.LongTimeComboBox_3.itemData(i)
            if p['id'] == sub['subscription_price_id']:
                self.ui.LongTimeComboBox_3.setCurrentIndex(i)
                self.current_subscription_price = p
                self.ui.PriceLabel_3.setText(f"{p['price']} ₽")
                end = subscription_calculate_end(start, p['duration'])
                self.ui.DayEndLabel_3.setText(str(end.day))
                self.ui.MonthEndLabel_3.setText(str(end.month))
                self.ui.YearEndLabel_3.setText(str(end.year))
                break


    def on_subscription_price_changed(self, index):
        if index < 0:
            self.current_subscription_price = None
            self.ui.PriceLabel_3.setText("")
            self.ui.DayEndLabel_3.setText("")
            self.ui.MonthEndLabel_3.setText("")
            self.ui.YearEndLabel_3.setText("")
            return

        price = self.ui.LongTimeComboBox_3.itemData(index)
        self.current_subscription_price = price
        self.ui.PriceLabel_3.setText(f"{price['price']} ₽")

        # Обновляем дату окончания
        try:
            start = date(
                int(self.ui.Year_subEdit_3.text()),
                int(self.ui.Month_subEdit_3.text()),
                int(self.ui.Day_subEdit_3.text())
            )
            end = subscription_calculate_end(start, price['duration'])
            self.ui.DayEndLabel_3.setText(str(end.day))
            self.ui.MonthEndLabel_3.setText(str(end.month))
            self.ui.YearEndLabel_3.setText(str(end.year))
        except Exception:
            self.ui.DayEndLabel_3.setText("")
            self.ui.MonthEndLabel_3.setText("")
            self.ui.YearEndLabel_3.setText("")

    def client_has_active_subscription(self) -> bool:
        """Проверяет, есть ли у клиента действующий абонемент"""
        if not self.current_subscription_id:
            return False

        sub = subscription_get_by_id(self.current_subscription_id)
        if not sub:
            return False

        start = sub['start_date']
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()

        for p in self.subscription_prices:
            if p['id'] == sub['subscription_price_id']:
                end = subscription_calculate_end(start, p['duration'])
                return date.today() <= end

        return False

    def save_subscription(self):
        if not self.current_client_id:
            QMessageBox.warning(None, "Ошибка", "Сначала сохраните клиента")
            return

        try:
            start = date(
                int(self.ui.Year_subEdit_3.text()),
                int(self.ui.Month_subEdit_3.text()),
                int(self.ui.Day_subEdit_3.text())
            )
        except Exception:
            QMessageBox.warning(None, "Ошибка", "Некорректная дата")
            return

        if start < date.today():
            QMessageBox.warning(None, "Ошибка", "Нельзя оформить абонемент в прошлом")
            return

        price = self.current_subscription_price
        if not price:
            QMessageBox.warning(None, "Ошибка", "Выберите срок действия")
            return

        if self.current_subscription_id:
            subscription_update(self.current_subscription_id, start, price['id'])
        else:
            sub_id = subscription_create(start, price['id'])
            subscription_attach_to_client(sub_id, self.current_client_id)
            self.current_subscription_id = sub_id

        end = subscription_calculate_end(start, price['duration'])
        self.ui.DayEndLabel_3.setText(str(end.day))
        self.ui.MonthEndLabel_3.setText(str(end.month))
        self.ui.YearEndLabel_3.setText(str(end.year))

        QMessageBox.information(None, "Готово", "Абонемент сохранён")

    def update_subscription_ui_state(self):
        has_sub = self.client_has_active_subscription()
        self.ui.PersonalTrainingBtn_3.setEnabled(has_sub)

    def delete_subscription(self):
        if not self.current_subscription_id:
            return

        if QMessageBox.question(
                None, "Удаление", "Удалить абонемент?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return

        subscription_detach_client(self.current_client_id)
        subscription_delete(self.current_subscription_id)
        self.current_subscription_id = None
        self.load_subscription()

    # ---------------- trainings ----------------
    def load_trainings(self):
        table = self.ui.PersonalTrainingTabWidget_3
        table.setRowCount(0)

        if not self.current_client_id:
            return

        trainings = personal_training_get_by_client(self.current_client_id)
        table.setRowCount(len(trainings))
        table.setColumnHidden(0, False)  # столбец с ID (будет скрыт)

        for row, pt in enumerate(trainings):
            # Скрытый столбец с ID тренировки
            id_item = QTableWidgetItem(str(pt['personal_training_id']))
            id_item.setData(Qt.ItemDataRole.UserRole, pt['personal_training_id'])
            table.setItem(row, 0, id_item)

            # Дата тренировки
            table.setItem(row, 1, QTableWidgetItem(pt['training_date'].strftime("%d-%m-%Y")))
            # Время тренировки
            table.setItem(row, 2, QTableWidgetItem(str(pt['start_time'])[:5]))
            # Тренер
            trainer = trainer_get_by_id(pt['trainer_id'])
            table.setItem(row, 3, QTableWidgetItem(
                f"{trainer['last_name']} {trainer['first_name']}" if trainer else ""
            ))

        # Скрываем столбец с ID
        table.setColumnHidden(0, True)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.itemDoubleClicked.connect(self.edit_personal_training)

    def add_personal_training(self):
        if not self.current_client_id:
            QMessageBox.warning(None, "Ошибка", "Сначала выберите клиента")
            return

        if not self.client_has_active_subscription():
            QMessageBox.warning(
                None,
                "Ошибка",
                "Нельзя записать на тренировку без активного абонемента"
            )
            return

        # Диалог для новой тренировки
        client_data = client_get_by_id(self.current_client_id)
        dialog = AddPersonalTrainingDialog(client_data)
        dialog.exec()
        self.load_trainings()

    def edit_personal_training(self, item):
        row = item.row()
        table = self.ui.PersonalTrainingTabWidget_3

        # Получаем ID тренировки из скрытого столбца
        training_id_item = table.item(row, 0)
        if not training_id_item:
            return
        training_id = training_id_item.data(Qt.ItemDataRole.UserRole)

        client_data = client_get_by_id(self.current_client_id)
        if not client_data:
            QMessageBox.warning(None, "Ошибка", "Клиент не найден")
            return

        # Создаём диалог
        dialog = AddPersonalTrainingDialog(client_data)

        # Загружаем существующую тренировку
        dialog.load_existing_training(training_id)

        dialog.exec()
        self.load_trainings()

    def load_group_trainings(self):
        table = self.ui.GroupTrainingTabWidget_3
        table.setRowCount(0)

        if not self.current_client_id:
            return

        trainings = group_attendance_get_by_client(self.current_client_id)
        table.setRowCount(len(trainings))

        for row, ga in enumerate(trainings):
            # Скрытый столбец с ID посещения
            table.setItem(row, 0, QTableWidgetItem(str(ga['attendance_id'])))

            # Получаем тренировку
            tr = GroupTraining.get_by_id(ga['group_training_id'])

            if tr:
                table.setItem(row, 1, QTableWidgetItem(tr.training_date.strftime("%d-%m-%Y")))
                table.setItem(row, 2, QTableWidgetItem(str(tr.start_time)[:5]))
                table.setItem(row, 3, QTableWidgetItem(tr.service_name or ""))
                table.setItem(row, 4, QTableWidgetItem(tr.hall_name or ""))
                table.setItem(row, 5, QTableWidgetItem(tr.trainer_name or ""))

        table.setColumnHidden(0, True)
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)

    # ---------------- group trainings ----------------
    def add_group_training(self):
        if not self.current_client_id:
            QMessageBox.warning(None, "Ошибка", "Сначала выберите клиента")
            return

        if not self.client_has_active_subscription():
            QMessageBox.warning(
                None,
                "Ошибка",
                "Нельзя записать на групповую тренировку без активного абонемента"
            )
            return

        client_data = client_get_by_id(self.current_client_id)
        dialog = AddGroupTrainingDialog(client_data)
        dialog.exec()
        self.load_group_trainings()


    # ---------------- helpers ----------------
    def clear_client_form(self):
        self.current_client_id = None
        self.current_subscription_id = None
        self.current_photo_data = None

        self.ui.Last_nameEdit_3.clear()
        self.ui.First_nameEdit_3.clear()
        self.ui.Midle_nameEdit_3.clear()
        self.ui.PhoneEdit_3.clear()
        self.ui.EmailEdit_3.clear()
        self.ui.Photo_3.setText("Фото")

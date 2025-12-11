# views/client_window.py (refactored)
import os
from datetime import datetime, timedelta
from io import BytesIO

from PyQt6.QtWidgets import (
    QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath

from src.ui.client_window import Ui_client_window

# models (functional API)
from src.models.client import (
    client_get_all, client_get_by_id, client_search_by_last_name,
    client_search_by_phone, client_create, client_update, client_delete, DURATION_MAP
)
from src.models.subscriptions import (
    subscription_create, subscription_update, subscription_delete,
    subscription_attach_to_client, subscription_detach_client, subscription_calculate_end
)
from src.models.subscription_prices import (
    subscription_price_get_all, subscription_price_get_by_id
)

# Constants
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
AVATAR_DISPLAY_SIZE = 150
AVATAR_SAVE_SIZE = 256  # size to downscale to before saving


def qpixmap_to_png_bytes(pixmap: QPixmap, size: int = AVATAR_SAVE_SIZE) -> bytes:
    """
    Scale QPixmap to square size x size (center-crop if needed) and return PNG bytes.
    Avoids external libs; uses QBuffer internally.
    """
    from PyQt6.QtCore import QBuffer, QByteArray

    if pixmap.isNull():
        return b""

    scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)

    final = QPixmap(QSize(size, size))
    final.fill(Qt.GlobalColor.transparent)
    painter = QPainter(final)
    # compute offsets to crop center if needed
    sx = (scaled.width() - size) // 2 if scaled.width() > size else 0
    sy = (scaled.height() - size) // 2 if scaled.height() > size else 0
    painter.drawPixmap(0, 0, scaled, sx, sy, size, size)
    painter.end()

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.OpenModeFlag.WriteOnly)
    final.save(buf, "PNG")
    buf.close()
    return bytes(ba)


def make_round_pixmap(pixmap: QPixmap, display_size: int = AVATAR_DISPLAY_SIZE) -> QPixmap:
    """Return a circular masked QPixmap scaled to display_size."""
    if pixmap.isNull():
        res = QPixmap(display_size, display_size)
        res.fill(Qt.GlobalColor.transparent)
        return res

    scaled = pixmap.scaled(display_size, display_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           Qt.TransformationMode.SmoothTransformation)
    final = QPixmap(display_size, display_size)
    final.fill(Qt.GlobalColor.transparent)
    painter = QPainter(final)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, display_size, display_size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled, 0, 0, display_size, display_size)
    painter.end()
    return final


class ClientWindow(QMainWindow):
    """Refactored ClientWindow using functional models and better photo handling"""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_client_window()
        self.ui.setupUi(self)

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # State
        self.current_client = None  # dict or None
        self.current_subscription = None  # dict-like or None
        self.current_photo_bytes = None  # bytes to save to DB

        # UI setup
        self.setWindowTitle("Фитнес-Менеджер - Клиенты")
        self._setup_interface()
        self.connect_buttons()

        # load
        self.load_clients()
        self.load_long_time_options()
        self.reset_form()
        self.hide_edit_panel()
        self.ui.ClientsButton.setEnabled(False)

    def _setup_interface(self):
        # Table setup: non-editable, select rows, auto resize
        tbl = self.ui.ClientsTabWidget
        tbl.setSelectionBehavior(tbl.SelectionBehavior.SelectRows)
        tbl.setEditTriggers(tbl.EditTrigger.NoEditTriggers)
        header = tbl.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # trainings tables stretch
        self.ui.PersonalTrainingTabWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.GroupTrainingTabWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.PersonalTrainingTabWidget.horizontalHeader().setVisible(False)
        self.ui.GroupTrainingTabWidget.horizontalHeader().setVisible(False)

        # Photo label clickable
        self.ui.Photo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.Photo.mousePressEvent = self._on_photo_label_clicked
        # default style
        self._set_photo_default_style()

        # connect search inputs
        self.ui.SearchLastNameEdit.textChanged.connect(self.on_search_last_name_changed)
        self.ui.SearchPhoneEdit.textChanged.connect(self.on_search_phone_changed)

        # subscription inputs
        self.ui.Day_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.Month_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.Year_subEdit.textChanged.connect(self.calculate_end_date)
        self.ui.LongTimeComboBox.currentIndexChanged.connect(self.calculate_end_date)
        self.ui.ClientTabWidget.currentChanged.connect(self._on_tab_changed)

    # -----------------------------
    # Photo helpers
    # -----------------------------
    def _set_photo_default_style(self):
        self.ui.Photo.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.ui.Photo.setText("Фото")

    def _on_photo_label_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.load_photo()

    def load_photo(self):
        """Open file dialog, validate size, scale, make circular and set current_photo_bytes."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите фото клиента", "",
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if not file_path:
            return

        # size check
        size = os.path.getsize(file_path)
        if size > MAX_PHOTO_BYTES:
            QMessageBox.warning(self, "Ошибка", "Размер файла слишком большой. Максимум 5 MB.")
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            return

        # prepare bytes to save: downscale and crop to square
        img_bytes = qpixmap_to_png_bytes(pixmap, AVATAR_SAVE_SIZE)
        if len(img_bytes) > MAX_PHOTO_BYTES:
            # fallback smaller
            img_bytes = qpixmap_to_png_bytes(pixmap, 128)

        self.current_photo_bytes = img_bytes

        # display circular avatar scaled to AVATAR_DISPLAY_SIZE
        disp = make_round_pixmap(pixmap, AVATAR_DISPLAY_SIZE)
        self.ui.Photo.setPixmap(disp)
        # indicate loaded
        self.ui.Photo.setStyleSheet("""
            QLabel {
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 5px;
            }
        """)

    def clear_photo(self):
        self.current_photo_bytes = None
        self.ui.Photo.clear()
        self._set_photo_default_style()

    # -----------------------------
    # Data loading / rendering
    # -----------------------------
    def load_clients(self):
        """Load clients into the table"""
        rows = client_get_all()
        tbl = self.ui.ClientsTabWidget
        tbl.setRowCount(0)
        for r, cl in enumerate(rows):
            tbl.insertRow(r)
            # last name (store id)
            it_ln = QTableWidgetItem(str(cl.get("last_name", "")))
            it_ln.setData(Qt.ItemDataRole.UserRole, cl.get("client_id"))
            it_ln.setFlags(it_ln.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_fn = QTableWidgetItem(str(cl.get("first_name", "")))
            it_fn.setFlags(it_fn.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_mn = QTableWidgetItem(str(cl.get("middle_name", "")))
            it_mn.setFlags(it_mn.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_phone = QTableWidgetItem(str(cl.get("phone", "")))
            it_phone.setFlags(it_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # card number
            card = str(cl.get("subscription_id")) if cl.get("subscription_id") else "Нет карты"
            it_card = QTableWidgetItem(card)
            it_card.setFlags(it_card.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # active
            active = "✓" if cl.get("is_active_subscription") else "✗"
            it_active = QTableWidgetItem(active)
            it_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_active.setFlags(it_active.flags() & ~Qt.ItemFlag.ItemIsEditable)

            if cl.get("is_active_subscription"):
                it_active.setForeground(Qt.GlobalColor.green)
            else:
                it_active.setForeground(Qt.GlobalColor.red)

            tbl.setItem(r, 0, it_ln)
            tbl.setItem(r, 1, it_fn)
            tbl.setItem(r, 2, it_mn)
            tbl.setItem(r, 3, it_phone)
            tbl.setItem(r, 4, it_card)
            tbl.setItem(r, 5, it_active)

    def load_long_time_options(self):
        """Load subscription price options into combobox"""
        self.ui.LongTimeComboBox.clear()
        rows = subscription_price_get_all()
        if rows:
            for item in rows:
                # item: {"id":.., "duration":.., "price":..}
                self.ui.LongTimeComboBox.addItem(f"{item['duration']} - {item['price']} руб.", item['id'])
        else:
            # fallback static options (ids assumed)
            fallback = [("1 месяц - 3000 руб.", 1), ("3 месяца - 8000 руб.", 2),
                        ("полгода - 15000 руб.", 3), ("год - 28000 руб.", 4)]
            for label, pid in fallback:
                self.ui.LongTimeComboBox.addItem(label, pid)

    def connect_buttons(self):
        self.ui.Add_clientBtn.clicked.connect(self.add_client)
        self.ui.Save_clientBtn.clicked.connect(self.save_client)
        self.ui.Delete_clientBtn.clicked.connect(self.delete_client)
        self.ui.SaveSubBtn.clicked.connect(self.save_subscription)
        self.ui.DeleteSubBtn.clicked.connect(self.delete_subscription)
        self.ui.PersonalTrainingBtn.clicked.connect(self.open_personal_training)
        self.ui.GroupTrainingBtn.clicked.connect(self.open_group_training)
        self.ui.ExitButton.clicked.connect(self.close)

        # nav
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.TrainerButton.clicked.connect(self.open_trainers)
        self.ui.HallButton.clicked.connect(self.open_halls)
        self.ui.ReportButton.clicked.connect(self.open_reports)

        # table interactions
        self.ui.ClientsTabWidget.doubleClicked.connect(self.on_table_double_click)
        self.ui.ClientsTabWidget.itemClicked.connect(self.on_table_item_clicked)

    def reset_form(self):
        self.current_client = None
        self.current_subscription = None
        self.ui.Last_nameEdit.clear()
        self.ui.First_nameEdit.clear()
        self.ui.Midle_nameEdit.clear()
        self.ui.PhoneEdit.clear()
        self.ui.EmailEdit.clear()
        self.clear_photo()
        self.ui.id_subsrciption.clear()
        self.ui.Day_subEdit.clear()
        self.ui.Month_subEdit.clear()
        self.ui.Year_subEdit.clear()
        if self.ui.LongTimeComboBox.count() > 0:
            self.ui.LongTimeComboBox.setCurrentIndex(0)
        self.ui.DayEndLable.clear()
        self.ui.MonthEndLabel.clear()
        self.ui.YearEndLabel.clear()
        self.ui.PriceLabel.clear()
        self.ui.PersonalTrainingTabWidget.setRowCount(0)
        self.ui.GroupTrainingTabWidget.setRowCount(0)
        self.ui.Delete_clientBtn.setEnabled(False)
        self.ui.DeleteSubBtn.setEnabled(False)
        self.hide_edit_panel()

    def add_client(self):
        self.reset_form()
        self.show_edit_panel()
        self.ui.ClientTabWidget.setCurrentIndex(0)
        self.ui.Last_nameEdit.setFocus()

    def show_edit_panel(self):
        self.ui.ClientTabWidget.setVisible(True)

    def hide_edit_panel(self):
        self.ui.ClientTabWidget.setVisible(False)

    def get_selected_client_id(self):
        row = self.ui.ClientsTabWidget.currentRow()
        if row >= 0:
            it = self.ui.ClientsTabWidget.item(row, 0)
            if it:
                return it.data(Qt.ItemDataRole.UserRole)
        return None

    def on_table_double_click(self, _index):
        cid = self.get_selected_client_id()
        if cid:
            self.edit_client(cid)

    def on_table_item_clicked(self, _item):
        cid = self.get_selected_client_id()
        if cid:
            self.edit_client(cid)

    def edit_client(self, client_id=None):
        if client_id is None:
            client_id = self.get_selected_client_id()
        if not client_id:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента для редактирования")
            return
        cl = client_get_by_id(client_id)
        if not cl:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден")
            return

        self.current_client = cl
        # fill fields
        self.ui.Last_nameEdit.setText(cl.get("last_name", ""))
        self.ui.First_nameEdit.setText(cl.get("first_name", ""))
        self.ui.Midle_nameEdit.setText(cl.get("middle_name", ""))
        self.ui.PhoneEdit.setText(cl.get("phone", ""))
        self.ui.EmailEdit.setText(cl.get("email", ""))

        # photo
        photo = cl.get("photo")
        if photo:
            pix = QPixmap()
            pix.loadFromData(photo)
            disp = make_round_pixmap(pix, AVATAR_DISPLAY_SIZE)
            self.ui.Photo.setPixmap(disp)
            self.ui.Photo.setStyleSheet("""
                QLabel { border: 2px solid #4CAF50; border-radius: 5px; padding: 5px; }
            """)
            self.current_photo_bytes = photo
        else:
            self.clear_photo()

        # subscription
        sub_id = cl.get("subscription_id")
        if sub_id:
            self.ui.id_subsrciption.setText(str(sub_id))
            # attempt to fill start/date/price if available
            if cl.get("subscription_start_date"):
                sd = cl.get("subscription_start_date")
                if isinstance(sd, str):
                    try:
                        sd_dt = datetime.strptime(sd, "%Y-%m-%d")
                        self.ui.Day_subEdit.setText(str(sd_dt.day))
                        self.ui.Month_subEdit.setText(str(sd_dt.month))
                        self.ui.Year_subEdit.setText(str(sd_dt.year))
                    except Exception:
                        pass
            if cl.get("subscription_price"):
                self.ui.PriceLabel.setText(f"{cl.get('subscription_price')} руб.")
            if cl.get("subscription_end_date"):
                ed = cl.get("subscription_end_date")
                try:
                    self.ui.DayEndLable.setText(str(ed.day))
                    self.ui.MonthEndLabel.setText(str(ed.month))
                    self.ui.YearEndLabel.setText(str(ed.year))
                except Exception:
                    pass

        self.ui.Delete_clientBtn.setEnabled(True)
        self.show_edit_panel()
        self.ui.ClientTabWidget.setCurrentIndex(0)

    def calculate_end_date(self):
        # read date fields and selected price_id
        day = self.ui.Day_subEdit.text().strip()
        month = self.ui.Month_subEdit.text().strip()
        year = self.ui.Year_subEdit.text().strip()
        price_id = self.ui.LongTimeComboBox.currentData()
        if not (day and month and year and price_id):
            self.ui.DayEndLable.clear(); self.ui.MonthEndLabel.clear(); self.ui.YearEndLabel.clear()
            self.ui.PriceLabel.clear()
            return
        try:
            d = int(day); m = int(month); y = int(year)
            start = datetime(y, m, d)
        except Exception:
            self.ui.DayEndLable.clear(); self.ui.MonthEndLabel.clear(); self.ui.YearEndLabel.clear()
            self.ui.PriceLabel.clear()
            return
        price_obj = subscription_price_get_by_id(price_id)
        if not price_obj:
            self.ui.PriceLabel.clear()
            return
        duration = price_obj.get("duration")
        days = DURATION_MAP.get(duration, 30)
        end = start + timedelta(days=days)
        self.ui.DayEndLable.setText(str(end.day))
        self.ui.MonthEndLabel.setText(str(end.month))
        self.ui.YearEndLabel.setText(str(end.year))
        self.ui.PriceLabel.setText(f"{price_obj.get('price')} руб.")

    # -----------------------------
    # Save / Delete
    # -----------------------------
    def save_client(self):
        ln = self.ui.Last_nameEdit.text().strip()
        fn = self.ui.First_nameEdit.text().strip()
        mn = self.ui.Midle_nameEdit.text().strip()
        phone = self.ui.PhoneEdit.text().strip()
        email = self.ui.EmailEdit.text().strip()

        if not ln:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию клиента!")
            self.ui.Last_nameEdit.setFocus(); return
        if not fn:
            QMessageBox.warning(self, "Ошибка", "Введите имя клиента!")
            self.ui.First_nameEdit.setFocus(); return
        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите телефон клиента!")
            self.ui.PhoneEdit.setFocus(); return

        photo_bytes = self.current_photo_bytes

        if self.current_client:
            # update
            client_update(self.current_client.get("client_id"), ln, fn, mn, photo_bytes, phone, email, self.current_client.get("subscription_id"))
            QMessageBox.information(self, "Успех", "Данные клиента успешно обновлены!")
            # reload
            self.load_clients()
        else:
            # create
            new_id = client_create(ln, fn, mn, photo_bytes, phone, email, None)
            if new_id:
                QMessageBox.information(self, "Успех", "Клиент успешно добавлен!")
                self.current_client = client_get_by_id(new_id)
                self.load_clients()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить клиента")

    def delete_client(self):
        if not self.current_client:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного клиента для удаления")
            return
        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     f"Вы уверены, что хотите удалить клиента '{self.current_client.get('last_name','')}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        client_delete(self.current_client.get("client_id"))
        QMessageBox.information(self, "Успех", "Клиент удален!")
        self.reset_form()
        self.load_clients()

    def save_subscription(self):
        if not self.current_client:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите или создайте клиента!")
            return
        day = self.ui.Day_subEdit.text().strip()
        month = self.ui.Month_subEdit.text().strip()
        year = self.ui.Year_subEdit.text().strip()
        price_id = self.ui.LongTimeComboBox.currentData()
        if not (day and month and year and price_id):
            QMessageBox.warning(self, "Ошибка", "Заполните дату и выберите тип абонемента!")
            return
        try:
            start = datetime(int(year), int(month), int(day))
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректная дата оформления!")
            return
        # prevent past dates
        if start.date() < datetime.now().date():
            QMessageBox.warning(self, "Ошибка", "Дата оформления не может быть в прошлом!")
            return
        # create subscription and attach to client
        new_sub_id = subscription_create(start.date(), price_id)
        if new_sub_id:
            subscription_attach_to_client(new_sub_id, self.current_client.get("client_id"))
            QMessageBox.information(self, "Успех", "Абонемент успешно оформлен!")
            # reload client and display
            self.current_client = client_get_by_id(self.current_client.get("client_id"))
            self.load_subscription_into_ui()
            self.load_clients()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось оформить абонемент")

    def delete_subscription(self):
        # will detach client and delete subscription if exists
        sub_id = self.ui.id_subsrciption.text().strip()
        if not sub_id:
            QMessageBox.warning(self, "Ошибка", "Нет выбранного абонемента для удаления")
            return
        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     "Вы уверены, что хотите удалить абонемент?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        subscription_detach_client(self.current_client.get("client_id"))
        subscription_delete(int(sub_id))
        QMessageBox.information(self, "Успех", "Абонемент удален!")
        self.current_client = client_get_by_id(self.current_client.get("client_id"))
        self.load_subscription_into_ui()
        self.load_clients()

    def load_subscription_into_ui(self):
        """Helper to refresh subscription UI from current_client"""
        if not self.current_client:
            return
        sub_id = self.current_client.get("subscription_id")
        if not sub_id:
            self.ui.id_subsrciption.clear()
            self.ui.Day_subEdit.clear(); self.ui.Month_subEdit.clear(); self.ui.Year_subEdit.clear()
            self.ui.DayEndLable.clear(); self.ui.MonthEndLabel.clear(); self.ui.YearEndLabel.clear()
            self.ui.PriceLabel.clear()
            self.ui.DeleteSubBtn.setEnabled(False)
            return
        # set id
        self.ui.id_subsrciption.setText(str(sub_id))
        start = self.current_client.get("subscription_start_date")
        if start:
            if isinstance(start, str):
                try:
                    sd = datetime.strptime(start, "%Y-%m-%d")
                    self.ui.Day_subEdit.setText(str(sd.day)); self.ui.Month_subEdit.setText(str(sd.month)); self.ui.Year_subEdit.setText(str(sd.year))
                except Exception:
                    pass
        price = self.current_client.get("subscription_price")
        if price:
            self.ui.PriceLabel.setText(f"{price} руб.")
        end = self.current_client.get("subscription_end_date")
        if end:
            try:
                self.ui.DayEndLable.setText(str(end.day)); self.ui.MonthEndLabel.setText(str(end.month)); self.ui.YearEndLabel.setText(str(end.year))
            except Exception:
                pass
        self.ui.DeleteSubBtn.setEnabled(True)

    # -----------------------------
    # Trainings (fallback: if you have functions add them)
    # -----------------------------
    def load_trainings_data(self):
        # If your client model provides training getters, you can call them here.
        # For now, we'll clear tables.
        self.ui.PersonalTrainingTabWidget.setRowCount(0)
        self.ui.GroupTrainingTabWidget.setRowCount(0)

    def open_personal_training(self):
        QMessageBox.information(self, "В разработке", "Запись на персональную тренировку в разработке")

    def open_group_training(self):
        QMessageBox.information(self, "В разработке", "Запись на групповую тренировку в разработке")

    # -----------------------------
    # Navigation helpers
    # -----------------------------
    def _on_tab_changed(self, index):
        if index == 1 and not self.current_client:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите или создайте клиента!")
            self.ui.ClientTabWidget.setCurrentIndex(0)
        if index == 2 and not self.current_client:
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите или создайте клиента!")
            self.ui.ClientTabWidget.setCurrentIndex(0)
        if index == 2 and self.current_client:
            self.load_trainings_data()

    def on_search_last_name_changed(self, text):
        if text.strip():
            rows = client_search_by_last_name(text.strip())
            self._populate_table_from_list(rows)
        else:
            self.load_clients()

    def on_search_phone_changed(self, text):
        if text.strip():
            rows = client_search_by_phone(text.strip())
            self._populate_table_from_list(rows)
        else:
            self.load_clients()

    def _populate_table_from_list(self, rows):
        tbl = self.ui.ClientsTabWidget
        tbl.setRowCount(0)
        for r, cl in enumerate(rows):
            tbl.insertRow(r)
            it_ln = QTableWidgetItem(str(cl.get("last_name", "")))
            it_ln.setData(Qt.ItemDataRole.UserRole, cl.get("client_id"))
            it_ln.setFlags(it_ln.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_fn = QTableWidgetItem(str(cl.get("first_name", ""))); it_fn.setFlags(it_fn.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_mn = QTableWidgetItem(str(cl.get("middle_name", ""))); it_mn.setFlags(it_mn.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_phone = QTableWidgetItem(str(cl.get("phone", ""))); it_phone.setFlags(it_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)
            card = str(cl.get("subscription_id")) if cl.get("subscription_id") else "Нет карты"
            it_card = QTableWidgetItem(card); it_card.setFlags(it_card.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_active = QTableWidgetItem("✓" if cl.get("is_active_subscription") else "✗"); it_active.setFlags(it_active.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_active.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cl.get("is_active_subscription"):
                it_active.setForeground(Qt.GlobalColor.green)
            else:
                it_active.setForeground(Qt.GlobalColor.red)
            tbl.setItem(r, 0, it_ln); tbl.setItem(r, 1, it_fn); tbl.setItem(r, 2, it_mn)
            tbl.setItem(r, 3, it_phone); tbl.setItem(r, 4, it_card); tbl.setItem(r, 5, it_active)

    def open_services(self):
        try:
            from src.views.service_window import ServiceForm
            self.service_window = ServiceForm(self.user_id, self.user_email, self.user_role)
            self.service_window.show()
            self.close()
        except Exception:
            QMessageBox.warning(self, "В разработке", "Окно услуг находится в разработке")

    def open_schedule(self):
        try:
            from src.views.schedule_window import ScheduleWindow
            self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
            self.schedule_window.show()
            self.close()
        except Exception:
            QMessageBox.warning(self, "В разработке", "Окно расписания находится в разработке")

    def open_trainers(self):
        try:
            from src.views.trainer_window import TrainerWindow
            self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
            self.trainer_window.show()
            self.close()
        except Exception:
            QMessageBox.warning(self, "В разработке", "Окно тренеров в разработке")

    def open_halls(self):
        try:
            from src.views.hall_window import HallWindow
            self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
            self.hall_window.show()
            self.close()
        except Exception:
            QMessageBox.warning(self, "В разработке", "Окно залов находится в разработке")

    def open_reports(self):
        QMessageBox.information(self, "В разработке", "Окно отчетов находится в разработке")

# views/hall_window.py
from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt

from src.ui.hall_window import Ui_HallForm
from src.models.halls import Hall


class HallWindow(QMainWindow):
    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()
        self.ui = Ui_HallForm()
        self.ui.setupUi(self)

        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        self.setup_interface()
        self.load_halls()
        self.connect_buttons()

        self.ui.HallButton.setEnabled(False)

    # ---------------- UI ----------------

    def setup_interface(self):
        self.ui.HallTableWidget.setColumnWidth(0, 230)
        self.ui.HallTableWidget.setColumnWidth(1, 230)

        self.ui.HallTableWidget.itemChanged.connect(self.on_item_changed)

    # ---------------- DATA LOAD ----------------

    def load_halls(self):
        self.ui.HallTableWidget.itemChanged.disconnect(self.on_item_changed)

        # Clear table
        for row in range(20):
            self.ui.HallTableWidget.setItem(row, 0, QTableWidgetItem(""))
            self.ui.HallTableWidget.setItem(row, 1, QTableWidgetItem(""))

        halls = Hall.get_all()

        for row, hall in enumerate(halls[:20]):
            item_name = QTableWidgetItem(hall.hall_name)
            item_capacity = QTableWidgetItem(str(hall.capacity))

            # store hall_id
            item_name.setData(Qt.ItemDataRole.UserRole, hall.hall_id)
            item_capacity.setData(Qt.ItemDataRole.UserRole, hall.hall_id)

            self.ui.HallTableWidget.setItem(row, 0, item_name)
            self.ui.HallTableWidget.setItem(row, 1, item_capacity)

        self.ui.HallTableWidget.itemChanged.connect(self.on_item_changed)

    # ---------------- SAVE / UPDATE ----------------

    def on_item_changed(self, item):
        row = item.row()
        name_item = self.ui.HallTableWidget.item(row, 0)
        cap_item = self.ui.HallTableWidget.item(row, 1)

        if not name_item or not cap_item:
            return

        hall_name = name_item.text().strip()
        cap_text = cap_item.text().strip()

        # Empty row = ignore
        if not hall_name and not cap_text:
            return

        # Validate
        if not hall_name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым!")
            return

        if not cap_text.isdigit() or int(cap_text) <= 0:
            QMessageBox.warning(self, "Ошибка", "Вместимость должна быть > 0")
            cap_item.setText("")
            return

        capacity = int(cap_text)
        hall_id = name_item.data(Qt.ItemDataRole.UserRole)

        # New hall
        if hall_id is None:
            if Hall.name_exists(hall_name):
                QMessageBox.warning(self, "Ошибка", "Зал с таким названием уже существует!")
                name_item.setText("")
                return

            hall = Hall.create(hall_name, capacity)

            # assign ID to row
            name_item.setData(Qt.ItemDataRole.UserRole, hall.hall_id)
            cap_item.setData(Qt.ItemDataRole.UserRole, hall.hall_id)

            QMessageBox.information(self, "Успех", "Зал добавлен")
            return

        # Update existing
        if Hall.name_exists(hall_name, exclude_id=hall_id):
            QMessageBox.warning(self, "Ошибка", "Зал с таким названием уже существует!")
            self.load_halls()
            return

        hall = Hall(hall_id=hall_id, hall_name=hall_name, capacity=capacity)
        hall.update()

        QMessageBox.information(self, "Успех", "Зал обновлён")

    # ---------------- Navigation ----------------

    def connect_buttons(self):
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.ClientsButton.clicked.connect(self.open_clients)
        self.ui.TrainerButton.clicked.connect(self.open_trainers)
        self.ui.HallButton.clicked.connect(lambda: None)
        self.ui.ReportButton.clicked.connect(self.open_reports)
        self.ui.ExitButton.clicked.connect(self.close)

    def open_services(self):
        from src.views.service_window import ServiceForm
        self.service_window = ServiceForm(self.user_id, self.user_email, self.user_role)
        self.service_window.show()
        self.close()

    def open_schedule(self):
        from src.views.schedule_window import ScheduleWindow
        self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
        self.schedule_window.show()
        self.close()

    def open_clients(self):
        from src.views.client_window import ClientWindow
        self.client_window = ClientWindow(self.user_id, self.user_email, self.user_role)
        self.client_window.show()
        self.close()

    def open_trainers(self):
        from src.views.trainer_window import TrainerWindow
        self.trainer_window = TrainerWindow(self.user_id, self.user_email, self.user_role)
        self.trainer_window.show()
        self.close()

    def open_reports(self):
        QMessageBox.information(self, "Инфо", "Отчеты в разработке")

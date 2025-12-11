# src/views/trainer_window.py
import os
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QByteArray, QBuffer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath

# Импорт UI остаётся на уровне модуля — это нормально
from src.ui.trainer_window import Ui_TrainerForm

# Константы
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB
SAVE_PHOTO_SIZE = 256               # уменьшать перед сохранением до 256x256
THUMBNAIL_SIZE = 150                # показывать миниатюру 150x150

# Настройка логгера для этого модуля (пишет в основной лог приложения, если настроен)
logger = logging.getLogger("trainer_window")
if not logger.handlers:
    # если логгер ещё не настроен, добавим минимальный обработчик (не перезаписывает основной)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


def qimage_to_bytes(qimage: QImage, fmt: str = "PNG") -> bytes:
    """Сохранить QImage в байты через QBuffer."""
    try:
        buf = QBuffer()
        buf.open(QBuffer.OpenModeFlag.WriteOnly)
        ok = qimage.save(buf, fmt)
        if not ok:
            logger.warning("qimage_to_bytes: qimage.save returned False")
        data = bytes(buf.data())
        buf.close()
        return data
    except Exception as e:
        logger.exception("qimage_to_bytes failed: %s", e)
        return b""


def make_circular_pixmap(pix: QPixmap, size: int) -> QPixmap:
    """Возвращает QPixmap размером size x size, обрезанный в круг и с рамкой.
       Весь код обёрнут в try/except, при проблеме возвращаем пустой pixmap."""
    try:
        if pix.isNull():
            out = QPixmap(size, size)
            out.fill(Qt.GlobalColor.transparent)
            return out

        scaled = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)

        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)

        painter = QPainter(out)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)

        # рамка
        pen = painter.pen()
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(0, 0, size - 1, size - 1)

        painter.end()
        return out
    except Exception as e:
        logger.exception("make_circular_pixmap failed: %s", e)
        fallback = QPixmap(size, size)
        fallback.fill(Qt.GlobalColor.transparent)
        return fallback


class TrainerWindow(QMainWindow):
    """Стабильный вариант окна тренеров с защитами."""

    def __init__(self, user_id=None, user_email=None, user_role=None):
        super().__init__()

        try:
            self.ui = Ui_TrainerForm()
            self.ui.setupUi(self)
        except Exception:
            logger.exception("Failed to setup UI in TrainerWindow __init__")
            raise

        # user data
        self.user_id = user_id
        self.user_email = user_email
        self.user_role = user_role

        # state
        self.current_trainer = None
        self.current_photo_data = None  # bytes

        # init UI bits
        try:
            self.setup_interface()
        except Exception:
            logger.exception("setup_interface crashed")
            # не поднимаем дальше — но можно продолжить
        # грузим типы/список — обёрнуто в try, чтобы локализовать падение
        try:
            self.load_trainer_types()
        except Exception:
            logger.exception("load_trainer_types crashed (continuing)")

        try:
            self.load_trainers()
        except Exception:
            logger.exception("load_trainers crashed (continuing)")

        try:
            self.connect_buttons()
        except Exception:
            logger.exception("connect_buttons crashed (continuing)")

        try:
            self.hide_edit_panel()
            self.reset_form()
            self.ui.TrainerButton.setEnabled(False)
        except Exception:
            logger.exception("post-init UI adjustments failed")

        self.setWindowTitle("Фитнес-Менеджер - Тренеры")

    # -----------------------
    # Интерфейс / таблица
    # -----------------------
    def setup_interface(self):
        header = self.ui.TrainerTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Таблица — только чтение по умолчанию
        self.ui.TrainerTableWidget.setEditTriggers(
            self.ui.TrainerTableWidget.EditTrigger.NoEditTriggers
        )
        self.ui.TrainerTableWidget.setSelectionBehavior(
            self.ui.TrainerTableWidget.SelectionBehavior.SelectRows
        )

        # События
        self.ui.TrainerTableWidget.doubleClicked.connect(self.on_table_double_click)
        self.ui.TrainerTableWidget.itemClicked.connect(self.on_table_item_clicked)
        self.ui.SearchLastNameEdit.textChanged.connect(self.on_search_last_name_changed)
        self.ui.SearchPhoneEdit.textChanged.connect(self.on_search_phone_changed)

        # Clickable label may be provided by UI; safe-connect
        try:
            self.ui.PhotoTrainerE.clicked.connect(self.on_photo_clicked)
        except Exception:
            # fallback
            try:
                self.ui.PhotoTrainerE.mousePressEvent = lambda ev: self.on_photo_clicked()
            except Exception:
                logger.warning("Photo label has neither .clicked nor mousePressEvent assignable")

    # -----------------------
    # Загрузка / отображение данных
    # -----------------------
    def load_trainer_types(self):
        """Загружает типы тренеров в ComboBox. Использует локальные импорты моделей (чтобы избежать циклов)."""
        try:
            from src.models.trainer_types import trainer_type_get_all as _get_all
            self.ui.TrainerTypeComboBox.clear()
            self.ui.TrainerTypeComboBox.addItem("Выберите тип", None)
            types = _get_all()
            for t in types:
                # ожидаем dict {'trainer_type_id', 'trainer_type_name', 'rate'}
                self.ui.TrainerTypeComboBox.addItem(t.get("trainer_type_name") or "Не указан", t.get("trainer_type_id"))
            # событие изменения типа
            self.ui.TrainerTypeComboBox.currentIndexChanged.connect(self.on_trainer_type_changed)
        except Exception as e:
            logger.exception("load_trainer_types failed: %s", e)

    def load_trainers(self):
        """Load trainers using model functions (local import)."""
        try:
            from src.models.trainers import trainer_get_all as _get_all
            self.ui.TrainerTableWidget.setRowCount(0)
            rows = _get_all()
            for rnum, row in enumerate(rows):
                try:
                    self.ui.TrainerTableWidget.insertRow(rnum)
                    item_last = QTableWidgetItem(str(row.get("last_name", "")))
                    item_last.setData(Qt.ItemDataRole.UserRole, row.get("trainer_id"))
                    item_last.setFlags(item_last.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_first = QTableWidgetItem(str(row.get("first_name", "")))
                    item_first.setFlags(item_first.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_mid = QTableWidgetItem(str(row.get("middle_name", "")))
                    item_mid.setFlags(item_mid.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    item_phone = QTableWidgetItem(str(row.get("phone", "")))
                    item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    self.ui.TrainerTableWidget.setItem(rnum, 0, item_last)
                    self.ui.TrainerTableWidget.setItem(rnum, 1, item_first)
                    self.ui.TrainerTableWidget.setItem(rnum, 2, item_mid)
                    self.ui.TrainerTableWidget.setItem(rnum, 3, item_phone)
                except Exception:
                    logger.exception("Failed to populate row %s in trainer table", rnum)
        except Exception as e:
            logger.exception("load_trainers failed: %s", e)

    # -----------------------
    # Навигация / кнопки
    # -----------------------
    def connect_buttons(self):
        self.ui.Add_clientBtn.clicked.connect(self.add_trainer)
        self.ui.SaveTrainerBtn.clicked.connect(self.save_trainer)
        self.ui.DeleteTrainerBtn.clicked.connect(self.delete_trainer)
        self.ui.ExitButton.clicked.connect(self.close)

        # Навигация — локальные импорты при клике
        self.ui.ServiceButton.clicked.connect(self.open_services)
        self.ui.ScheduleButton.clicked.connect(self.open_schedule)
        self.ui.ClientsButton.clicked.connect(self.open_clients)
        self.ui.HallButton.clicked.connect(self.open_halls)
        self.ui.ReportButton.clicked.connect(self.open_reports)

    # -----------------------
    # Работа с фото
    # -----------------------
    def on_photo_clicked(self):
        self.load_photo()

    def load_photo(self):
        """Загрузить файл, проверить размер, уменьшить, сохранить в current_photo_data и показать миниатюру"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Выберите фото тренера", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
            )
            if not path:
                return

            size = os.path.getsize(path)
            if size > MAX_PHOTO_BYTES:
                QMessageBox.warning(self, "Ошибка", "Размер файла слишком большой. Максимум 5 MB.")
                return

            img = QImage(path)
            if img.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
                return

            # Сохраняем уменьшённый для БД
            saved = img.scaled(SAVE_PHOTO_SIZE, SAVE_PHOTO_SIZE,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            bts = qimage_to_bytes(saved, "PNG")
            if not bts:
                QMessageBox.warning(self, "Ошибка", "Не удалось подготовить изображение для сохранения.")
                return
            if len(bts) > MAX_PHOTO_BYTES:
                # ещё сильнее уменьшаем
                saved = img.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                bts = qimage_to_bytes(saved, "PNG")

            self.current_photo_data = bts

            # отображаем круглый thumbnail
            pix = QPixmap()
            pix.loadFromData(bts)
            circ = make_circular_pixmap(pix, THUMBNAIL_SIZE)
            self.ui.PhotoTrainerE.setPixmap(circ)
        except Exception as e:
            logger.exception("load_photo failed: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить фото: {e}")

    def clear_photo(self):
        self.ui.PhotoTrainerE.clear()
        self.ui.PhotoTrainerE.setText("Фото")
        self.current_photo_data = None

    # -----------------------
    # CRUD / редактирование
    # -----------------------
    def reset_form(self):
        self.current_trainer = None
        try:
            self.ui.LastNameTrainerEdit.clear()
            self.ui.FirstNameTrainerEdit.clear()
            self.ui.MidleNameTrainerEdit.clear()
            self.ui.PhoneTrainer.clear()
            self.ui.EmailTrainerEdit.clear()
            self.ui.TrainerTypeComboBox.setCurrentIndex(0)
            self.ui.RateE.clear()
            self.ui.IdTrainerE.clear()
            self.clear_photo()
            self.ui.SaveTrainerBtn.setText("Сохранить")
            self.ui.DeleteTrainerBtn.setEnabled(False)
            self.ui.Add_clientBtn.setEnabled(True)
            self.hide_edit_panel()
        except Exception:
            logger.exception("reset_form encountered problem")

    def show_edit_panel(self):
        try:
            self.ui.widget_2.setVisible(True)
        except Exception:
            logger.exception("show_edit_panel failed")

    def hide_edit_panel(self):
        try:
            self.ui.widget_2.setVisible(False)
        except Exception:
            logger.exception("hide_edit_panel failed")

    def add_trainer(self):
        self.reset_form()
        self.show_edit_panel()
        self.ui.LastNameTrainerEdit.setFocus()

    def get_selected_trainer_id(self):
        try:
            r = self.ui.TrainerTableWidget.currentRow()
            if r >= 0:
                item = self.ui.TrainerTableWidget.item(r, 0)
                if item:
                    return item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            logger.exception("get_selected_trainer_id failed")
        return None

    def on_table_double_click(self, _index):
        tid = self.get_selected_trainer_id()
        if tid:
            self.edit_trainer(tid)

    def on_table_item_clicked(self, _item):
        tid = self.get_selected_trainer_id()
        if tid:
            self.edit_trainer(tid)

    def edit_trainer(self, trainer_id=None):
        try:
            if not trainer_id:
                trainer_id = self.get_selected_trainer_id()
            if not trainer_id:
                QMessageBox.warning(self, "Предупреждение", "Выберите тренера")
                return

            # Локальный импорт модели
            from src.models.trainers import trainer_get_by_id as _get_by_id
            tr = _get_by_id(trainer_id)
            if not tr:
                QMessageBox.warning(self, "Ошибка", "Тренер не найден")
                return

            # tr — dict
            self.current_trainer = tr
            self.ui.LastNameTrainerEdit.setText(str(tr.get("last_name", "")))
            self.ui.FirstNameTrainerEdit.setText(str(tr.get("first_name", "")))
            self.ui.MidleNameTrainerEdit.setText(str(tr.get("middle_name", "") or ""))
            self.ui.PhoneTrainer.setText(str(tr.get("phone", "") or ""))
            self.ui.EmailTrainerEdit.setText(str(tr.get("email", "") or ""))
            self.ui.IdTrainerE.setText(str(tr.get("trainer_id", "") or ""))

            tt_id = tr.get("trainer_type_id")
            if tt_id:
                idx = self.ui.TrainerTypeComboBox.findData(tt_id)
                if idx >= 0:
                    self.ui.TrainerTypeComboBox.setCurrentIndex(idx)

            photo = tr.get("photo")
            if photo:
                pix = QPixmap()
                pix.loadFromData(photo)
                circ = make_circular_pixmap(pix, THUMBNAIL_SIZE)
                self.ui.PhotoTrainerE.setPixmap(circ)
                self.current_photo_data = photo
            else:
                self.clear_photo()

            self.ui.DeleteTrainerBtn.setEnabled(True)
            self.ui.SaveTrainerBtn.setText("Обновить")
            self.ui.Add_clientBtn.setEnabled(False)
            self.show_edit_panel()
        except Exception as e:
            logger.exception("edit_trainer failed: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные тренера: {e}")

    def save_trainer(self):
        """Сохраняет или создаёт тренера, использует функциональные модели (локальные импорты)."""
        try:
            last = self.ui.LastNameTrainerEdit.text().strip()
            first = self.ui.FirstNameTrainerEdit.text().strip()
            middle = self.ui.MidleNameTrainerEdit.text().strip()
            phone = self.ui.PhoneTrainer.text().strip()
            trainer_type_id = self.ui.TrainerTypeComboBox.currentData()
            email = self.ui.EmailTrainerEdit.text().strip()

            if not last:
                QMessageBox.warning(self, "Ошибка", "Введите фамилию тренера!")
                self.ui.LastNameTrainerEdit.setFocus()
                return
            if not first:
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

            # Локальные импорты CRUD-функций
            from src.models.trainers import (
                trainer_create as _create,
                trainer_update as _update
            )

            if self.current_trainer:
                # обновление
                trainer_id = self.current_trainer.get("trainer_id")
                photo_bytes = self.current_photo_data if self.current_photo_data is not None else self.current_trainer.get("photo")
                ok = _update(trainer_id, last, first, middle, photo_bytes, phone, trainer_type_id, email)
                if ok:
                    QMessageBox.information(self, "Успех", "Данные тренера обновлены!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить тренера")
            else:
                # создание
                photo_bytes = self.current_photo_data
                new_id = _create(last, first, middle, photo_bytes, phone, trainer_type_id, email)
                if new_id:
                    QMessageBox.information(self, "Успех", "Тренер успешно добавлен!")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить тренера")

            self.load_trainers()
            self.reset_form()
        except Exception as e:
            logger.exception("save_trainer failed: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить тренера: {e}")

    def delete_trainer(self):
        try:
            if not self.current_trainer:
                QMessageBox.warning(self, "Ошибка", "Нет выбранного тренера для удаления")
                return
            from src.models.trainers import trainer_delete as _delete
            trainer_id = self.current_trainer.get("trainer_id")
            reply = QMessageBox.question(self, "Подтверждение удаления",
                                         f"Вы уверены, что хотите удалить тренера '{self.current_trainer.get('last_name','')}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            ok = _delete(trainer_id)
            if ok:
                QMessageBox.information(self, "Успех", "Тренер удален!")
                self.load_trainers()
                self.reset_form()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить тренера")
        except Exception as e:
            logger.exception("delete_trainer failed: %s", e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тренера: {e}")

    # -----------------------
    # Поиск
    # -----------------------
    def on_search_last_name_changed(self, text):
        txt = text.strip()
        try:
            if not txt:
                self.load_trainers(); return
            from src.models.trainers import trainer_search_by_last_name as _search
            rows = _search(txt)
            # rows — список dict
            self._fill_table_from_list(rows)
        except Exception:
            logger.exception("on_search_last_name_changed failed")

    def on_search_phone_changed(self, text):
        txt = text.strip()
        try:
            if not txt:
                self.load_trainers(); return
            from src.models.trainers import trainer_search_by_phone as _search
            rows = _search(txt)
            self._fill_table_from_list(rows)
        except Exception:
            logger.exception("on_search_phone_changed_failed")

    def _fill_table_from_list(self, trainers_list):
        try:
            self.ui.TrainerTableWidget.setRowCount(0)
            for rnum, tr in enumerate(trainers_list):
                self.ui.TrainerTableWidget.insertRow(rnum)
                item_last = QTableWidgetItem(str(tr.get("last_name","")))
                item_last.setFlags(item_last.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_last.setData(Qt.ItemDataRole.UserRole, tr.get("trainer_id"))

                item_first = QTableWidgetItem(str(tr.get("first_name","")))
                item_first.setFlags(item_first.flags() & ~Qt.ItemFlag.ItemIsEditable)

                item_mid = QTableWidgetItem(str(tr.get("middle_name","")))
                item_mid.setFlags(item_mid.flags() & ~Qt.ItemFlag.ItemIsEditable)

                item_phone = QTableWidgetItem(str(tr.get("phone","")))
                item_phone.setFlags(item_phone.flags() & ~Qt.ItemFlag.ItemIsEditable)

                self.ui.TrainerTableWidget.setItem(rnum, 0, item_last)
                self.ui.TrainerTableWidget.setItem(rnum, 1, item_first)
                self.ui.TrainerTableWidget.setItem(rnum, 2, item_mid)
                self.ui.TrainerTableWidget.setItem(rnum, 3, item_phone)
        except Exception:
            logger.exception("_fill_table_from_list failed")

    # -----------------------
    # Режим выбора типа тренера (показываем ставку)
    # -----------------------
    def on_trainer_type_changed(self, index):
        try:
            tid = self.ui.TrainerTypeComboBox.itemData(index)
            if not tid:
                self.ui.RateE.clear()
                return
            # локальный импорт
            from src.models.trainer_types import trainer_type_get_by_id as _get_by_id
            tt = _get_by_id(tid)
            if tt:
                # tt — dict {'trainer_type_id','trainer_type_name','rate'}
                rate = tt.get("rate")
                self.ui.RateE.setText(f"{rate} руб." if rate is not None else "")
            else:
                self.ui.RateE.clear()
        except Exception:
            logger.exception("on_trainer_type_changed failed")

    # -----------------------
    # Навигация (локальные импорты)
    # -----------------------
    def open_services(self):
        try:
            from src.views.service_window import ServiceForm
            self.service_window = ServiceForm(self.user_id, self.user_email, self.user_role)
            self.service_window.show(); self.close()
        except Exception:
            logger.exception("open_services failed")
            QMessageBox.warning(self, "В разработке", "Окно услуг находится в разработке")

    def open_schedule(self):
        try:
            from src.views.schedule_window import ScheduleWindow
            self.schedule_window = ScheduleWindow(self.user_id, self.user_email, self.user_role)
            self.schedule_window.show(); self.close()
        except Exception:
            logger.exception("open_schedule failed")
            QMessageBox.warning(self, "В разработке", "Окно расписания находится в разработке")

    def open_clients(self):
        try:
            from src.views.client_window import ClientWindow
            self.client_window = ClientWindow(self.user_id, self.user_email, self.user_role)
            self.client_window.show(); self.close()
        except Exception:
            logger.exception("open_clients failed")
            QMessageBox.warning(self, "В разработке", "Окно клиентов находится в разработке")

    def open_halls(self):
        try:
            from src.views.hall_window import HallWindow
            self.hall_window = HallWindow(self.user_id, self.user_email, self.user_role)
            self.hall_window.show(); self.close()
        except Exception:
            logger.exception("open_halls failed")
            QMessageBox.warning(self, "В разработке", "Окно залов находится в разработке")

    def open_reports(self):
        QMessageBox.information(self, "В разработке", "Окно отчетов находится в разработке")

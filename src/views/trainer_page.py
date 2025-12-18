# src/views/trainer_page.py
import os
import logging
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QTableWidgetItem, QMessageBox, QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QBuffer
from PyQt6.QtGui import QPixmap, QImage

# Импорт моделей
from src.models.trainers import (
    trainer_get_all, trainer_get_by_id, trainer_create, trainer_update,
    trainer_delete, trainer_search_by_last_name, trainer_search_by_phone
)
from src.models.trainer_types import trainer_type_get_all, trainer_type_get_by_id

# --------------------------
# Настройка логгера и констант
# --------------------------
MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB

logger = logging.getLogger("trainer_page_controller")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

def qimage_to_bytes(qimage: QImage, fmt: str = "PNG") -> bytes:
    """Сохраняет QImage в байты для хранения в БД."""
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


# --------------------------
# Контроллер страницы тренеров
# --------------------------
class TrainerPageController:
    """Контроллер для страницы 'Тренеры' в главном окне."""

    def __init__(self, ui):
        self.ui = ui
        self.current_trainer: Optional[Dict] = None
        self.current_photo_data: Optional[bytes] = None


        self._setup_interface()
        self._connect_signals()
        self.load_trainer_types()
        self.load_trainers()
        self.reset_form()

        self.ui.widget_trainer.setVisible(False)

    # -----------------------
    # Интерфейс таблицы
    # -----------------------
    def _setup_interface(self):
        table = self.ui.TrainerTableWidget
        table.setColumnCount(7)
        headers = ["Фамилия", "Имя", "Отчество", "Телефон", "Email", "Тип", "ID"]
        table.setHorizontalHeaderLabels(headers)
        table.setColumnHidden(6, True)  # ID скрыт

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(table.SelectionBehavior.SelectRows)

    # -----------------------
    # Сигналы
    # -----------------------
    def _connect_signals(self):
        self.ui.TrainerTableWidget.doubleClicked.connect(self.on_table_double_click)
        self.ui.TrainerTableWidget.itemClicked.connect(self.on_table_item_clicked)

        self.ui.SearchLastNameEdit_2.textChanged.connect(self.on_search_last_name_changed)
        self.ui.SearchPhoneEdit_2.textChanged.connect(self.on_search_phone_changed)

        try:
            self.ui.AddTrainerBtn.clicked.connect(self.add_new_trainer)
        except AttributeError:
            logger.warning("AddTrainerBtn not found, reset form functionality disabled/needs different connection")

        self.ui.SaveTrainerBtn.clicked.connect(self.save_trainer)
        self.ui.DeleteTrainerBtn.clicked.connect(self.delete_trainer)

        # Фото
        try:
            self.ui.PhotoTrainerE.clicked.connect(self.on_photo_clicked)
        except AttributeError:
            self.ui.PhotoTrainerE.mousePressEvent = lambda ev: self.on_photo_clicked()

        # Тип тренера
        self.ui.TrainerTypeComboBox.currentIndexChanged.connect(self.on_trainer_type_changed)

        try:
            self.ui.DeletePhotoTrainerBtn.clicked.connect(self.on_delete_photo_clicked)
        except AttributeError:
            logger.warning("DeletePhotoTrainerBtn not found")

    # -----------------------
    # Загрузка данных
    # -----------------------
    def load_trainer_types(self):
        try:
            combo = self.ui.TrainerTypeComboBox
            combo.clear()
            combo.addItem("Выберите тип", None)
            types = trainer_type_get_all()
            for t in types:
                combo.addItem(t.get("trainer_type_name") or "Не указан", t.get("trainer_type_id"))
        except Exception as e:
            logger.exception("load_trainer_types failed: %s", e)

    def load_trainers(self):
        try:
            rows = trainer_get_all()
            self._fill_table_from_list(rows)
        except Exception:
            logger.exception("load_trainers crashed")

    def _fill_table_from_list(self, trainers_list):
        table = self.ui.TrainerTableWidget
        table.setRowCount(0)
        for rnum, tr in enumerate(trainers_list):
            try:
                table.insertRow(rnum)
                type_name = ''
                tt = trainer_type_get_by_id(tr.get("trainer_type_id"))
                if tt:
                    type_name = tt.get("trainer_type_name", "")
                data = [
                    tr.get("last_name", ""),
                    tr.get("first_name", ""),
                    tr.get("middle_name", ""),
                    tr.get("phone", ""),
                    tr.get("email", ""),
                    type_name,
                    str(tr.get("trainer_id", ""))
                ]
                for col, value in enumerate(data):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    table.setItem(rnum, col, item)
            except Exception:
                logger.exception("Failed to populate row %s in trainer table", rnum)

    # -----------------------
    # Работа с фото
    # -----------------------
    def on_photo_clicked(self):
        self.load_photo()

    def load_photo(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.ui.centralwidget, "Выберите фото тренера", "",
                "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)"
            )
            if not path:
                return

            img = QImage(path)
            if img.isNull():
                QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Не удалось загрузить изображение.")
                return

            # Масштабируем под размер виджета
            w, h = self.ui.PhotoTrainerE.width(), self.ui.PhotoTrainerE.height()
            scaled = img.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)

            # Конвертируем для хранения
            bts = qimage_to_bytes(scaled, "PNG")
            self.current_photo_data = bts

            # Показываем в виджете
            pix = QPixmap()
            pix.loadFromData(bts)
            self.ui.PhotoTrainerE.setPixmap(pix)
        except Exception as e:
            logger.exception("load_photo failed: %s", e)
            QMessageBox.critical(self.ui.centralwidget, "Ошибка", f"Не удалось загрузить фото: {e}")

    def clear_photo(self):
        self.ui.PhotoTrainerE.clear()
        self.ui.PhotoTrainerE.setText("Фото")
        self.current_photo_data = None

    def on_delete_photo_clicked(self):
        """Удаляет фото тренера, если оно есть."""
        if self.current_photo_data:
            confirm = QMessageBox.question(
                self.ui.centralwidget,
                "Удаление фото",
                "Вы уверены, что хотите удалить фото тренера?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.clear_photo()
        else:
            QMessageBox.information(self.ui.centralwidget, "Информация", "Фото отсутствует")

    # -----------------------
    # CRUD / редактирование
    # -----------------------

    def add_new_trainer(self):
        self.reset_form()
        self.ui.widget_trainer.setVisible(True)

    def reset_form(self):
        self.current_trainer = None
        self.current_photo_data = None
        self.ui.TrainerTableWidget.clearSelection()
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

            self.ui.SaveTrainerBtn.setText("Сохранить (Новый)")
            self.ui.DeleteTrainerBtn.setEnabled(False)
            try:
                self.ui.AddTrainerBtn.setText("Новый тренер (Сброс)")
            except AttributeError:
                pass
            self.ui.LastNameTrainerEdit.setFocus()
        except Exception:
            logger.exception("reset_form encountered problem")

    def get_selected_trainer_id(self):
        try:
            r = self.ui.TrainerTableWidget.currentRow()
            if r >= 0:
                item = self.ui.TrainerTableWidget.item(r, 6)
                if item:
                    return int(item.text())
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
            self.ui.widget_trainer.setVisible(True)
            if not trainer_id:
                trainer_id = self.get_selected_trainer_id()
            if not trainer_id:
                QMessageBox.warning(self.ui.centralwidget, "Предупреждение", "Выберите тренера")
                return

            tr = trainer_get_by_id(trainer_id)
            if not tr:
                QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Тренер не найден")
                return



            self.current_trainer = tr
            self.ui.LastNameTrainerEdit.setText(str(tr.get("last_name", "")))
            self.ui.FirstNameTrainerEdit.setText(str(tr.get("first_name", "")))
            self.ui.MidleNameTrainerEdit.setText(str(tr.get("middle_name", "")))
            self.ui.PhoneTrainer.setText(str(tr.get("phone", "")))
            self.ui.EmailTrainerEdit.setText(str(tr.get("email", "")))
            self.ui.IdTrainerE.setText(str(tr.get("trainer_id", "")))

            tt_id = tr.get("trainer_type_id")
            if tt_id:
                idx = self.ui.TrainerTypeComboBox.findData(tt_id)
                if idx >= 0:
                    self.ui.TrainerTypeComboBox.setCurrentIndex(idx)

            photo = tr.get("photo")
            if photo:
                pix = QPixmap()
                pix.loadFromData(photo)
                self.ui.PhotoTrainerE.setPixmap(pix)
                self.current_photo_data = photo
            else:
                self.clear_photo()

            self.ui.DeleteTrainerBtn.setEnabled(True)
            self.ui.SaveTrainerBtn.setText("Обновить")
            try:
                self.ui.AddTrainerBtn.setText("Новый тренер (Сброс)")
            except AttributeError:
                pass
        except Exception as e:
            logger.exception("edit_trainer failed: %s", e)
            QMessageBox.critical(self.ui.centralwidget, "Ошибка", f"Не удалось загрузить данные тренера: {e}")

    def save_trainer(self):
        try:
            last = self.ui.LastNameTrainerEdit.text().strip()
            first = self.ui.FirstNameTrainerEdit.text().strip()
            middle = self.ui.MidleNameTrainerEdit.text().strip()
            phone = self.ui.PhoneTrainer.text().strip()
            trainer_type_id = self.ui.TrainerTypeComboBox.currentData()
            email = self.ui.EmailTrainerEdit.text().strip()

            if not all([last, first, trainer_type_id, phone]):
                QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Заполните Фамилию, Имя, Тип и Телефон!")
                return

            if self.current_trainer:
                trainer_id = self.current_trainer.get("trainer_id")
                ok = trainer_update(trainer_id, last, first, middle, self.current_photo_data, phone, trainer_type_id, email)
                if ok:
                    QMessageBox.information(self.ui.centralwidget, "Успех", "Данные тренера обновлены!")
            else:
                new_id = trainer_create(last, first, middle, self.current_photo_data, phone, trainer_type_id, email)
                if new_id:
                    QMessageBox.information(self.ui.centralwidget, "Успех", "Тренер успешно добавлен!")
                else:
                    QMessageBox.critical(self.ui.centralwidget, "Ошибка", "Не удалось добавить тренера")

            self.load_trainers()
            self.reset_form()
            self.ui.widget_trainer.setVisible(False)
        except Exception as e:
            logger.exception("save_trainer failed: %s", e)
            QMessageBox.critical(self.ui.centralwidget, "Ошибка", f"Не удалось сохранить тренера: {e}")

    def delete_trainer(self):
        try:
            if not self.current_trainer:
                QMessageBox.warning(self.ui.centralwidget, "Ошибка", "Нет выбранного тренера для удаления")
                return
            trainer_id = self.current_trainer.get("trainer_id")
            trainer_name = f"{self.current_trainer.get('last_name','')} {self.current_trainer.get('first_name','')}"
            reply = QMessageBox.question(self.ui.centralwidget, "Подтверждение удаления",
                                         f"Вы уверены, что хотите удалить тренера '{trainer_name}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            ok = trainer_delete(trainer_id)
            if ok:
                QMessageBox.information(self.ui.centralwidget, "Успех", "Тренер удален!")
                self.load_trainers()
                self.reset_form()
                self.ui.widget_trainer.setVisible(False)
            else:
                QMessageBox.critical(self.ui.centralwidget, "Ошибка", "Не удалось удалить тренера")
        except Exception as e:
            logger.exception("delete_trainer failed: %s", e)
            QMessageBox.critical(self.ui.centralwidget, "Ошибка", f"Не удалось удалить тренера: {e}")

    # -----------------------
    # Поиск
    # -----------------------
    def on_search_last_name_changed(self, text):
        txt = text.strip()
        try:
            if not txt and not self.ui.SearchPhoneEdit_2.text().strip():
                self.load_trainers()
                return
            rows = trainer_search_by_last_name(txt)
            self._fill_table_from_list(rows)
        except Exception:
            logger.exception("on_search_last_name_changed failed")

    def on_search_phone_changed(self, text):
        txt = text.strip()
        try:
            if not txt and not self.ui.SearchLastNameEdit_2.text().strip():
                self.load_trainers()
                return
            rows = trainer_search_by_phone(txt)
            self._fill_table_from_list(rows)
        except Exception:
            logger.exception("on_search_phone_changed_failed")

    # -----------------------
    # Тип тренера
    # -----------------------
    def on_trainer_type_changed(self, index):
        try:
            tid = self.ui.TrainerTypeComboBox.itemData(index)
            if not tid:
                self.ui.RateE.clear()
                return
            tt = trainer_type_get_by_id(tid)
            if tt:
                rate = tt.get("rate")
                self.ui.RateE.setText(f"{rate} руб." if rate is not None else "")
            else:
                self.ui.RateE.clear()
        except Exception:
            logger.exception("on_trainer_type_changed failed")

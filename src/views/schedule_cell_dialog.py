from datetime import time, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialogButtonBox
)
from src.models.group_trainings import GroupTraining

class ScheduleCellDialog(QDialog):
    def __init__(self, parent, training_date, time_slot):
        super().__init__(parent)
        self.training_date = training_date
        self.time_slot = time_slot
        self.selected_training = None

        self.setWindowTitle(
            f"{training_date.strftime('%d.%m.%Y')} — {time_slot}"
        )
        self.setFixedSize(600, 320)

        self._setup_ui()
        self._load_trainings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Тренировка", "Тренер", "Зал", "Вместимость", "ID"
        ])
        self.table.setColumnHidden(4, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)

        layout.addWidget(self.table)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def _load_trainings(self):
        trainings = GroupTraining.get_all_in_week(self.training_date, self.training_date)

        filtered = []
        for t in trainings:
            if isinstance(t.start_time, time):
                t_time_str = t.start_time.strftime("%H:%M")
            elif isinstance(t.start_time, timedelta):
                total_seconds = int(t.start_time.total_seconds())
                t_time_str = f"{total_seconds // 3600:02d}:{(total_seconds % 3600) // 60:02d}"
            else:
                t_time_str = str(t.start_time)[:5]

            if t_time_str == self.time_slot:
                filtered.append(t)

        self.table.setRowCount(len(filtered))

        for row, t in enumerate(filtered):
            self.table.setItem(row, 0, QTableWidgetItem(t.service_name))
            self.table.setItem(row, 1, QTableWidgetItem(t.trainer_name))
            self.table.setItem(row, 2, QTableWidgetItem(t.hall_name))
            self.table.setItem(row, 3, QTableWidgetItem(str(t.capacity)))
            self.table.setItem(row, 4, QTableWidgetItem(str(t.group_training_id)))

    def on_row_double_clicked(self, row, _):
        training_id_item = self.table.item(row, 4)
        if not training_id_item:
            return

        training_id = int(training_id_item.text())
        self.selected_training = GroupTraining.get_by_id(training_id)
        self.accept()
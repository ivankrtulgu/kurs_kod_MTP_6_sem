"""
Issue Book Dialog module.

Provides a dialog for issuing a physical book copy to a reader.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService


class IssueBookDialog(QDialog):
    """
    Dialog for issuing a book item to a reader.
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Выдача экземпляра")
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Reader ID input
        self.reader_id_input = QLineEdit()
        self.reader_id_input.setPlaceholderText("Введите ID читателя")
        form.addRow("ID Читателя:", self.reader_id_input)

        # Inventory Number input
        self.inv_num_input = QLineEdit()
        self.inv_num_input.setPlaceholderText("Например: 1001")
        form.addRow("Инв. № экземпляра:", self.inv_num_input)

        # Loan period input
        self.days_input = QSpinBox()
        self.days_input.setRange(1, 365)
        self.days_input.setValue(14)
        form.addRow("Срок выдачи (дней):", self.days_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("Выдать")
        self.btn_confirm.clicked.connect(self._handle_confirm)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def _handle_confirm(self):
        try:
            # Validate inputs
            reader_id = int(self.reader_id_input.text())
            inv_num = self.inv_num_input.text().strip()
            days = self.days_input.value()

            if not inv_num:
                raise ValueError("Инвентарный номер не может быть пустым")

            self._service.issue_item_by_inv(inv_num, reader_id, days)
            QMessageBox.information(self, "Успех", "Книга успешно выдана")
            self.accept()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка системы", f"Не удалось выдать книгу: {str(e)}")


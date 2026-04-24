"""
Return Book Dialog module.

Provides a dialog for returning a physical book copy.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService


class ReturnBookDialog(QDialog):
    """
    Dialog for returning a book item.
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Возврат экземпляра")
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Inventory Number input
        self.inv_num_input = QLineEdit()
        self.inv_num_input.setPlaceholderText("Введите инв. №")
        form.addRow("Инв. № экземпляра:", self.inv_num_input)

        # Condition input
        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Например: Хорошее, порвана обложка")
        self.condition_input.setText("Хорошее")
        form.addRow("Состояние при возврате:", self.condition_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("Вернуть")
        self.btn_confirm.clicked.connect(self._handle_confirm)
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def _handle_confirm(self):
        try:
            inv_num = self.inv_num_input.text().strip()
            condition = self.condition_input.text().strip()

            if not inv_num:
                raise ValueError("Инвентарный номер не может быть пустым")

            # Similarly to IssueBookDialog, we need to find the item_id.
            # I'll use a hypothetical `return_item_by_inv` method in the service.
            self._service.return_item_by_inv(inv_num, condition)
            
            QMessageBox.information(self, "Успех", "Книга успешно возвращена")
            self.accept()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка системы", f"Не удалось вернуть книгу: {str(e)}")

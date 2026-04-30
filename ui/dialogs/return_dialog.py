"""
Return Book Dialog module.

Provides a dialog for returning a physical book copy.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService
from ui.style_manager import StyleManager

class ReturnBookDialog(QDialog):
    """
    Dialog for returning a book item.
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        self.setWindowTitle("Возврат экземпляра")
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main form group
        form_group = QGroupBox(" Данные возврата")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Inventory Number input
        self.inv_num_input = QLineEdit()
        self.inv_num_input.setPlaceholderText("Введите инв. №")
        form_layout.addRow("Инв. № экземпляра:", self.inv_num_input)

        # Condition input
        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Например: Хорошее, порвана обложка")
        self.condition_input.setText("Хорошее")
        form_layout.addRow("Состояние при возврате:", self.condition_input)

        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
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


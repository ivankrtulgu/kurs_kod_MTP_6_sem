"""
Return Book Widget module.

Provides a widget for returning a physical book copy within an MDI environment.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService
from ui.style_manager import StyleManager

class ReturnBookWidget(QWidget):
    """
    Widget for returning a book item.
    Designed to be hosted within a QMdiSubWindow.
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        self.setWindowTitle("Возврат экземпляра")
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
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def set_item(self, inv_num: str):
        """Pre-fill the form with a specific item's inventory number."""
        self.inv_num_input.setText(inv_num)
        self.inv_num_input.setReadOnly(True)

    def _close_window(self):
        """Close the MDI subwindow containing this widget."""
        from PyQt5.QtWidgets import QMdiSubWindow
        parent = self.parent()
        if isinstance(parent, QMdiSubWindow):
            parent.close()
        else:
            self.close()

    def _handle_confirm(self):
        try:
            inv_num = self.inv_num_input.text().strip()
            condition = self.condition_input.text().strip()

            if not inv_num:
                raise ValueError("Инвентарный номер не может быть пустым")

            self._service.return_item_by_inv(inv_num, condition)
            
            QMessageBox.information(self, "Успех", "Книга успешно возвращена")
            self._close_window()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка системы", f"Не удалось вернуть книгу: {str(e)}")

"""
Issue Book Widget module.

Provides a widget for issuing a physical book copy to a reader within an MDI environment.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService
from ui.style_manager import StyleManager

class IssueBookWidget(QWidget):
    """
    Widget for issuing a book item to a reader.
    Designed to be hosted within a QMdiSubWindow.
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        self.setWindowTitle("Выдача экземпляра")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main form group
        form_group = QGroupBox(" Данные выдачи")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Reader selection row
        reader_layout = QHBoxLayout()
        reader_layout.setSpacing(10)
        self.reader_id_input = QLineEdit()
        self.reader_id_input.setPlaceholderText("ID читателя")
        self.reader_id_input.setFixedWidth(100)
        
        self.lbl_reader_name = QLabel("Выберите читателя...")
        self.lbl_reader_name.setMinimumWidth(200)
        
        self.btn_select_reader = QPushButton("Выбрать...")
        self.btn_select_reader.clicked.connect(self._on_select_reader_clicked)
        
        self.btn_clear_reader = QPushButton("Очистить")
        self.btn_clear_reader.clicked.connect(self._clear_reader)
        
        reader_layout.addWidget(self.reader_id_input)
        reader_layout.addWidget(self.lbl_reader_name)
        reader_layout.addWidget(self.btn_select_reader)
        reader_layout.addWidget(self.btn_clear_reader)
        form_layout.addRow("Читатель:", reader_layout)

        # Inventory Number input
        self.inv_num_input = QLineEdit()
        self.inv_num_input.setPlaceholderText("Например: 1001")
        form_layout.addRow("Инв. № экземпляра:", self.inv_num_input)

        # Loan period input
        self.days_input = QSpinBox()
        self.days_input.setRange(1, 365)
        self.days_input.setValue(14)
        form_layout.addRow("Срок выдачи (дней):", self.days_input)

        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_confirm = QPushButton("Выдать")
        self.btn_confirm.clicked.connect(self._handle_confirm)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def _on_select_reader_clicked(self):
        """Open reader selection window."""
        main_window = self.window()
        if hasattr(main_window, '_open_reader_list_for_selection'):
            self._opened_selection_widget = main_window._open_reader_list_for_selection(self.set_selected_reader)
            main_window.add_close_dependency(self, self._opened_selection_widget)
        else:
            QMessageBox.critical(self, "Ошибка", "Система выбора читателей не доступна")

    def set_selected_reader(self, reader_id: int, reader_name: str):
        """Callback method to update UI with selected reader."""
        self.reader_id_input.setText(str(reader_id))
        self.lbl_reader_name.setText(reader_name)

    def _clear_reader(self):
        """Clear selected reader data."""
        self.reader_id_input.clear()
        self.lbl_reader_name.setText("Выберите читателя...")

    def set_item(self, inv_num: str):
        """Pre-fill the form with a specific item's inventory number."""
        self.inv_num_input.setText(inv_num)
        self.inv_num_input.setReadOnly(True) # Prevent changing when opened from card

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
            self.close()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка системы", f"Не удалось выдать книгу: {str(e)}")

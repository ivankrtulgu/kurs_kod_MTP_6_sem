"""
Add Items Widget module.

Provides a widget for adding multiple physical copies of a specific book,
designed to be hosted within an MDI subwindow.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QMessageBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt, QVariant, pyqtSignal
from core.services.book_service import BookService
from core.services.inventory_service import InventoryService
from ui.style_manager import StyleManager

class AddItemsWidget(QWidget):
    """
    Widget for adding multiple physical copies of a book.
    Designed to be hosted within a QMdiSubWindow.
    """
    
    # Signal emitted when items are successfully added
    items_added = pyqtSignal()

    def __init__(self, book_service: BookService, inventory_service: InventoryService, parent=None):
        super().__init__(parent)
        self._book_service = book_service
        self._inventory_service = inventory_service
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main form group
        form_group = QGroupBox(" Данные добавления")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # Book selection
        self.book_info_edit = QLineEdit()
        self.book_info_edit.setReadOnly(True)
        self.book_info_edit.setPlaceholderText("Нажмите 'Выбрать...', чтобы выбрать книгу")
        
        self.btn_select_book = QPushButton("Выбрать...")
        self.btn_select_book.clicked.connect(self._on_select_book_clicked)
        
        self.btn_clear_book = QPushButton("Очистить")
        self.btn_clear_book.clicked.connect(self._on_clear_book)
        
        book_layout = QHBoxLayout()
        book_layout.setSpacing(10)
        book_layout.addWidget(self.book_info_edit)
        book_layout.addWidget(self.btn_select_book)
        book_layout.addWidget(self.btn_clear_book)
        form_layout.addRow("Произведение:", book_layout)

        # Location input
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Напр: ЗАЛ-1-ПОЛКА-5")
        form_layout.addRow("Местоположение:", self.location_input)

        # Quantity input
        self.count_input = QSpinBox()
        self.count_input.setRange(1, 1000)
        self.count_input.setValue(1)
        form_layout.addRow("Количество экземпляров:", self.count_input)

        # Starting inventory number (Optional)
        self.start_inv_input = QLineEdit()
        self.start_inv_input.setPlaceholderText("Оставить пустым для автонумерации")
        form_layout.addRow("Начать с № (опц.):", self.start_inv_input)

        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.btn_confirm = QPushButton("Добавить")
        self.btn_confirm.clicked.connect(self._handle_confirm)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

    def _on_clear_book(self):
        """Clear the selected book."""
        self._selected_book_id = None
        self.book_info_edit.clear()

    def _on_select_book_clicked(self):
        """Request the main window to open the BookListWidget in selection mode."""
        parent_window = self.window()
        if hasattr(parent_window, '_open_book_list_for_selection'):
            self._opened_selection_widget = parent_window._open_book_list_for_selection(self.set_selected_book)
            parent_window.add_close_dependency(self, self._opened_selection_widget)
        else:
            QMessageBox.critical(self, "Ошибка", "Система выбора книг не доступна")

    def set_selected_book(self, book_id: int, book_text: str):
        """Set the selected book after selection from the list."""
        self._selected_book_id = book_id
        self.book_info_edit.setText(book_text)

    def _handle_confirm(self):
        try:
            if not hasattr(self, '_selected_book_id') or self._selected_book_id is None:
                raise ValueError("Пожалуйста, выберите произведение")

            count = self.count_input.value()
            location = self.location_input.text().strip()
            
            start_inv_text = self.start_inv_input.text().strip()
            start_inv = None
            if start_inv_text:
                if not start_inv_text.isdigit():
                    raise ValueError("Начальный номер должен быть целым числом")
                start_inv = int(start_inv_text)

            self._inventory_service.add_items(
                book_id=self._selected_book_id, 
                count=count, 
                start_inv=start_inv,
                location=location
            )
            
            QMessageBox.information(self, "Успех", f"Добавлено {count} экз. произведения")
            self.items_added.emit()
            
            # CORRECTLY close the MDI sub-window, not the main window
            # In PyQt, the widget's parent in an MDI area is the QMdiSubWindow
            parent = self.parentWidget()
            if parent:
                from PyQt5.QtWidgets import QMdiSubWindow
                if isinstance(parent, QMdiSubWindow):
                    parent.close()
                else:
                    # Fallback: try to find the MDI subwindow in the parent chain
                    curr = parent
                    while curr:
                        if isinstance(curr, QMdiSubWindow):
                            curr.close()
                            break
                        curr = curr.parentWidget()

        except ValueError as e:
            QMessageBox.critical(self, "Ошибка ввода", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка системы", f"Не удалось добавить экземпляры: {str(e)}")




"""
Inventory List Widget module.

Provides a widget for viewing the list of physical book copies in an MDI environment.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableView
from PyQt5.QtCore import pyqtSignal
from ui.models import InventoryTableModel
from core.services.inventory_service import InventoryService


class InventoryListWidget(QWidget):
    """
    Widget for displaying the inventory table.
    Designed to be hosted within a QMdiSubWindow.
    """

    # Signal to notify the parent window that data was refreshed
    data_refreshed = pyqtSignal()

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Table setup
        self.table_model = InventoryTableModel(self._service)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        
        # Refresh button
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)

        layout.addWidget(self.table_view)
        layout.addWidget(self.btn_refresh)

    def refresh_list(self, book_id: int = 1):
        """
        Refresh the table data. 
        Note: book_id=1 is a placeholder; in a real app, this would depend on the current book selection.
        """
        self.table_model.refresh_data(book_id)
        self.data_refreshed.emit()

    def get_model(self) -> InventoryTableModel:
        """Return the underlying table model."""
        return self.table_model

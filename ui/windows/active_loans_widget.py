"""
Active Loans Widget module.

Provides a table view of all currently active book loans in the library.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal
from typing import Any
from ui.models import ActiveLoansTableModel
from core.services.inventory_service import InventoryService

class ActiveLoansWidget(QWidget):
    """
    Widget for displaying the list of active loans.
    Designed to be hosted within a QMdiSubWindow.
    """

    data_refreshed = pyqtSignal()

    def __init__(self, inventory_service: InventoryService, book_service: Any, parent=None):
        super().__init__(parent)
        self._inventory_service = inventory_service
        self._book_service = book_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Filter area
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Фильтр:")
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All", "Active", "Closed", "Overdue"])
        self.combo_filter.setCurrentText("Active")
        self.combo_filter.currentTextChanged.connect(self.refresh_list)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.combo_filter)
        filter_layout.addStretch()
        
        # Table setup
        self.table_model = ActiveLoansTableModel(self._inventory_service, self._book_service)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        
        from PyQt5.QtWidgets import QHeaderView
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Refresh button
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)

        layout.addLayout(filter_layout)
        layout.addWidget(self.table_view)
        layout.addWidget(self.btn_refresh)
        
        # Initial data load
        self.refresh_list()

    def refresh_list(self):
        """Refresh the loan table data with selected filter."""
        filter_type = self.combo_filter.currentText()
        self.table_model.refresh_data(filter_type)
        self.data_refreshed.emit()

    def get_model(self) -> ActiveLoansTableModel:
        """Return the underlying table model."""
        return self.table_model

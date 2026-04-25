"""
Reader List Widget module.

Provides a widget for viewing and managing library readers in an MDI environment.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableView, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from ui.models import ReaderTableModel
from core.services.inventory_service import InventoryService

class ReaderListWidget(QWidget):
    """
    Widget for displaying the reader table.
    Designed to be hosted within a QMdiSubWindow.
    """

    # Signal to notify the parent window that data was refreshed
    data_refreshed = pyqtSignal()
    # Signal for reader selection
    reader_selected = pyqtSignal(int)

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self.selection_mode = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Table setup
        self.table_model = ReaderTableModel(self._service)
        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        
        from PyQt5.QtWidgets import QHeaderView
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Handle double click
        self.table_view.doubleClicked.connect(self._on_item_double_clicked)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Добавить читателя")
        self.btn_add.clicked.connect(self._on_add_clicked)
        
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_refresh)

        layout.addWidget(self.table_view)
        layout.addLayout(btn_layout)
        
        # Initial data load
        self.refresh_list()

    def _on_add_clicked(self):
        """Open the add reader window."""
        from ui.windows.add_reader_widget import AddReaderWidget
        main_window = self.window()
        if hasattr(main_window, '_open_mdi_subwindow'):
            main_window._open_mdi_subwindow(AddReaderWidget, self._service)

    def _on_item_double_clicked(self, index):
        """Handle double click on a reader."""
        row = index.row()
        reader_id = self.table_model._readers[row].id
        
        if self.selection_mode:
            # Trigger selection signal
            self.reader_selected.emit(reader_id)
        else:
            # Edit reader
            main_window = self.window()
            if hasattr(main_window, '_open_mdi_subwindow'):
                from ui.windows.add_reader_widget import AddReaderWidget
                main_window._open_mdi_subwindow(AddReaderWidget, self._service, reader_id=reader_id)

    def refresh_list(self):
        """Refresh the reader table data."""
        self.table_model.refresh_data()
        self.data_refreshed.emit()

    def get_model(self) -> ReaderTableModel:
        """Return the underlying table model."""
        return self.table_model

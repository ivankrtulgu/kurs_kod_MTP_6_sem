"""
UI models module.

Provides specialized table models for displaying inventory data in PyQt5 widgets.
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List
from core.models.inventory import BookItem
from core.services.inventory_service import InventoryService


class InventoryTableModel(QAbstractTableModel):
    """
    PyQt5 Table Model for displaying physical book copies (BookItems).
    
    Columns:
        0: Inventory Number
        1: Status
        2: Location
        3: Book ID (Edition)
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self._items: List[BookItem] = []
        self._headers = ["Инвентарный №", "Статус", "Местоположение", "ID Издания"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        item = self._items[index.row()]
        col = index.column()

        if col == 0:
            return item.inventory_number
        elif col == 1:
            return item.status.value
        elif col == 2:
            return item.location if item.location else "Не указано"
        elif col == 3:
            return str(item.book_id)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh_data(self, book_id: int):
        """
        Fetch fresh data from the service for a specific book.
        """
        self.beginResetModel()
        self._items = self._service.get_items_by_book(book_id)
        self.endResetModel()

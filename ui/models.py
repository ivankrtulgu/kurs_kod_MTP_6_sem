"""
UI models module.

Provides specialized table models for displaying inventory data in PyQt5 widgets.
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List
from core.models.inventory import BookItem, Reader
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
            # Translate status to Russian
            status_map = {
                "AVAILABLE": "Доступен",
                "LOANED": "Выдан",
                "LOST": "Утерян",
                "REPAIR": "В ремонте",
                "WRITTEN_OFF": "Списан"
            }
            return status_map.get(item.status.value, item.status.value)
        elif col == 2:
            return item.location if item.location else "Не указано"
        elif col == 3:
            return str(item.book_id)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh_data(self, book_id: int | None = None):
        """
        Fetch fresh data from the service. 
        If book_id is provided, fetch items for that book.
        If book_id is None, fetch all items in the fund.
        """
        self.beginResetModel()
        if book_id is not None:
            self._items = self._service.get_items_by_book(book_id)
        else:
            self._items = self._service.get_all_items()
        self.endResetModel()

class ReaderTableModel(QAbstractTableModel):
    """
    PyQt5 Table Model for displaying library readers.
    
    Columns:
        0: ID
        1: Full Name
        2: Phone
        3: Status
    """

    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self._readers: List[Reader] = []
        self._headers = ["ID", "ФИО", "Телефон", "Статус"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._readers)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        reader = self._readers[index.row()]
        col = index.column()

        if col == 0:
            return str(reader.id)
        elif col == 1:
            return reader.full_name
        elif col == 2:
            return reader.phone
        elif col == 3:
            return "Активен" if reader.is_active else "Неактивен"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh_data(self):
        """Fetch fresh reader data."""
        self.beginResetModel()
        self._readers = self._service.get_all_readers()
        self.endResetModel()


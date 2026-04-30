"""
UI models module.

Provides specialized table models for displaying inventory data in PyQt5 widgets.
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List, Any
from datetime import datetime
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
        1: Surname
        2: First Name
        3: Patronymic
        4: Phone
        5: Status
    """
    
    def __init__(self, service: InventoryService, parent=None):
        super().__init__(parent)
        self._service = service
        self._readers: List[Reader] = []
        self._headers = ["ID", "Фамилия", "Имя", "Отчество", "Телефон", "Статус"]
    
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
            return reader.last_name
        elif col == 2:
            return reader.first_name
        elif col == 3:
            return reader.middle_name
        elif col == 4:
            return reader.phone
        elif col == 5:
            status_map = {
                "active": "Активен",
                "blocked": "Заблокирован",
                "expired": "Просрочен"
            }
            return status_map.get(reader.status, reader.status)
        
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

class ActiveLoansTableModel(QAbstractTableModel):
    """
    PyQt5 Table Model for displaying book loans with filtering.
    
    Columns:
        0: Inventory Number
        1: Book Title
        2: Reader Name
        3: Issue Date
        4: Due Date
        5: Actual Return Date
    """

    def __init__(self, inventory_service: InventoryService, book_service: Any, parent=None):
        super().__init__(parent)
        self._inventory_service = inventory_service
        self._book_service = book_service
        self._all_loans: List[LoanRecord] = []
        self._filtered_loans: List[LoanRecord] = []
        self._headers = ["Инв. №", "Произведение", "Читатель", "Дата выдачи", "Срок возврата", "Факт. возврат"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._filtered_loans)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        loan = self._filtered_loans[index.row()]
        col = index.column()

        # Resolve related entities
        item = self._inventory_service._repo.get_item_by_id(loan.item_id)
        reader = self._inventory_service._repo.get_reader_by_id(loan.reader_id)
        book = self._book_service.get_book_by_id(item.book_id) if item else None
        
        if col == 0:
            return item.inventory_number if item else "???"
        elif col == 1:
            return f"{book.author}. {book.title}" if book else "Неизвестно"
        elif col == 2:
            if reader:
                return f"{reader.last_name} {reader.first_name} {reader.middle_name}".strip()
            return "Неизвестно"
        elif col == 3:
            return loan.issue_date.strftime("%d.%m.%Y")

        elif col == 4:
            return loan.due_date.strftime("%d.%m.%Y")
        elif col == 5:
            return loan.return_date.strftime("%d.%m.%Y") if loan.return_date else "—"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh_data(self, filter_type: str = "All"):
        """
        Fetch loan data and apply filters.
        filter_type: 'All', 'Active', 'Closed', 'Overdue'
        """
        self.beginResetModel()
        self._all_loans = self._inventory_service.get_all_loans()
        
        now = datetime.now()
        if filter_type == "Active":
            self._filtered_loans = [l for l in self._all_loans if not l.return_date]
        elif filter_type == "Closed":
            self._filtered_loans = [l for l in self._all_loans if l.return_date]
        elif filter_type == "Overdue":
            self._filtered_loans = [l for l in self._all_loans if not l.return_date and l.due_date < now]
        else: # All
            self._filtered_loans = self._all_loans
            
        self.endResetModel()



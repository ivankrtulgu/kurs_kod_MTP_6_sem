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
    Caches resolved data to prevent N+1 query freezes.
    """

    def __init__(self, inventory_service: InventoryService, book_service: Any, parent=None):
        super().__init__(parent)
        self._inventory_service = inventory_service
        self._book_service = book_service
        self._cached_data = [] 
        self._headers = ["Инв. №", "Произведение", "Читатель", "Дата выдачи", "Срок возврата", "Факт. возврат"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._cached_data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        row_data = self._cached_data[index.row()]
        col = index.column()

        if col == 0:
            return row_data["inv"]
        elif col == 1:
            return row_data["book"]
        elif col == 2:
            return row_data["reader"]
        elif col == 3:
            return row_data["issue"]
        elif col == 4:
            return row_data["due"]
        elif col == 5:
            return row_data["return"]

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh_data(self, filter_type: str = "All"):
        """
        Fetch loan data, resolve entities, and cache results.
        """
        self.beginResetModel()
        self._cached_data = []
        
        all_loans = self._inventory_service.get_all_loans()
        now = datetime.now()
        
        if filter_type == "Active":
            loans = [loan for loan in all_loans if not loan.return_date]
        elif filter_type == "Closed":
            loans = [loan for loan in all_loans if loan.return_date]
        elif filter_type == "Overdue":
            loans = [loan for loan in all_loans if not loan.return_date and loan.due_date < now]
        else: 
            loans = all_loans

        # Pre-compute display data
        for loan in loans:
            item = self._inventory_service._repo.get_item_by_id(loan.item_id)
            reader = self._inventory_service._repo.get_reader_by_id(loan.reader_id)
            
            book_title = "Неизвестно"
            inv_num = "???"
            reader_name = "Неизвестно"
            
            if item:
                inv_num = item.inventory_number
                book = self._book_service.get_book_by_id(item.book_id)
                if book:
                    book_title = f"{book.author}. {book.title}"
            
            if reader:
                reader_name = f"{reader.last_name} {reader.first_name} {reader.middle_name}".strip()
                
            self._cached_data.append({
                "inv": inv_num,
                "book": book_title,
                "reader": reader_name,
                "issue": loan.issue_date.strftime("%d.%m.%Y"),
                "due": loan.due_date.strftime("%d.%m.%Y"),
                "return": loan.return_date.strftime("%d.%m.%Y") if loan.return_date else "—"
            })
            
        self.endResetModel()



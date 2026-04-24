"""
Inventory List Widget module.

Provides a hierarchical view (Tree) for viewing the list of physical book copies.
Books act as folders, and their physical copies act as files.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal, Qt
from core.services.inventory_service import InventoryService
from core.services.book_service import BookService
from core.models.inventory import ItemStatus

class InventoryListWidget(QWidget):
    """
    Widget for displaying the inventory as a hierarchical tree.
    Designed to be hosted within a QMdiSubWindow.
    """

    # Status translation map
    STATUS_MAP = {
        ItemStatus.AVAILABLE: "Доступен",
        ItemStatus.LOANED: "Выдан",
        ItemStatus.REPAIR: "В ремонте",
        ItemStatus.LOST: "Утерян"
    }

    data_refreshed = pyqtSignal()

    def __init__(self, inventory_service: InventoryService, book_service: BookService, parent=None):
        super().__init__(parent)
        self._inventory_service = inventory_service
        self._book_service = book_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Tree setup
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Наименование / №", "Статус / ISBN", "Местоположение"])
        
        # Stretch columns to fill width
        self.tree.header().setSectionResizeMode(QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)

        # Refresh button
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)

        layout.addWidget(self.tree)
        layout.addWidget(self.btn_refresh)
        
        # Initial data load
        self.refresh_list()

    def refresh_list(self):
        """
        Refresh the tree data. 
        Groups physical items by their book (edition).
        """
        self.tree.clear()
        
        try:
            # Fetch all physical items
            all_items = self._inventory_service.get_all_items()
            
            # Group items by book_id
            groups = {}
            for item in all_items:
                groups.setdefault(item.book_id, []).append(item)
            
            # Sort groups by book_id (or could be sorted by title)
            for book_id in sorted(groups.keys()):
                # Resolve book details
                book = self._book_service.get_book_by_id(book_id)
                if not book:
                    title = f"Неизвестное произведение (ID: {book_id})"
                    isbn = "N/A"
                else:
                    title = f"{book.author}. {book.title}"
                    isbn = book.isbn or "N/A"
                
                # Create "Folder" for the book
                book_node = QTreeWidgetItem(self.tree)
                book_node.setText(0, title)
                book_node.setText(1, isbn)
                book_node.setText(2, f"Копий: {len(groups[book_id])}")
                book_node.setExpanded(False) # Folded by default
                
                # Create "Files" for each physical copy
                for item in groups[book_id]:
                    item_node = QTreeWidgetItem(book_node)
                    item_node.setText(0, f"Инв. № {item.inventory_number}")
                    
                    # Translate status
                    status_text = self.STATUS_MAP.get(item.status, item.status.value)
                    item_node.setText(1, status_text)
                    
                    item_node.setText(2, item.location if item.location else "Не указано")

            self.data_refreshed.emit()
            
        except Exception as e:
            print(f"Ошибка при загрузке инвентаря: {e}")

    def get_model(self):
        """Legacy method kept for compatibility, returns the tree widget."""
        return self.tree

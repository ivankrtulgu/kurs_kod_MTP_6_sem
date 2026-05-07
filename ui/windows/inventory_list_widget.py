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
from ui.style_manager import StyleManager
from ui.icon_manager import IconManager

class InventoryListWidget(QWidget):
    """
    Widget for displaying the inventory as a hierarchical tree.
    Designed to be hosted within a QMdiSubWindow.
    """
    WINDOW_TITLE = "Список экземпляров"

    # Status translation map
    STATUS_MAP = {
        ItemStatus.AVAILABLE: "Доступен",
        ItemStatus.LOANED: "Выдан",
        ItemStatus.REPAIR: "В ремонте",
        ItemStatus.LOST: "Утерян",
        ItemStatus.WRITTEN_OFF: "Списан"
    }

    data_refreshed = pyqtSignal()

    def __init__(self, inventory_service: InventoryService, book_service: BookService, parent=None):
        super().__init__(parent)
        self._inventory_service = inventory_service
        self._book_service = book_service
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        self.setWindowIcon(IconManager.get_default_icon())
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Tree setup
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Наименование / №", "Статус / ISBN", "Местоположение"])
        
        # Stretch columns to fill width
        self.tree.header().setSectionResizeMode(QHeaderView.Stretch)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)

        # Handle double click to open card
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Refresh button
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh_list)

        layout.addWidget(self.tree)
        layout.addWidget(self.btn_refresh)
        
        # Initial data load
        self.refresh_list()

    def _on_item_double_clicked(self, item: QTreeWidgetItem):
        """Handle double click on a tree item."""
        # If it's a child item (a physical copy), open its card
        if item.parent():
            # We need to find the item_id. 
            # Since we didn't store it in the node, we'll find it by inventory number.
            inv_num = item.text(0).replace("Инв. № ", "").strip()
            
            # Notify MainWindow to open the card
            # We assume the parent window is MainWindow
            main_window = self.window()
            if hasattr(main_window, '_open_book_item_card'):
                # Find item_id from inv_num via service
                try:
                    item_obj = self._inventory_service._find_item_by_inv(inv_num)
                    main_window._open_book_item_card(item_obj.id)
                except Exception as e:
                    print(f"Ошибка при открытии карточки: {e}")

    def refresh_list(self):
        """
        Refresh the tree data.
        Groups physical items by their book (edition).
        Optimized: uses single JOIN query instead of N+1 queries.
        """
        self.tree.clear()

        try:
            # Fetch all items with book info in ONE query (optimized)
            items_with_books = self._inventory_service._repo.get_all_items_with_books()

            # Group by book_id
            groups = {}
            for entry in items_with_books:
                book_id = entry['item'].book_id
                if book_id not in groups:
                    groups[book_id] = {
                        'author': entry['book_author'],
                        'title': entry['book_title'],
                        'isbn': entry['book_isbn'],
                        'items': []
                    }
                groups[book_id]['items'].append(entry['item'])

            # Build tree
            for book_id in sorted(groups.keys()):
                group = groups[book_id]
                title = f"{group['author']}. {group['title']}"

                # Create "Folder" for the book
                book_node = QTreeWidgetItem(self.tree)
                book_node.setText(0, title)
                book_node.setText(1, group['isbn'])
                book_node.setText(2, f"Копий: {len(group['items'])}")
                book_node.setExpanded(False)  # Folded by default

                # Create "Files" for each physical copy
                for item in group['items']:
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

"""
Inventory List Widget module.

Provides a hierarchical view (Tree) for viewing the list of physical book copies.
Books act as folders, and their physical copies act as files.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTreeWidget, QTreeWidgetItem, QHeaderView,
                              QLineEdit, QLabel, QComboBox)
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

        # Store all data for client-side filtering
        self._all_items_data = []

        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        self.setWindowIcon(IconManager.get_default_icon())

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Filter panel
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(8)

        # First row: Book search
        book_search_layout = QHBoxLayout()
        book_search_label = QLabel("Поиск произведений:")
        book_search_label.setFixedWidth(150)
        self.book_search_input = QLineEdit()
        self.book_search_input.setPlaceholderText("Автор, название, ISBN, ID экземпляра...")
        self.book_search_input.textChanged.connect(self._apply_filters)
        book_search_layout.addWidget(book_search_label)
        book_search_layout.addWidget(self.book_search_input)
        filter_layout.addLayout(book_search_layout)

        # Second row: Inventory number search + Status filter
        second_row_layout = QHBoxLayout()

        inv_search_label = QLabel("Инвентарный номер:")
        inv_search_label.setFixedWidth(150)
        self.inv_search_input = QLineEdit()
        self.inv_search_input.setPlaceholderText("Точный поиск по номеру...")
        self.inv_search_input.textChanged.connect(self._apply_filters)

        status_label = QLabel("Статус:")
        status_label.setFixedWidth(60)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", None)
        self.status_filter.addItem("Доступен", ItemStatus.AVAILABLE)
        self.status_filter.addItem("Выдан", ItemStatus.LOANED)
        self.status_filter.addItem("В ремонте", ItemStatus.REPAIR)
        self.status_filter.addItem("Утерян", ItemStatus.LOST)
        self.status_filter.addItem("Списан", ItemStatus.WRITTEN_OFF)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)

        second_row_layout.addWidget(inv_search_label)
        second_row_layout.addWidget(self.inv_search_input)
        second_row_layout.addWidget(status_label)
        second_row_layout.addWidget(self.status_filter)
        filter_layout.addLayout(second_row_layout)

        layout.addLayout(filter_layout)

        # Tree setup
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["ID произв.", "Наименование / №", "Статус / ISBN", "Местоположение"])

        # Set column resize modes
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID - auto-fit to content
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name - stretch
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Status/ISBN - stretch
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Location - stretch

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
        Stores all data for client-side filtering.
        """
        try:
            # Fetch all items with book info in ONE query (optimized)
            items_with_books = self._inventory_service._repo.get_all_items_with_books()

            # Store all data for filtering
            self._all_items_data = items_with_books

            # Apply filters to display
            self._apply_filters()

            self.data_refreshed.emit()

        except Exception as e:
            print(f"Ошибка при загрузке инвентаря: {e}")

    def _apply_filters(self):
        """Apply client-side filters to the tree."""
        self.tree.clear()

        # Get filter values
        book_search = self.book_search_input.text().lower().strip()
        inv_search = self.inv_search_input.text().strip()
        status_filter = self.status_filter.currentData()

        # Filter items
        filtered_items = []
        for entry in self._all_items_data:
            item = entry['item']

            # Status filter
            if status_filter is not None and item.status != status_filter:
                continue

            # Inventory number exact search
            if inv_search and item.inventory_number != inv_search:
                continue

            # Book search (author, title, ISBN, item ID)
            if book_search:
                author = (entry['book_author'] or '').lower()
                title = (entry['book_title'] or '').lower()
                isbn = (entry['book_isbn'] or '').lower()
                item_id = str(item.id)

                if not (book_search in author or
                        book_search in title or
                        book_search in isbn or
                        book_search in item_id):
                    continue

            filtered_items.append(entry)

        # Group by book_id
        groups = {}
        for entry in filtered_items:
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
            book_node.setText(0, str(book_id))
            book_node.setText(1, title)
            book_node.setText(2, group['isbn'])
            book_node.setText(3, f"Копий: {len(group['items'])}")
            book_node.setExpanded(False)  # Folded by default

            # Create "Files" for each physical copy
            for item in group['items']:
                item_node = QTreeWidgetItem(book_node)
                item_node.setText(0, str(book_id))
                item_node.setText(1, f"Инв. № {item.inventory_number}")

                # Translate status
                status_text = self.STATUS_MAP.get(item.status, item.status.value)
                item_node.setText(2, status_text)

                item_node.setText(3, item.location if item.location else "Не указано")

    def get_model(self):
        """Legacy method kept for compatibility, returns the tree widget."""
        return self.tree

# ui/windows/book_list_widget.py
"""Book list widget with repository integration."""

from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSignal
from ui.generated.ui_book_list_widget import Ui_BookListWidget

from core.services.book_service import BookService
from core.models.book import Book


class BookListWidget(QWidget, Ui_BookListWidget):
    """Виджет списка книг с интеграцией репозитория."""

    # Signal to notify parent when window should be closed
    close_requested = pyqtSignal()

    def __init__(
        self,
        parent=None,
        book_service: BookService | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)

        # Inject service
        self._book_service = book_service or BookService()

        # Store all books and filtered results
        self._all_books: list[Book] = []
        self._filtered_books: list[Book] = []

        # Remove the actions column - it's not needed
        self._connect_signals()
        self._setup_table()
        self._load_books()

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_search.clicked.connect(self._on_search)
        self.btn_refresh.clicked.connect(self._load_books)
        
        # Connect double-click to open book card
        self.table_books.doubleClicked.connect(self._on_open_book)
        
        # Connect Enter key in search field
        self.input_search.returnPressed.connect(self._on_search)

    def _setup_table(self):
        """Setup books table."""
        self.table_books.setColumnCount(5)
        self.table_books.setHorizontalHeaderLabels([
            "ID", "Автор", "Название", "Год", "ISBN"
        ])
        self.table_books.horizontalHeader().setStretchLastSection(True)
        self.table_books.setSelectionBehavior(
            self.table_books.SelectRows
        )
        self.table_books.setSelectionMode(
            self.table_books.SingleSelection
        )

    def _load_books(self):
        """Load all books from repository."""
        try:
            self._all_books = self._book_service.get_all_books()
            self._filtered_books = self._all_books.copy()
            self._display_books(self._filtered_books)
            self.label_status.setText(f"Всего: {len(self._all_books)} книг")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить книги: {e}")
            self.label_status.setText("Ошибка загрузки")

    def _display_books(self, books: list[Book]):
        """Display books in table."""
        self.table_books.setRowCount(len(books))
        
        for row, book in enumerate(books):
            self.table_books.setItem(row, 0, QTableWidgetItem(str(book.id)))
            self.table_books.setItem(row, 1, QTableWidgetItem(book.author))
            self.table_books.setItem(row, 2, QTableWidgetItem(book.title))
            self.table_books.setItem(row, 3, QTableWidgetItem(str(book.year)))
            self.table_books.setItem(row, 4, QTableWidgetItem(book.isbn))
        
        # Adjust column widths
        self.table_books.resizeColumnsToContents()

    def _on_search(self):
        """Filter books by search query."""
        try:
            query = self.input_search.text().strip().lower()
            
            if not query:
                self._filtered_books = self._all_books.copy()
            else:
                # Filter books by author, title, or ISBN
                self._filtered_books = [
                    book for book in self._all_books
                    if (query in book.author.lower() or
                        query in book.title.lower() or
                        query in book.isbn.lower() or
                        query in str(book.year))
                ]
            
            self._display_books(self._filtered_books)
            self.label_status.setText(f"Найдено: {len(self._filtered_books)} из {len(self._all_books)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Ошибка: {e}")

    def _on_open_book(self):
        """Open book card for selected book."""
        try:
            row = self.table_books.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Открыть", "Выберите книгу из списка")
                return

            # Get book ID from table
            book_id_item = self.table_books.item(row, 0)
            if not book_id_item:
                QMessageBox.warning(self, "Открыть", "Не удалось получить ID книги")
                return

            book_id = int(book_id_item.text())

            # Find parent main window and open book card
            parent_window = self.window()
            if hasattr(parent_window, '_open_book_card'):
                parent_window._open_book_card(book_id)
            else:
                # Fallback: try to find mdi_area
                if hasattr(parent_window, 'mdi_area'):
                    sub_window = QMdiSubWindow()
                    widget = BookCardWidget(
                        book_id=book_id,
                        book_service=self._book_service,
                        parent=sub_window
                    )
                    sub_window.setWidget(widget)
                    sub_window.setWindowTitle(f"{widget.get_book_title()}")
                    parent_window.mdi_area.addSubWindow(sub_window)
                    sub_window.show()

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Неверный ID книги: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть книгу: {e}")

    def get_selected_book(self) -> Book | None:
        """Get the selected book from list."""
        row = self.table_books.currentRow()
        if 0 <= row < len(self._filtered_books):
            return self._filtered_books[row]
        return None

    def refresh(self):
        """Refresh book list from repository."""
        self._load_books()

    def closeEvent(self, event):
        """Handle window close event."""
        # Accept the close event - the widget will be deleted
        # because of WA_DeleteOnClose attribute set on subwindow
        event.accept()

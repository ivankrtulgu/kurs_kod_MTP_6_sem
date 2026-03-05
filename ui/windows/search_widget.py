# ui/windows/search_widget.py
"""Search widget with repository integration - for MDI child window."""

from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import pyqtSignal
from ui.generated.ui_search_dialog import Ui_SearchDialog

from core.services.book_service import BookService
from core.models.book import Book


class SearchWidget(QWidget, Ui_SearchDialog):
    """Виджет поиска по каталогу с интеграцией репозитория (для MDI)."""

    # Signal when book is opened from search
    book_open_requested = pyqtSignal(int)

    def __init__(self, parent=None, book_service: BookService | None = None):
        super().__init__(parent)
        self.setupUi(self)

        # Inject service
        self._book_service = book_service or BookService()

        # Store search results
        self._search_results: list[Book] = []

        # Change close button to close the widget
        self.btn_close.clicked.connect(self.close)

        self._connect_signals()
        self._setup_table()

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_search.clicked.connect(self._on_search)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_open.clicked.connect(self._on_open)

        # Connect double-click to open
        self.table_results.doubleClicked.connect(self._on_open)

    def _setup_table(self):
        """Setup search results table."""
        self.table_results.setColumnCount(5)
        self.table_results.setHorizontalHeaderLabels([
            "ID", "Автор", "Название", "Год", "ISBN"
        ])
        self.table_results.horizontalHeader().setStretchLastSection(True)
        self.table_results.setSelectionBehavior(
            self.table_results.SelectRows
        )
        self.table_results.setSelectionMode(
            self.table_results.SingleSelection
        )

    def _on_search(self):
        """Execute search using repository."""
        try:
            # Build search query from all fields
            author = self.input_search_author.text().strip()
            title = self.input_search_title.text().strip()
            isbn = self.input_search_isbn.text().strip()
            udc = self.input_search_udc.text().strip()

            # Combine all search terms
            search_terms = []
            if author:
                search_terms.append(author)
            if title:
                search_terms.append(title)
            if isbn:
                search_terms.append(isbn)
            if udc:
                search_terms.append(udc)

            query = " ".join(search_terms)

            if not query:
                QMessageBox.warning(self, "Поиск", "Введите хотя бы один поисковый запрос")
                return

            # Search via service
            self._search_results = self._book_service.search_books(query)

            # Display results
            self._display_results(self._search_results)

            self.groupBox_search.setTitle(f"Параметры поиска (найдено: {len(self._search_results)})")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Ошибка: {e}")

    def _display_results(self, books: list[Book]):
        """Display search results in table."""
        self.table_results.setRowCount(len(books))

        for row, book in enumerate(books):
            self.table_results.setItem(row, 0, QTableWidgetItem(str(book.id)))
            self.table_results.setItem(row, 1, QTableWidgetItem(book.author))
            self.table_results.setItem(row, 2, QTableWidgetItem(book.title))
            self.table_results.setItem(row, 3, QTableWidgetItem(str(book.year)))
            self.table_results.setItem(row, 4, QTableWidgetItem(book.isbn))

        # Adjust column widths
        self.table_results.resizeColumnsToContents()

    def _on_clear(self):
        """Clear search fields and results."""
        self.input_search_author.clear()
        self.input_search_title.clear()
        self.input_search_isbn.clear()
        self.input_search_udc.clear()
        self.input_search_year_from.setValue(1900)
        self.input_search_year_to.setValue(2100)
        self.table_results.setRowCount(0)
        self._search_results = []
        self.groupBox_search.setTitle("Параметры поиска")

    def _on_open(self):
        """Open selected book details."""
        try:
            row = self.table_results.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Открыть", "Выберите книгу из списка")
                return

            # Get book ID from table
            book_id_item = self.table_results.item(row, 0)
            if not book_id_item:
                QMessageBox.warning(self, "Открыть", "Не удалось получить ID книги")
                return

            book_id = int(book_id_item.text())

            # Emit signal to open book card in MDI
            self.book_open_requested.emit(book_id)

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Неверный ID книги: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть книгу: {e}")

    def get_selected_book(self) -> Book | None:
        """Get the selected book from results."""
        row = self.table_results.currentRow()
        if 0 <= row < len(self._search_results):
            return self._search_results[row]
        return None

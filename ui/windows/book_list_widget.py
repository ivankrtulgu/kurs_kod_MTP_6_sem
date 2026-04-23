# ui/windows/book_list_widget.py
"""Book list widget with repository integration."""

from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox, QMdiSubWindow, QLabel, QLineEdit, QGridLayout, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
import csv
import logging
from ui.generated.ui_book_list_widget import Ui_BookListWidget

logger = logging.getLogger(__name__)

from core.services.book_service import BookService
from core.models.book import Book
from ui.windows.book_card_widget import BookCardWidget
from datetime import datetime

class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem for proper numeric sorting."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            return super().__lt__(other)

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

        # Programmatic search fields for GOST R 7.0.4-2020
        self.search_fields_layout = QGridLayout()
        self.search_inputs = {}
        
        search_fields = [
            ("Автор", "author", "text"),
            ("Название", "title", "text"),
            ("Место", "place", "text"),
            ("Издатель", "publisher", "text"),
            ("Год", "year", "range"),
            ("Страницы", "pages", "range"),
            ("ISBN", "isbn", "text"),
        ]
        
        current_row = 0
        for label_text, field_name, field_type in search_fields:
            label = QLabel(label_text)
            self.search_fields_layout.addWidget(label, current_row, 0)
            
            if field_type == "range":
                # Create 'from' and 'to' inputs
                edit_from = QLineEdit()
                edit_from.setPlaceholderText("от")
                edit_to = QLineEdit()
                edit_to.setPlaceholderText("до")
                
                self.search_fields_layout.addWidget(edit_from, current_row, 1)
                self.search_fields_layout.addWidget(edit_to, current_row, 2)
                self.search_inputs[field_name] = (edit_from, edit_to)
            else:
                # Create single input
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(f"Поиск по {label_text}...")
                self.search_fields_layout.addWidget(line_edit, current_row, 1, 1, 2)
                self.search_inputs[field_name] = line_edit
            
            current_row += 1

        # Remove old single search input from layout
        self.horizontalLayout_search.removeWidget(self.input_search)
        self.input_search.setParent(None)
        
        # Insert the new search grid layout before the table
        self.verticalLayout.insertLayout(1, self.search_fields_layout)

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
        
        # Add import button programmatically
        self.btn_import = QPushButton("Импорт из CSV")
        self.btn_import.clicked.connect(self._on_import)
        
        # Add export button programmatically
        self.btn_export = QPushButton("Экспорт в CSV")
        self.btn_export.clicked.connect(self._on_export)
        
        # Add buttons to the button layout (near btn_refresh)
        btn_layout = self.btn_refresh.parentWidget().layout()
        if btn_layout:
            btn_layout.addWidget(self.btn_import)
            btn_layout.addWidget(self.btn_export)
        
        # Connect double-click to open book card
        self.table_books.doubleClicked.connect(self._on_open_book)
        
        # Connect Enter key in search field
        self.input_search.returnPressed.connect(self._on_search)

    def _setup_table(self):
        """Setup books table."""
        ALL_BOOK_FIELDS = [
            "id", "author", "title", "place", "publisher", "year", "pages", "isbn"
        ]
        ALL_BOOK_HEADERS = [
            "ID", "Автор", "Название", "Место", "Издатель", "Год", "Страницы", "ISBN"
        ]
        
        self.table_books.setColumnCount(len(ALL_BOOK_FIELDS))
        self.table_books.setHorizontalHeaderLabels(ALL_BOOK_HEADERS)
        self._all_book_fields = ALL_BOOK_FIELDS # Store for _display_books
        self.table_books.horizontalHeader().setStretchLastSection(True)
        self.table_books.setSelectionBehavior(
            self.table_books.SelectRows
        )
        self.table_books.setSelectionMode(
            self.table_books.SingleSelection
        )
        
        # Enable sorting and set default sort by ID (Column 0, Ascending)
        self.table_books.setSortingEnabled(True)
        self.table_books.sortByColumn(0, Qt.AscendingOrder)

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
        # Temporarily disable sorting to avoid performance issues and unexpected behavior during population
        self.table_books.setSortingEnabled(False)
        self.table_books.setRowCount(len(books))
        
        for row, book in enumerate(books):
            for col, field_name in enumerate(self._all_book_fields):
                value = getattr(book, field_name)
                if isinstance(value, datetime):
                    item_text = value.strftime("%Y-%m-%d %H:%M:%S")
                    item = QTableWidgetItem(item_text)
                elif isinstance(value, (int, float)):
                    item_text = str(value)
                    item = NumericTableWidgetItem(item_text)
                else:
                    item_text = str(value)
                    item = QTableWidgetItem(item_text)
                self.table_books.setItem(row, col, item)
        
        # Adjust column widths
        self.table_books.resizeColumnsToContents()
        
        # Re-enable sorting
        self.table_books.setSortingEnabled(True)

    def _on_search(self):
        """Filter books by multiple search criteria including ranges (AND search)."""
        try:
            # Build active filters
            active_filters = {}
            for field, input_widget in self.search_inputs.items():
                if isinstance(input_widget, tuple):
                    # Range field (from, to)
                    val_from = input_widget[0].text().strip()
                    val_to = input_widget[1].text().strip()
                    if val_from or val_to:
                        active_filters[field] = {"from": val_from, "to": val_to, "type": "range"}
                else:
                    # Text field
                    val = input_widget.text().strip().lower()
                    if val:
                        active_filters[field] = {"val": val, "type": "text"}
            
            if not active_filters:
                self._filtered_books = self._all_books.copy()
            else:
                self._filtered_books = []
                for book in self._all_books:
                    match = True
                    for field, filter_data in active_filters.items():
                        val = getattr(book, field)
                        
                        if filter_data["type"] == "text":
                            if filter_data["val"] not in str(val).lower():
                                match = False
                                break
                        elif filter_data["type"] == "range":
                            try:
                                book_val = int(val)
                                f_from = filter_data["from"]
                                f_to = filter_data["to"]
                                
                                if f_from and not (int(f_from) <= book_val):
                                    match = False
                                    break
                                if f_to and not (book_val <= int(f_to)):
                                    match = False
                                    break
                            except (ValueError, TypeError):
                                # If book value is not an int or input is not an int, it's not a match
                                match = False
                                break
                    if match:
                        self._filtered_books.append(book)
            
            self._display_books(self._filtered_books)
            self.label_status.setText(f"Найдено: {len(self._filtered_books)} из {len(self._all_books)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Ошибка: {e}")

    def _on_import(self):
        """Import books from a CSV file with optional ID handling."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт книг", "", "CSV Files (*.csv)"
        )
        
        if not path:
            return

        # Ask user whether to use IDs from the file
        use_ids = QMessageBox.question(
            self, "Импорт ID", 
            "Использовать идентификаторы (ID) из файла?\nЕсли 'Нет', будут назначены новые ID.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes
            
        try:
            imported_count = 0
            error_count = 0
            
            with open(path, mode='r', encoding='utf-8-sig') as f:
                # Try different delimiters
                success = False
                for delimiter in [';', '\t', ',']:
                    f.seek(0)
                    first_line = f.readline()
                    if delimiter not in first_line and delimiter != '\t':
                        continue
                    
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    headers = reader.fieldnames if reader.fieldnames else []
                    if not any(h in headers for h in ["Автор", "author", "Название", "title"]):
                        continue
                    
                    for row_idx, row in enumerate(reader, start=2):
                        try:
                            # Helper for mapped headers
                            def get_val(field):
                                map_headers = {
                                    "author": ["Автор", "author"],
                                    "title": ["Название", "title"],
                                    "place": ["Место", "place"],
                                    "publisher": ["Издатель", "publisher"],
                                    "year": ["Год", "year"],
                                    "pages": ["Страницы", "pages"],
                                    "isbn": ["ISBN", "isbn"],
                                    "subtitle": ["Подзаголовок", "subtitle"],
                                    "responsibility": ["Ответственность", "responsibility"],
                                    "edition": ["Издание", "edition"],
                                    "copyright": ["Авторские права", "copyright"],
                                    "udc": ["УДК", "udc"],
                                    "bbk": ["ББК", "bbk"],
                                    "author_mark": ["Авторский знак", "author_mark"],
                                    "reviewers": ["Рецензенты", "reviewers"],
                                    "annotation": ["Аннотация", "annotation"],
                                    "abstract": ["Аннотация (англ.)", "abstract"],
                                    "doi": ["DOI", "doi"],
                                    "content_type": ["Тип контента", "content_type"],
                                    "access_method": ["Метод доступа", "access_method"],
                                    "id": ["id", "ID"]
                                }
                                for h in map_headers.get(field, [field]):
                                    if h in row: return row[h]
                                return ""

                            # ID handling
                            book_id = 0
                            if use_ids:
                                try:
                                    book_id = int(get_val("id")) if get_val("id") else 0
                                except ValueError:
                                    book_id = 0

                            book = Book(
                                id=book_id,
                                author=get_val("author"),
                                title=get_val("title"),
                                place=get_val("place"),
                                publisher=get_val("publisher"),
                                year=int(get_val("year")) if get_val("year") else 0,
                                pages=int(get_val("pages")) if get_val("pages") else 0,
                                isbn=get_val("isbn"),
                                subtitle=get_val("subtitle"),
                                responsibility=get_val("responsibility"),
                                edition=get_val("edition"),
                                copyright=get_val("copyright"),
                                udc=get_val("udc"),
                                bbk=get_val("bbk"),
                                author_mark=get_val("author_mark"),
                                reviewers=get_val("reviewers"),
                                annotation=get_val("annotation"),
                                abstract=get_val("abstract"),
                                doi=get_val("doi"),
                                content_type=get_val("content_type") or "Текст",
                                access_method=get_val("access_method") or "непосредственный"
                            )
                            
                            self._book_service.add_book(book)
                            imported_count += 1
                        except Exception as e:
                            logger.error(f"Error importing row {row_idx}: {e}")
                            error_count += 1
                    
                    success = True
                    break
            
            if not success:
                QMessageBox.warning(self, "Ошибка импорта", "Не удалось распознать формат файла.")
                return

            QMessageBox.information(
                self, "Импорт завершен", 
                f"Успешно импортировано: {imported_count} книг.\nОшибок: {error_count}."
            )
            self._load_books()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", f"Критическая ошибка при чтении файла: {e}")

    def _on_export(self):
        """Export books to CSV file with optional ID handling."""
        # Ask user whether to include IDs
        include_ids = QMessageBox.question(
            self, "Экспорт ID", 
            "Включить идентификаторы (ID) в экспортный файл?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить список книг", 
            "books_export.csv", "CSV Files (*.csv)"
        )
        
        if not path:
            return
            
        try:
            # Define fields to export
            export_fields = ["id", "author", "title", "place", "publisher", "year", "pages", "isbn"]
            export_headers = ["ID", "Автор", "Название", "Место", "Издатель", "Год", "Страницы", "ISBN"]
            
            if not include_ids:
                export_fields = export_fields[1:]
                export_headers = export_headers[1:]
                
            with open(path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(export_headers)
                
                for book in self._all_books:
                    row = [getattr(book, field) for field in export_fields]
                    writer.writerow(row)
            
            QMessageBox.information(self, "Экспорт", f"Данные успешно экспортированы в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить файл: {e}")

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

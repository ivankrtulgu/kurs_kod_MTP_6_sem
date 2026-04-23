# ui/windows/search_widget.py
"""Search widget with repository integration - for MDI child window."""

from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QGridLayout, QScrollArea, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
import csv
from ui.generated.ui_search_dialog import Ui_SearchDialog

from core.services.book_service import BookService
from core.models.book import Book
from datetime import datetime


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom QTableWidgetItem for proper numeric sorting."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            return super().__lt__(other)

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
        
        # Programmatic Search Fields Configuration
        self.search_inputs = {}
        self._setup_advanced_search_ui()
        
        # Change close button to close the widget
        self.btn_close.clicked.connect(self.close)
        
        self._connect_signals()
        self._setup_table()

    def _setup_advanced_search_ui(self):
        """Build a comprehensive search form with grouped fields."""
        # Create a scroll area for the search fields to prevent window overflow
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)
        
        # Define fields by category
        groups = {
            "Обязательные поля": [
                ("Автор", "author", "text"),
                ("Название", "title", "text"),
                ("Место", "place", "text"),
                ("Издатель", "publisher", "text"),
                ("Год", "year", "range"),
                ("Страницы", "pages", "range"),
                ("ISBN", "isbn", "text"),
            ],
            "Дополнительные поля": [
                ("Подзаголовок", "subtitle", "text"),
                ("Ответственность", "responsibility", "text"),
                ("Издание", "edition", "text"),
                ("Авторские права", "copyright", "text"),
                ("УДК", "udc", "text"),
                ("ББК", "bbk", "text"),
                ("Авторский знак", "author_mark", "text"),
            ],
            "Прочее": [
                ("Рецензенты", "reviewers", "text"),
                ("Аннотация", "annotation", "text"),
                ("Аннотация (англ.)", "abstract", "text"),
                ("DOI", "doi", "text"),
                ("Тип контента", "content_type", "text"),
                ("Метод доступа", "access_method", "text"),
            ]
        }
        
        for group_name, fields in groups.items():
            group_box = QVBoxLayout()
            header = QLabel(f"<b>{group_name}</b>")
            group_box.addWidget(header)
            
            grid = QGridLayout()
            for i, (label_text, field_name, field_type) in enumerate(fields):
                label = QLabel(label_text)
                if field_type == "range":
                    edit_from = QLineEdit()
                    edit_from.setPlaceholderText("от")
                    edit_to = QLineEdit()
                    edit_to.setPlaceholderText("до")
                    grid.addWidget(label, i, 0)
                    grid.addWidget(edit_from, i, 1)
                    grid.addWidget(edit_to, i, 2)
                    self.search_inputs[field_name] = (edit_from, edit_to)
                else:
                    line_edit = QLineEdit()
                    line_edit.setPlaceholderText(f"Поиск по {label_text}...")
                    grid.addWidget(label, i, 0)
                    grid.addWidget(line_edit, i, 1, 1, 2)
                    self.search_inputs[field_name] = line_edit
            
            group_box.addLayout(grid)
            main_layout.addLayout(group_box)
        
        scroll.setWidget(scroll_content)
        
        # Replace the existing groupBox_search layout with our scroll area
        # Since groupBox_search is a QGroupBox, we can set its layout
        if self.groupBox_search.layout():
            # This is a bit hacky but necessary for generated UI
            import shutil
            # We can't easily remove a layout, so we just add the scroll area
            # and hide the generated inputs
            self.input_search_author.hide()
            self.input_search_title.hide()
            self.input_search_isbn.hide()
            self.input_search_udc.hide()
            
        # Instead of trying to replace layout in a generated QGroupBox, 
        # let's just place the scroll area over it or replace the groupbox in the main layout
        # The generated UI layout is likely a vertical layout
        parent_layout = self.layout()
        if parent_layout:
            # Find index of groupBox_search and insert scroll area
            idx = parent_layout.indexOf(self.groupBox_search)
            if idx != -1:
                parent_layout.insertWidget(idx, scroll)
                self.groupBox_search.hide()

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_search.clicked.connect(self._on_search)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_open.clicked.connect(self._on_open)
        
        # Add export buttons programmatically if not present
        self.btn_export_csv = QPushButton("Экспорт в CSV")
        self.btn_export_csv.clicked.connect(self._on_export)
        
        self.btn_export_txt = QPushButton("Экспорт в TXT")
        self.btn_export_txt.clicked.connect(self._on_export_txt)
        
        # Add buttons to the button area (near btn_search)
        btn_layout = self.btn_search.parentWidget().layout()
        if btn_layout:
            btn_layout.addWidget(self.btn_export_csv)
            btn_layout.addWidget(self.btn_export_txt)
        
        # Connect double-click to open
        self.table_results.doubleClicked.connect(self._on_open)

    def _setup_table(self):
        """Setup search results table with all fields and sorting."""
        ALL_BOOK_FIELDS = [
            "id", "author", "title", "subtitle", "responsibility", "edition",
            "place", "publisher", "year", "pages", "isbn", "copyright",
            "udc", "bbk", "author_mark", "reviewers", "annotation",
            "abstract", "doi", "content_type", "access_method",
            "created_at", "qr_code_path", "cover_image_path"
        ]
        ALL_BOOK_HEADERS = [
            "ID", "Автор", "Название", "Подзаголовок", "Ответственность", "Издание",
            "Место", "Издатель", "Год", "Страницы", "ISBN", "Авторские права",
            "УДК", "ББК", "Авторский знак", "Рецензенты", "Аннотация",
            "Аннотация (англ.)", "DOI", "Тип контента", "Метод доступа",
            "Создано", "Путь к QR", "Путь к обложке"
        ]
        
        self.table_results.setColumnCount(len(ALL_BOOK_FIELDS))
        self.table_results.setHorizontalHeaderLabels(ALL_BOOK_HEADERS)
        self._all_book_fields = ALL_BOOK_FIELDS
        self.table_results.horizontalHeader().setStretchLastSection(True)
        self.table_results.setSelectionBehavior(
            self.table_results.SelectRows
        )
        self.table_results.setSelectionMode(
            self.table_results.SingleSelection
        )
        
        # Enable sorting
        self.table_results.setSortingEnabled(True)

    def _on_search(self):
        """Execute advanced search with AND filtering and ranges."""
        try:
            # Build active filters
            active_filters = {}
            for field, input_widget in self.search_inputs.items():
                if isinstance(input_widget, tuple):
                    # Range field
                    val_from = input_widget[0].text().strip()
                    val_to = input_widget[1].text().strip()
                    if val_from or val_to:
                        active_filters[field] = {"from": val_from, "to": val_to, "type": "range"}
                else:
                    # Text field
                    val = input_widget.text().strip().lower()
                    if val:
                        active_filters[field] = {"val": val, "type": "text"}
            
            # Fetch all books and filter on client side for flexibility
            all_books = self._book_service.get_all_books()
            
            if not active_filters:
                self._search_results = all_books
            else:
                self._search_results = []
                for book in all_books:
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
                                match = False
                                break
                    if match:
                        self._search_results.append(book)
            
            self._display_results(self._search_results)
            
            # Update the search info (the group box is hidden, but we can update status if we had one)
            # We'll just use a simple message box or update a label if we add one.
            # For now, we'll just display the results.
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка поиска", f"Ошибка: {e}")

    def _display_results(self, books: list[Book]):
        """Display all book fields in results table."""
        self.table_results.setSortingEnabled(False)
        self.table_results.setRowCount(len(books))
        
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
                self.table_results.setItem(row, col, item)
        
        self.table_results.resizeColumnsToContents()
        self.table_results.setSortingEnabled(True)

    def _on_clear(self):
        """Clear all search fields and results."""
        for input_widget in self.search_inputs.values():
            if isinstance(input_widget, tuple):
                input_widget[0].clear()
                input_widget[1].clear()
            else:
                input_widget.clear()
        
        self.table_results.setRowCount(0)
        self._search_results = []

    def _format_bibliographic_record(self, book: Book) -> str:
        """Format a book object into a bibliographic record string (approximating GOST)."""
        # Author. Title : subtitle / responsibility. — Edition. — Place : Publisher, Year. — Pages. — ISBN.
        
        parts = []
        
        # 1. Author
        parts.append(f"{book.author}.")
        
        # 2. Title and Subtitle
        title_part = book.title
        if book.subtitle:
            title_part += f" : {book.subtitle}"
        parts.append(title_part)
        
        # 3. Responsibility
        if book.responsibility:
            parts.append(f"/ {book.responsibility}.")
        
        # 4. Edition
        if book.edition:
            parts.append(f"— {book.edition}.")
        
        # 5. Place, Publisher, Year
        pub_info = []
        if book.place: pub_info.append(book.place)
        if book.publisher: pub_info.append(book.publisher)
        
        if pub_info:
            pub_str = " : ".join(pub_info)
            parts.append(f"— {pub_str}, {book.year}.")
        else:
            parts.append(f"— {book.year}.")
            
        # 6. Pages
        if book.pages:
            parts.append(f"— {book.pages} с.")
            
        # 7. ISBN
        if book.isbn:
            parts.append(f"— ISBN {book.isbn}.")
            
        # Join with spaces and fix double spaces
        record = " ".join(parts)
        return record.replace("  ", " ").strip()

    def _get_books_in_table_order(self) -> list[Book]:
        """Get books in the order they are currently displayed in the table."""
        books_in_order = []
        # Create a lookup dictionary for fast access
        book_lookup = {book.id: book for book in self._search_results}
        
        for row in range(self.table_results.rowCount()):
            book_id_item = self.table_results.item(row, 0)
            if book_id_item:
                try:
                    book_id = int(book_id_item.text())
                    if book_id in book_lookup:
                        books_in_order.append(book_lookup[book_id])
                except ValueError:
                    continue
        return books_in_order

    def _on_export(self):
        """Export search results to CSV file in table order."""
        books_to_export = self._get_books_in_table_order()
        if not books_to_export:
            QMessageBox.warning(self, "Экспорт", "Нет результатов для экспорта")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты поиска", 
            "search_results.csv", "CSV Files (*.csv)"
        )
        
        if not path:
            return
        
        try:
            with open(path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(self._all_book_fields)
                for book in books_to_export:
                    row = [getattr(book, field) for field in self._all_book_fields]
                    writer.writerow(row)
            QMessageBox.information(self, "Экспорт", f"Данные успешно экспортированы в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить файл: {e}")

    def _on_export_txt(self):
        """Export search results to bibliographic TXT file in table order."""
        books_to_export = self._get_books_in_table_order()
        if not books_to_export:
            QMessageBox.warning(self, "Экспорт", "Нет результатов для экспорта")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить библиографические записи", 
            "bibliographic_records.txt", "Text Files (*.txt)"
        )
        
        if not path:
            return
        
        try:
            with open(path, mode='w', encoding='utf-8') as f:
                for book in books_to_export:
                    record = self._format_bibliographic_record(book)
                    f.write(record + "\n")
            
            QMessageBox.information(self, "Экспорт", f"Записи успешно экспортированы в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось сохранить файл: {e}")

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

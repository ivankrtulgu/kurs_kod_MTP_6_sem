# ui/windows/search_dialog.py
"""Search dialog with repository integration."""

from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QGridLayout, QScrollArea, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QWidget, QGroupBox
from PyQt5.QtCore import Qt
import csv
from ui.generated.ui_search_dialog import Ui_SearchDialog
from ui.style_manager import StyleManager

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

class SearchDialog(QDialog, Ui_SearchDialog):
    """Диалог поиска по каталогу с интеграцией репозитория."""

    def __init__(self, parent=None, book_service: BookService | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet(StyleManager.get_stylesheet())

        # Standardize main layout
        if self.verticalLayout:
            self.verticalLayout.setSpacing(10)
            self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        
        # Inject service
        self._book_service = book_service or BookService()
        
        # Store search results
        self._search_results: list[Book] = []
        
        # Programmatic Search Fields Configuration
        self.search_inputs = {}
        self._setup_advanced_search_ui()
        
        self._connect_signals()
        self._setup_table()

    def _setup_advanced_search_ui(self):
        """Build a comprehensive search form with grouped fields."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
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
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout(group_box)
            group_layout.setSpacing(10)
            
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
            
            group_layout.addLayout(grid)
            main_layout.addWidget(group_box)
        
        scroll.setWidget(scroll_content)
        
        # Replace the existing groupBox_search layout
        if self.groupBox_search.layout():
            self.input_search_author.hide()
            self.input_search_title.hide()
            self.input_search_isbn.hide()
            self.input_search_udc.hide()
            
        parent_layout = self.layout()
        if parent_layout:
            idx = parent_layout.indexOf(self.groupBox_search)
            if idx != -1:
                parent_layout.insertWidget(idx, scroll)
                self.groupBox_search.hide()

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_search.clicked.connect(self._on_search)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_close.clicked.connect(self.reject)
        self.btn_open.clicked.connect(self._on_open)
        
        # Add buttons programmatically
        self.btn_import = QPushButton("Импорт из CSV")
        self.btn_import.clicked.connect(self._on_import)
        
        self.btn_export_csv = QPushButton("Экспорт в CSV")
        self.btn_export_csv.clicked.connect(self._on_export)
        
        self.btn_export_txt = QPushButton("Экспорт в TXT")
        self.btn_export_txt.clicked.connect(self._on_export_txt)
        
        btn_layout = self.btn_search.parentWidget().layout()
        if btn_layout:
            btn_layout.addWidget(self.btn_import)
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
                    val_from = input_widget[0].text().strip()
                    val_to = input_widget[1].text().strip()
                    if val_from or val_to:
                        active_filters[field] = {"from": val_from, "to": val_to, "type": "range"}
                else:
                    val = input_widget.text().strip().lower()
                    if val:
                        active_filters[field] = {"val": val, "type": "text"}
            
            # Fetch all books and filter on client side
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
                            print(f"Error importing row {row_idx}: {e}")
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
            
            # Refresh search results to show newly imported books
            self._on_search()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", f"Критическая ошибка при чтении файла: {e}")

    def _format_bibliographic_record(self, book: Book) -> str:
        """Format a book object into a bibliographic record string (approximating GOST)."""
        parts = []
        parts.append(f"{book.author}.")
        title_part = book.title
        if book.subtitle:
            title_part += f" : {book.subtitle}"
        parts.append(title_part)
        if book.responsibility:
            parts.append(f"/ {book.responsibility}.")
        if book.edition:
            parts.append(f"— {book.edition}.")
        pub_info = []
        if book.place: pub_info.append(book.place)
        if book.publisher: pub_info.append(book.publisher)
        if pub_info:
            pub_str = " : ".join(pub_info)
            parts.append(f"— {pub_str}, {book.year}.")
        else:
            parts.append(f"— {book.year}.")
        if book.pages:
            parts.append(f"— {book.pages} с.")
        if book.isbn:
            parts.append(f"— ISBN {book.isbn}.")
        record = " ".join(parts)
        return record.replace("  ", " ").strip()

    def _get_books_in_table_order(self) -> list[Book]:
        """Get books in the order they are currently displayed in the table."""
        books_in_order = []
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
        """Export search results to CSV file with optional ID handling."""
        # Ask user whether to include IDs
        include_ids = QMessageBox.question(
            self, "Экспорт ID", 
            "Включить идентификаторы (ID) в экспортный файл?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes
        
        if not self._search_results:
            QMessageBox.warning(self, "Экспорт", "Нет результатов для экспорта")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результаты поиска", 
            "search_results.csv", "CSV Files (*.csv)"
        )
        
        if not path:
            return
        
        try:
            # Determine fields to export
            export_fields = self._all_book_fields.copy()
            if not include_ids:
                if 'id' in export_fields:
                    export_fields.remove('id')
            
            headers_map = {
                "id": "ID", "author": "Автор", "title": "Название", "subtitle": "Подзаголовок", 
                "responsibility": "Ответственность", "edition": "Издание", "place": "Место", 
                "publisher": "Издатель", "year": "Год", "pages": "Страницы", "isbn": "ISBN", 
                "copyright": "Авторские права", "udc": "УДК", "bbk": "ББК", "author_mark": "Авторский знак", 
                "reviewers": "Рецензенты", "annotation": "Аннотация", "abstract": "Аннотация (англ.)", 
                "doi": "DOI", "content_type": "Тип контента", "access_method": "Метод доступа", 
                "created_at": "Создано", "qr_code_path": "Путь к QR", "cover_image_path": "Путь к обложке"
            }
            export_headers = [headers_map[f] for f in export_fields]
            
            with open(path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(export_headers)
                
                books_to_export = self._get_books_in_table_order()
                for book in books_to_export:
                    row = [getattr(book, field) for field in export_fields]
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
            
            # Get book from service
            book = self._book_service.get_book(book_id)
            if not book:
                QMessageBox.warning(self, "Открыть", f"Книга с ID {book_id} не найдена")
                return
            
            # Open book card dialog
            from ui.windows.book_card_widget import BookCardWidget
            from PyQt5.QtWidgets import QDialog
            
            card_dialog = QDialog(self)
            card_widget = BookCardWidget(
                book_id=book_id,
                book_service=self._book_service,
                parent=card_dialog
            )
            
            layout = card_dialog.layout() if card_dialog.layout() else None
            if layout:
                layout.addWidget(card_widget)
            else:
                from PyQt5.QtWidgets import QVBoxLayout
                card_dialog.setLayout(QVBoxLayout())
                card_dialog.layout().addWidget(card_widget)
            
            card_dialog.setWindowTitle(f"{book.title}")
            card_dialog.resize(800, 600)
            card_dialog.exec_()
            
            self.accept()
            
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

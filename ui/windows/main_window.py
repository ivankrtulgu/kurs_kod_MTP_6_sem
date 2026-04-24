# ui/windows/main_window.py
"""Main window module with business logic integration - Professional MDI implementation."""

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QMdiSubWindow, QMdiArea
from PyQt5.QtCore import Qt
from typing import Any
from ui.generated.ui_main_window import Ui_MainWindow

from core.services.book_service import BookService
from ui.windows.book_list_widget import BookListWidget
from ui.windows.book_card_widget import BookCardWidget
from ui.windows.add_book_widget import AddBookWidget
from ui.windows.search_widget import SearchWidget
from ui.windows.about_widget import AboutWidget
from ui.windows.ocr_window import OcrWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """Главное MDI-окно приложения с интеграцией бизнес-логики."""

    def __init__(self, parent=None, book_service: BookService | None = None, inventory_service: Any | None = None):
        super().__init__(parent)
        self.setupUi(self)

        # Inject services (dependency injection)
        self._book_service = book_service or BookService()
        self._inventory_service = inventory_service # Injected from main.py
        
        # Configure MDI area for proper SDI/MDI hybrid behavior
        self.mdi_area.setViewMode(QMdiArea.SubWindowView)
        self.mdi_area.setDocumentMode(False)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        
        # Enable cascade and tile options
        self.mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self._setup_inventory_toolbar()
        self._connect_signals()
        self._update_status_bar()


    def _connect_signals(self):
        """Подключение всех кнопок и меню."""
        # Каталог
        self.action_add_book.triggered.connect(self._open_add_book)
        self.action_refresh.triggered.connect(self._open_book_list)
        self.action_search.triggered.connect(self._open_search)
        self.action_export.triggered.connect(self._on_export)

        # Инвентарь (Inventory)
        self.act_add_items.triggered.connect(self._on_add_items_clicked)
        self.act_show_inv.triggered.connect(self._on_show_inventory)
        self.act_issue.triggered.connect(self._on_issue_clicked)
        self.act_return.triggered.connect(self._on_return_clicked)
        
        # Сервис
        self.action_ocr.triggered.connect(self._on_ocr)
        self.action_generate_qr.triggered.connect(self._on_generate_qr)

        # Файл
        self.action_exit.triggered.connect(self.close)

        # Справка
        self.action_about.triggered.connect(self._open_about)

    def _update_status_bar(self):
        """Update status bar with book count."""
        try:
            count = self._book_service.count_books()
            self.statusbar.showMessage(f"Всего книг: {count}", 5000)
        except Exception as e:
            self.statusbar.showMessage(f"Ошибка: {e}", 5000)

    def _setup_inventory_toolbar(self):
        """Add inventory management actions to the toolbar."""
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QAction, QToolBar

        # If you have a toolbar already defined in .ui, we add to it.
        # Otherwise, we create a new one.
        if hasattr(self, 'mainToolBar'):
            toolbar = self.mainToolBar
        else:
            toolbar = QToolBar("Inventory Toolbar")
            self.addToolBar(toolbar)

        toolbar.addSeparator()

        # Action: Add Items
        self.act_add_items = QAction(QIcon.fromTheme("document-new"), "Добавить экземпляры", self)
        self.act_add_items.setToolTip("Добавить новые физические копии произведения")
        toolbar.addAction(self.act_add_items)

        # Action: Show Inventory List
        self.act_show_inv = QAction(QIcon.fromTheme("view-list"), "Учет экземпляров", self)
        self.act_show_inv.setToolTip("Открыть список физических экземпляров")
        toolbar.addAction(self.act_show_inv)

        # Action: Issue Book
        self.act_issue = QAction(QIcon.fromTheme("document-send"), "Выдать книгу", self)
        self.act_issue.setToolTip("Оформить выдачу экземпляра читателю")
        toolbar.addAction(self.act_issue)

        # Action: Return Book
        self.act_return = QAction(QIcon.fromTheme("document-open"), "Принять книгу", self)
        self.act_return.setToolTip("Оформить возврат экземпляра")
        toolbar.addAction(self.act_return)

    def _open_mdi_subwindow(self, widget_class, *args, **kwargs):
        """
        Universal method to open a widget as an MDI subwindow.
        Prevents duplicate windows of the same class.
        """
        
        # Check if already open
        for sub_window in self.mdi_area.subWindowList():
            widget = sub_window.widget()
            if isinstance(widget, widget_class):
                self.mdi_area.setActiveSubWindow(sub_window)
                if sub_window.isMinimized():
                    sub_window.showNormal()
                return widget

        # Create new
        new_widget = widget_class(*args, **kwargs)
        title = widget_class.__name__.replace("Widget", "")
        sub_window = self._create_sub_window(new_widget, title)
        
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        return new_widget

    def _on_show_inventory(self):
        """Open the inventory list window."""
        from ui.windows.inventory_list_widget import InventoryListWidget
        self._open_mdi_subwindow(InventoryListWidget, self._inventory_service)

    def _on_issue_clicked(self):
        """Open the issue book dialog."""
        from ui.dialogs.issue_dialog import IssueBookDialog
        dialog = IssueBookDialog(self._inventory_service, self)
        if dialog.exec_():
            self._refresh_inventory_windows()

    def _on_return_clicked(self):
        """Open the return book dialog."""
        from ui.dialogs.return_dialog import ReturnBookDialog
        dialog = ReturnBookDialog(self._inventory_service, self)
        if dialog.exec_():
            self._refresh_inventory_windows()

    def _on_add_items_clicked(self):
        """Open the add items window as MDI child."""
        from ui.windows.add_items_widget import AddItemsWidget
        
        widget = self._open_mdi_subwindow(AddItemsWidget, self._book_service, self._inventory_service)
        if widget:
            widget.items_added.connect(self._refresh_inventory_windows)

    def _open_book_list_for_selection(self, callback_dialog):
        """
        Open BookListWidget in selection mode.
        When a book is double-clicked, it notifies the callback_dialog.
        """
        from ui.windows.book_list_widget import BookListWidget
        
        # Use _open_mdi_subwindow to get the widget
        # Pass book_service as a keyword argument to avoid it being treated as the 'parent'
        list_widget = self._open_mdi_subwindow(BookListWidget, book_service=self._book_service)
        
        if list_widget:
            # Enable selection mode
            list_widget.selection_mode = True
            
            # Connect selection signal to the dialog
            def handle_selection(book_id):
                # Find the book object to get its text
                book = self._book_service.get_book_by_id(book_id)
                if book:
                    book_text = f"{book.author}. {book.title}"
                    callback_dialog.set_selected_book(book_id, book_text)
                
                # Return to normal mode
                list_widget.selection_mode = False
                
                # Close the selection window automatically after choice
                sub_window = self.mdi_area.activeSubWindow()
                if sub_window and sub_window.widget() == list_widget:
                    sub_window.close()
            
            # Disconnect any previous selection handlers to avoid duplicates
            try:
                list_widget.book_selected.disconnect()
            except TypeError:
                pass
                
            list_widget.book_selected.connect(handle_selection)


    def _refresh_inventory_windows(self):
        """Refresh all open inventory list windows."""
        from ui.windows.inventory_list_widget import InventoryListWidget
        for sub_window in self.mdi_area.subWindowList():
            widget = sub_window.widget()
            if isinstance(widget, InventoryListWidget):
                widget.refresh_list()

    # ========== КАТАЛОГ ==========

    def _create_sub_window(self, widget, title: str, width: int = 800, height: int = 600) -> QMdiSubWindow:
        """
        Create a properly configured MDI sub window.
        
        Args:
            widget: The widget to place in the sub window
            title: Window title
            width: Initial width
            height: Initial height
            
        Returns:
            Configured QMdiSubWindow
        """
        sub_window = QMdiSubWindow()
        sub_window.setWidget(widget)
        sub_window.setWindowTitle(title)
        sub_window.setAttribute(Qt.WA_DeleteOnClose)
        
        # Set window flags for proper MDI behavior
        sub_window.setWindowFlags(
            Qt.SubWindow |
            Qt.WindowTitleHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinMaxButtonsHint |
            Qt.WindowCloseButtonHint
        )
        
        # Set initial size
        sub_window.resize(width, height)
        
        # Center the window in MDI area
        mdi_size = self.mdi_area.size()
        x = (mdi_size.width() - width) // 2
        y = (mdi_size.height() - height) // 2
        sub_window.move(max(0, x), max(0, y))
        
        return sub_window

    def _open_book_list(self):
        """Открыть список книг как MDI дочернее окно."""
        try:
            # Use the unified singleton method
            self._open_mdi_subwindow(BookListWidget, book_service=self._book_service)
            self.statusbar.showMessage("Список книг открыт", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть список книг: {e}")


    def _open_add_book(self):
        """Открыть окно добавления книги как MDI дочернее окно."""
        try:
            # Use the unified singleton method
            self._open_mdi_subwindow(AddBookWidget, book_service=self._book_service)
            self.statusbar.showMessage("Добавление книги открыто", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить книгу: {e}")


    def _open_search(self):
        """Открыть поиск как MDI дочернее окно."""
        try:
            # Use the unified singleton method
            widget = self._open_mdi_subwindow(SearchWidget, book_service=self._book_service)
            if widget:
                # Connect book open signal
                widget.book_open_requested.connect(self._on_search_book_open)
            
            self.statusbar.showMessage("Поиск открыт", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {e}")


    def _on_search_book_open(self, book_id: int):
        """Handle book open request from search widget."""
        self._open_book_card(book_id)

    def _open_book_card(self, book_id: int):
        """Open book card as MDI child window."""
        try:
            # Since book cards are unique to each book ID, 
            # we need to pass the ID to the widget and potentially 
            # modify the singleton check to include the book_id.
            # For now, we'll just open it as a new window.
            widget = BookCardWidget(
                book_id=book_id,
                book_service=self._book_service
            )
            title = widget.get_book_title()
            
            sub_window = self._create_sub_window(widget, title, 850, 650)
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            self.statusbar.showMessage(f"Открыта карточка книги: {title}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть книгу: {e}")

    def _on_export(self):
        """Экспорт каталога."""
        try:
            books = self._book_service.get_all_books()
            if not books:
                QMessageBox.information(self, "Экспорт", "Каталог пуст")
                return

            # Simple export to text format
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт каталога", "", "Text files (*.txt);;All files (*)"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for book in books:
                        f.write(book.format_bibliographic_record() + "\n\n")
                QMessageBox.information(self, "Экспорт", f"Каталог экспортирован: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {e}")

    # ========== СЕРВИС ==========

    def _on_ocr(self):
        """OCR распознавание - открывается как дочернее MDI окно."""
        try:
            # Check if already open
            existing = self._find_child_window("OCR")
            if existing:
                self.mdi_area.setActiveSubWindow(existing)
                if existing.isMinimized():
                    existing.showNormal()
                return

            widget = OcrWindow()
            sub_window = self._create_sub_window(widget, "OCR — Распознавание текста", 1400, 900)
            
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # Connect OCR data signal
            widget.ocr_data_ready.connect(self._on_ocr_data_ready)
            
            self.statusbar.showMessage("OCR распознавание открыто", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка OCR: {e}")

    def _on_ocr_data_ready(self, ocr_data: dict):
        """Обработка распознанных данных из OCR - открывает окно добавления книги."""
        try:
            # Check if add book window is already open
            existing = self._find_child_window("Добавить книгу")
            if existing:
                # Fill existing window with OCR data
                widget = existing.widget()
                if isinstance(widget, AddBookWidget):
                    widget._fill_from_ocr_data(ocr_data)
                self.mdi_area.setActiveSubWindow(existing)
                if existing.isMinimized():
                    existing.showNormal()
            else:
                # Open new add book window with OCR data
                widget = AddBookWidget(
                    book_service=self._book_service,
                    ocr_data=ocr_data
                )
                sub_window = self._create_sub_window(widget, "Добавить книгу (OCR)", 800, 750)
                self.mdi_area.addSubWindow(sub_window)
                sub_window.show()
            
            self.statusbar.showMessage("Данные OCR загружены в форму", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления книги: {e}")

    def _on_generate_qr(self):
        """Генерация QR-кодов."""
        try:
            # Get selected book from active subwindow
            active_subwindow = self.mdi_area.activeSubWindow()
            if active_subwindow:
                widget = active_subwindow.widget()
                if isinstance(widget, BookCardWidget):
                    # Generate QR for this book
                    QMessageBox.information(self, "QR", "Генерация QR-кода в разработке")
                elif isinstance(widget, BookListWidget):
                    QMessageBox.information(self, "QR", "Выберите книгу для генерации QR")
                else:
                    QMessageBox.information(self, "QR", "Откройте книгу для генерации QR")
            else:
                QMessageBox.information(self, "QR", "Откройте список книг или карточку книги")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации QR: {e}")

    # ========== СПРАВКА ==========

    def _open_about(self):
        """О программе - как MDI дочернее окно."""
        try:
            # Check if already open
            existing = self._find_child_window("О программе")
            if existing:
                self.mdi_area.setActiveSubWindow(existing)
                if existing.isMinimized():
                    existing.showNormal()
                return

            widget = AboutWidget()
            sub_window = self._create_sub_window(widget, "О программе", 550, 450)
            
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            self.statusbar.showMessage("О программе открыто", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия окна 'О программе': {e}")

    def _find_child_window(self, title_contains: str) -> QMdiSubWindow | None:
        """Find existing child window by title."""
        for sub_window in self.mdi_area.subWindowList():
            if title_contains in sub_window.windowTitle():
                return sub_window
        return None

    def closeEvent(self, event):
        """Handle main window close - close all MDI subwindows."""
        # Close all subwindows gracefully
        for sub_window in self.mdi_area.subWindowList():
            sub_window.close()
        event.accept()

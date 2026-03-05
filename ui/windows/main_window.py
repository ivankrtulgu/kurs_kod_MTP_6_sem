# ui/windows/main_window.py
"""Main window module with business logic integration."""

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QMdiSubWindow
from ui.generated.ui_main_window import Ui_MainWindow

from core.services.book_service import BookService
from ui.windows.book_list_widget import BookListWidget
from ui.windows.book_card_widget import BookCardWidget
from ui.windows.add_book_dialog import AddBookDialog
from ui.windows.search_dialog import SearchDialog
from ui.windows.about_dialog import AboutDialog
from ui.windows.test_ocr_window import TestOcrWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """Главное MDI-окно приложения с интеграцией бизнес-логики."""

    def __init__(self, parent=None, book_service: BookService | None = None):
        super().__init__(parent)
        self.setupUi(self)
        
        # Inject service (dependency injection)
        self._book_service = book_service or BookService()
        
        self._connect_signals()
        self._update_status_bar()

    def _connect_signals(self):
        """Подключение всех кнопок и меню."""
        # Каталог
        self.action_add_book.triggered.connect(self._open_add_book)
        self.action_refresh.triggered.connect(self._open_book_list)
        self.action_search.triggered.connect(self._open_search)
        self.action_export.triggered.connect(self._on_export)

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

    # ========== КАТАЛОГ ==========

    def _open_book_list(self):
        """Открыть список книг."""
        try:
            sub_window = QMdiSubWindow()
            widget = BookListWidget(book_service=self._book_service, parent=self)
            sub_window.setWidget(widget)
            sub_window.setWindowTitle("Список книг")
            self.mdi_area.addSubWindow(sub_window)
            sub_window.show()
            self.statusbar.showMessage("Список книг обновлен", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть список книг: {e}")

    def _open_add_book(self):
        """Открыть диалог добавления книги."""
        try:
            dialog = AddBookDialog(book_service=self._book_service, parent=self)
            if dialog.exec_() == AddBookDialog.Accepted:
                # После добавления — обновить список
                self._open_book_list()
                self.statusbar.showMessage("Книга добавлена!", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить книгу: {e}")

    def _open_search(self):
        """Открыть поиск."""
        try:
            dialog = SearchDialog(book_service=self._book_service, parent=self)
            if dialog.exec_() == SearchDialog.Accepted:
                self.statusbar.showMessage("Поиск выполнен", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {e}")

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
        """OCR распознавание."""
        try:
            # Открываем полноценное OCR окно с TestOcrWindow
            self._ocr_window = TestOcrWindow()
            
            # Подключаемся к сигналу готовности данных
            self._ocr_window.ocr_data_ready.connect(self._on_ocr_data_ready)
            
            self._ocr_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка OCR: {e}")

    def _on_ocr_data_ready(self, ocr_data: dict):
        """Обработка распознанных данных из OCR."""
        try:
            # Открываем диалог добавления книги с распознанными данными
            add_dialog = AddBookDialog(
                book_service=self._book_service,
                ocr_data=ocr_data,
                parent=self
            )
            if add_dialog.exec_() == AddBookDialog.Accepted:
                self._open_book_list()
                self.statusbar.showMessage("Книга добавлена!", 3000)
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
        """О программе."""
        try:
            dialog = AboutDialog(parent=self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия окна 'О программе': {e}")

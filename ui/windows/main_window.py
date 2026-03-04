# ui/windows/main_window.py
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QMdiSubWindow
from ui.generated.ui_main_window import Ui_MainWindow

# Импорты всех дочерних окон
from ui.windows.book_list_widget import BookListWidget
from ui.windows.book_card_widget import BookCardWidget
from ui.windows.add_book_dialog import AddBookDialog
from ui.windows.search_dialog import SearchDialog
from ui.windows.about_dialog import AboutDialog


class MainWindow(QMainWindow, Ui_MainWindow):
    """Главное MDI-окно приложения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
    
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
    
    # ========== КАТАЛОГ ==========
    
    def _open_book_list(self):
        """Открыть список книг."""
        sub_window = QMdiSubWindow()
        widget = BookListWidget(parent=self)
        sub_window.setWidget(widget)
        sub_window.setWindowTitle("📚 Список книг")
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
    
    def _open_add_book(self):
        """Открыть диалог добавления книги."""
        dialog = AddBookDialog(parent=self)
        if dialog.exec_() == AddBookDialog.Accepted:
            # После добавления — обновить список
            self._open_book_list()
            self.statusbar.showMessage("✅ Книга добавлена!", 3000)
    
    def _open_search(self):
        """Открыть поиск."""
        dialog = SearchDialog(parent=self)
        if dialog.exec_() == SearchDialog.Accepted:
            self.statusbar.showMessage("🔍 Поиск выполнен", 3000)
    
    def _on_export(self):
        """Экспорт каталога."""
        QMessageBox.information(self, "Экспорт", "Функция экспорта в разработке")
    
    # ========== СЕРВИС ==========
    
    def _on_ocr(self):
        """OCR распознавание."""
        QMessageBox.information(self, "OCR", "Функция распознавания в разработке")
    
    def _on_generate_qr(self):
        """Генерация QR-кодов."""
        QMessageBox.information(self, "QR", "Функция генерации QR в разработке")
    
    # ========== СПРАВКА ==========
    
    def _open_about(self):
        """О программе."""
        dialog = AboutDialog(parent=self)
        dialog.exec_()
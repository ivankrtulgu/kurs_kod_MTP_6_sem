# ui/windows/book_list_widget.py
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QMessageBox
from ui.generated.ui_book_list_widget import Ui_BookListWidget


class BookListWidget(QWidget, Ui_BookListWidget):
    """Виджет списка книг."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
        self._fill_test_data()
    
    def _connect_signals(self):
        self.btn_search.clicked.connect(self._on_search)
        self.btn_refresh.clicked.connect(self._fill_test_data)
    
    def _fill_test_data(self):
        """Заполнить таблицу тестовыми данными."""
        test_books = [
            (1, "Иванов И.И.", "Основы программирования", 2024, "978-5-02-040500-0"),
            (2, "Петров П.П.", "Базы данных", 2023, "978-5-02-040501-7"),
            (3, "Сидоров С.С.", "Python для начинающих", 2024, "978-5-02-040502-4"),
        ]
        
        self.table_books.setRowCount(len(test_books))
        for row, book in enumerate(test_books):
            for col, value in enumerate(book):
                self.table_books.setItem(row, col, QTableWidgetItem(str(value)))
        
        self.label_status.setText(f"Всего: {len(test_books)} книг")
    
    def _on_search(self):
        query = self.input_search.text()
        if query:
            QMessageBox.information(self, "Поиск", f"Поиск: {query}")
        else:
            QMessageBox.warning(self, "Поиск", "Введите запрос для поиска")
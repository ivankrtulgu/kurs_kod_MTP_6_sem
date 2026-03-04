# ui/windows/search_dialog.py
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QMessageBox
from ui.generated.ui_search_dialog import Ui_SearchDialog


class SearchDialog(QDialog, Ui_SearchDialog):
    """Диалог поиска по каталогу."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
    
    def _connect_signals(self):
        self.btn_search.clicked.connect(self._on_search)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_close.clicked.connect(self.reject)
        self.btn_open.clicked.connect(self._on_open)
    
    def _on_search(self):
        """Выполнить поиск."""
        # Тестовые результаты
        test_results = [
            (1, "Иванов И.И.", "Основы программирования", 2024, "978-5-02-040500-0"),
            (3, "Сидоров С.С.", "Python для начинающих", 2024, "978-5-02-040502-4"),
        ]
        
        self.table_results.setRowCount(len(test_results))
        for row, book in enumerate(test_results):
            for col, value in enumerate(book):
                self.table_results.setItem(row, col, QTableWidgetItem(str(value)))
        
        QMessageBox.information(self, "Поиск", f"Найдено: {len(test_results)} книг")
    
    def _on_clear(self):
        """Очистить поля."""
        self.input_search_author.clear()
        self.input_search_title.clear()
        self.input_search_isbn.clear()
        self.input_search_udc.clear()
        self.table_results.setRowCount(0)
    
    def _on_open(self):
        """Открыть выбранную книгу."""
        row = self.table_results.currentRow()
        if row >= 0:
            QMessageBox.information(self, "Открыть", f"Открыть книгу ID: {self.table_results.item(row, 0).text()}")
        else:
            QMessageBox.warning(self, "Открыть", "Выберите книгу из списка")
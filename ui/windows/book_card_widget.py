# ui/windows/book_card_widget.py
from PyQt5.QtWidgets import QWidget, QMessageBox
from ui.generated.ui_book_card_widget import Ui_BookCardWidget


class BookCardWidget(QWidget, Ui_BookCardWidget):
    """Виджет карточки книги."""
    
    def __init__(self, book_id=1, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
        self._fill_test_data()
    
    def _connect_signals(self):
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_qr.clicked.connect(self._on_qr)
    
    def _fill_test_data(self):
        """Заполнить тестовыми данными."""
        self.label_author_value.setText("Иванов И.И.")
        self.label_title_value.setText("Основы программирования")
        self.label_year_value.setText("2024")
        self.label_isbn_value.setText("978-5-02-040500-0")
        self.label_udc_value.setText("004.43")
        self.label_bbk_value.setText("32.973")
        
        biblio = """Иванов И.И. Основы программирования : учебное пособие / 
Иванов И.И. — 2-е изд., перераб. и доп. — Москва : Наука, 2024. — 350 с. — 
ISBN 978-5-02-040500-0. — УДК 004.43; ББК 32.973"""
        self.text_biblio_record.setPlainText(biblio)
    
    def _on_edit(self):
        QMessageBox.information(self, "Редактирование", "Функция в разработке")
    
    def _on_delete(self):
        QMessageBox.warning(self, "Удаление", "Функция в разработке")
    
    def _on_export(self):
        QMessageBox.information(self, "Экспорт", "Функция в разработке")
    
    def _on_qr(self):
        QMessageBox.information(self, "QR-код", "Функция в разработке")
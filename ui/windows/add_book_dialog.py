# ui/windows/add_book_dialog.py
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from ui.generated.ui_add_book_dialog import Ui_AddBookDialog


class AddBookDialog(QDialog, Ui_AddBookDialog):
    """Диалог добавления книги."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connect_signals()
    
    def _connect_signals(self):
        self.btn_ocr.clicked.connect(self._on_ocr)
        self.btn_select_cover.clicked.connect(self._on_select_cover)
    
    def _on_ocr(self):
        """OCR распознавание."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            QMessageBox.information(self, "OCR", f"Выбран файл: {file_path}\n\nРаспознавание в разработке")
    
    def _on_select_cover(self):
        """Выбор обложки."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.input_cover_path.setText(file_path)
# ui/windows/ocr_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox
from ui.widgets.ocr_image_widget import OcrImageWidget
from PyQt5.QtCore import QRect


class OcrDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCR — Выделение области")
        
        layout = QVBoxLayout(self)
        
        # Кастомный виджет изображения
        self.image_widget = OcrImageWidget()
        layout.addWidget(self.image_widget)
        
        # Кнопки
        self.btn_load = QPushButton("Загрузить изображение")
        self.btn_load.clicked.connect(self._load_image)
        layout.addWidget(self.btn_load)
        
        self.btn_ocr = QPushButton("Распознать выделенную область")
        self.btn_ocr.clicked.connect(self._run_ocr)
        layout.addWidget(self.btn_ocr)
        
        # Подключение сигнала
        self.image_widget.region_selected.connect(self._on_region_selected)
    
    def _load_image(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image_widget.load_image(file_path)
    
    def _on_region_selected(self, rect: QRect):
        """Обработка выделенной области."""
        print(f"Выделена область: {rect}")
        # Здесь можно сразу запустить OCR для этой области
    
    def _run_ocr(self):
        cropped = self.image_widget.get_selected_image()
        if not cropped.isNull():
            # Запуск OCR для выделенной области
            cropped.save("temp/selected_region.png")
            QMessageBox.information(self, "OCR", "Область сохранена для распознавания")
        else:
            QMessageBox.warning(self, "OCR", "Сначала выделите область на изображении")
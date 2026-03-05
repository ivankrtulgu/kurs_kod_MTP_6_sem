# ui/windows/ocr_dialog.py
"""OCR dialog with OcrImageWidget integration."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox, QHBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import pyqtSignal
from ui.widgets.ocr_image_widget import OcrImageWidget
from PyQt5.QtCore import QRect


class OcrDialog(QDialog):
    """
    Диалог OCR с интеграцией OcrImageWidget.
    
    Provides OCR recognition for book fields using region selection.
    Returns recognized data to caller.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCR — Распознавание текста")
        self.setMinimumSize(900, 700)

        # Store recognized data
        self._recognized_data: dict = {}
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        
        # Info label
        self.info_label = QLabel(
            "Выделите 7 областей на изображении:\n"
            "1. Автор, 2. Название, 3. Издательство, 4. Год, "
            "5. ISBN, 6. УДК, 7. ББК"
        )
        self.info_label.setStyleSheet("color: #aaa; padding: 5px;")
        layout.addWidget(self.info_label)
        
        # Кастомный виджет изображения
        self.image_widget = OcrImageWidget()
        layout.addWidget(self.image_widget)
        
        # Progress bar for OCR
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Готов к работе")
        layout.addWidget(self.status_label)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("Загрузить изображение")
        self.btn_load.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_load)
        
        self.btn_ocr = QPushButton("Распознать все области")
        self.btn_ocr.setMinimumHeight(40)
        self.btn_ocr.setEnabled(False)
        btn_layout.addWidget(self.btn_ocr)
        
        self.btn_retry = QPushButton("Повторить выделение")
        self.btn_retry.setMinimumHeight(40)
        self.btn_retry.setEnabled(False)
        btn_layout.addWidget(self.btn_retry)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("Готово")
        self.btn_ok.setMinimumHeight(40)
        self.btn_ok.setEnabled(False)
        btn_layout.addWidget(self.btn_ok)
        
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_load.clicked.connect(self._load_image)
        self.btn_ocr.clicked.connect(self._run_ocr)
        self.btn_retry.clicked.connect(self._retry_regions)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_accept)
        
        # Подключение сигнала выделения области
        self.image_widget.region_completed.connect(self._on_regions_completed)

    def _load_image(self):
        """Load image for OCR."""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", 
            "Images (*.png *.jpg *.jpeg);;All files (*)"
        )
        if file_path:
            try:
                self.image_widget.load_image(file_path)
                self.status_label.setText(f"Загружено: {file_path}")
                self.btn_ocr.setEnabled(False)
                self.btn_ok.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение: {e}")

    def _on_regions_completed(self, regions: list):
        """Handle when all 7 regions are selected."""
        self.status_label.setText(f"Выделено областей: {len(regions)}. Нажмите 'Распознать'")
        self.btn_ocr.setEnabled(True)
        self.btn_retry.setEnabled(True)

    def _retry_regions(self):
        """Reset regions for re-selection."""
        self.image_widget.reset_regions()
        self._recognized_data = {}
        self.status_label.setText("Выделите области заново")
        self.btn_ocr.setEnabled(False)
        self.btn_retry.setEnabled(False)
        self.btn_ok.setEnabled(False)

    def _run_ocr(self):
        """Run OCR on all selected regions."""
        try:
            if not self.image_widget.regions:
                QMessageBox.warning(self, "OCR", "Сначала выделите области на изображении")
                return
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.image_widget.regions))
            self.status_label.setText("Распознавание...")
            
            # Region names mapping
            region_names = [
                'author', 'title', 'publisher', 'year', 
                'isbn', 'udc', 'bbk'
            ]
            
            # Process each region
            for i, region in enumerate(self.image_widget.regions):
                self.progress_bar.setValue(i + 1)
                
                # Get region image with applied adjustments
                pixmap = self.image_widget.get_region_image(region.id, use_adjusted=True)
                
                if not pixmap.isNull():
                    # Recognize text based on region type
                    region_name = region_names[i] if i < len(region_names) else f'field_{i}'
                    
                    # Choose OCR language based on field type
                    if region_name in ['year', 'isbn', 'udc', 'bbk']:
                        lang = 'digits'  # Numbers only
                    else:
                        lang = 'rus+eng'  # Russian and English
                    
                    text = self.image_widget.recognize_text(pixmap, lang=lang)
                    
                    # Post-process recognized text
                    text = self._post_process_text(text, region_name)
                    
                    self._recognized_data[region_name] = text
                    region.ocr_text = text

                    self.status_label.setText(f"Распознано: {region.name} -> {text[:50]}...")
            
            self.progress_bar.setVisible(False)
            self.btn_ok.setEnabled(True)
            
            QMessageBox.information(
                self, "OCR завершено",
                f"Распознано {len(self._recognized_data)} полей"
            )
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Ошибка OCR", f"Ошибка распознавания: {e}")

    def _post_process_text(self, text: str, field_name: str) -> str:
        """
        Post-process recognized text based on field type.
        
        Args:
            text: Raw recognized text.
            field_name: Name of the field being processed.
            
        Returns:
            str: Cleaned text.
        """
        if not text:
            return ""
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        # Field-specific processing
        if field_name == 'year':
            # Extract 4-digit year
            import re
            match = re.search(r'\b(19|20|21)\d{2}\b', text)
            if match:
                return match.group()
            # Try to extract any 4 digits
            match = re.search(r'\b\d{4}\b', text)
            if match:
                return match.group()
                
        elif field_name == 'isbn':
            # Clean ISBN: remove spaces, keep digits and hyphens
            import re
            text = re.sub(r'[^\d\-Xx]', '', text)
            
        elif field_name == 'udc':
            # UDC format: numbers with dots
            import re
            match = re.search(r'[\d.]+', text)
            if match:
                return match.group()
                
        elif field_name == 'bbk':
            # BBK format: numbers with dots
            import re
            match = re.search(r'[\d.]+', text)
            if match:
                return match.group()
        
        return text

    def _on_accept(self):
        """Accept dialog and return recognized data."""
        if not self._recognized_data:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Данные не распознаны. Всё равно завершить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.accept()

    def get_recognized_data(self) -> dict:
        """
        Get recognized data as dictionary.
        
        Returns:
            dict: Recognized field values with keys:
                  author, title, publisher, year, isbn, udc, bbk, pages
        """
        return self._recognized_data.copy()

    def closeEvent(self, event):
        """Cleanup on close."""
        self.image_widget.closeEvent(event)
        super().closeEvent(event)

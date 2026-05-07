# ui/windows/test_ocr_window.py

import sys
import os

# Фикс импорта
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ===== ФИКС QT PLUGIN =====
import PyQt5
pyqt5_path = os.path.dirname(PyQt5.__file__)

plugin_paths = [
    os.path.join(pyqt5_path, 'Qt5', 'plugins'),
    os.path.join(pyqt5_path, 'Qt', 'plugins'),
    os.path.join(pyqt5_path, 'plugins'),
    os.path.join(os.path.dirname(pyqt5_path), 'plugins'),
]

qt_plugin_path = None
for plugin_path in plugin_paths:
    if os.path.exists(plugin_path):
        qt_plugin_path = plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugin_path, 'platforms')
        os.environ['QT_IMAGEFORMATS_PATH'] = os.path.join(plugin_path, 'imageformats')
        print(f" Qt plugins path: {plugin_path}")
        break
# ==========================

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QApplication,
    QSlider, QScrollArea, QComboBox, QAbstractItemView
)
from PyQt5.QtCore import QRect, Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImageReader, QImage


from ui.widgets.ocr_image_widget import OcrImageWidget
from ui.style_manager import StyleManager
from ui.icon_manager import IconManager


class OcrWindow(QWidget):
    """Окно OCR распознавания для MDI (на основе TestOcrWindow)."""
    WINDOW_TITLE = "OCR распознавание"

    # Signal when OCR data is ready
    ocr_data_ready = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Store recognized data
        self._recognized_data: dict = {}

        # Debounce timer for brightness/contrast adjustments
        self._adjustment_timer = QTimer()
        self._adjustment_timer.setSingleShot(True)
        self._adjustment_timer.setInterval(50)  # 150ms delay
        self._adjustment_timer.timeout.connect(self._apply_image_settings_delayed)

        # Set window icon if parent is a window
        if parent and hasattr(parent, 'setWindowIcon'):
            parent.setWindowIcon(IconManager.get_default_icon())

        #  Применяем светлую тему ко всему приложению
        self.setStyleSheet(StyleManager.get_stylesheet())

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ===== ЛЕВАЯ ЧАСТЬ: Изображение =====
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        
        #  Скролл-область для изображения
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setAlignment(Qt.AlignCenter)
        # Удалены жесткие минимальные размеры (800, 600) для гибкости интерфейса
        
        self.image_widget = OcrImageWidget()
        self.image_widget.setStyleSheet("background-color: #2d3748; border-radius: 8px;")
        scroll_area.setWidget(self.image_widget)
        
        left_layout.addWidget(scroll_area, stretch=1)
        
        #  Панель настроек изображения
        settings_group = QGroupBox(" Настройки изображения")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        # Яркость
        brightness_layout = QHBoxLayout()
        brightness_label = QLabel("Яркость")
        brightness_label.setStyleSheet("font-weight: 500; color: #68a385;")
        brightness_label.setFixedWidth(90)
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(self._on_brightness_changed)
        self.label_brightness_value = QLabel("0")
        self.label_brightness_value.setFixedWidth(35)
        self.label_brightness_value.setStyleSheet("""
            background-color: #f0fff4;
            color: #68a385;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
        """)
        self.label_brightness_value.setAlignment(Qt.AlignCenter)
        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(self.slider_brightness)
        brightness_layout.addWidget(self.label_brightness_value)
        settings_layout.addLayout(brightness_layout)
        
        # Контраст
        contrast_layout = QHBoxLayout()
        contrast_label = QLabel("Контраст")
        contrast_label.setStyleSheet("font-weight: 500; color: #68a385;")
        contrast_label.setFixedWidth(90)
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(-100, 100)
        self.slider_contrast.setValue(0)
        self.slider_contrast.valueChanged.connect(self._on_contrast_changed)
        self.label_contrast_value = QLabel("0")
        self.label_contrast_value.setFixedWidth(35)
        self.label_contrast_value.setStyleSheet("""
            background-color: #f0fff4;
            color: #68a385;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
        """)
        self.label_contrast_value.setAlignment(Qt.AlignCenter)
        contrast_layout.addWidget(contrast_label)
        contrast_layout.addWidget(self.slider_contrast)
        contrast_layout.addWidget(self.label_contrast_value)
        settings_layout.addLayout(contrast_layout)

        # Кнопка сброса настроек
        btn_reset_settings = QPushButton(" Сбросить настройки")
        btn_reset_settings.clicked.connect(self._reset_image_settings)
        btn_reset_settings.setStyleSheet("""
            QPushButton {
                background-color: #f8faf9;
                border: 1px solid #e2e8f0;
            }
            QPushButton:hover {
                background-color: #f0fff4;
                border-color: #68a385;
            }
        """)
        settings_layout.addWidget(btn_reset_settings)

        left_layout.addWidget(settings_group)
        
        #  Настройки языка распознавания
        lang_group = QGroupBox("Язык распознавания")
        lang_layout = QVBoxLayout(lang_group)
        lang_layout.setSpacing(8)
        
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Русский", "rus")
        self.combo_lang.addItem("Английский", "eng")
        self.combo_lang.addItem("Русский + English (смешанный)", "rus+eng")
        self.combo_lang.addItem("Английский + Русский (приоритет EN)", "eng+rus")
        self.combo_lang.addItem("Цифры и символы", "digits")
        self.combo_lang.setCurrentIndex(2)  # По умолчанию rus+eng
        lang_layout.addWidget(self.combo_lang)
        
        left_layout.addWidget(lang_group)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_load = QPushButton(" Загрузить")
        self.btn_load.clicked.connect(self._load_image)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #f8faf9;
            }
            QPushButton:hover {
                background-color: #f0fff4;
                border-color: #68a385;
            }
        """)
        btn_layout.addWidget(self.btn_load)

        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.clicked.connect(self._reset_regions)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #fff5f5;
                border-color: #fed7d7;
                color: #e53e3e;
            }
            QPushButton:hover {
                background-color: #fed7d7;
                border-color: #e53e3e;
                color: #c53030;
            }
        """)
        btn_layout.addWidget(self.btn_reset)

        self.btn_ocr = QPushButton("Распознать")
        self.btn_ocr.clicked.connect(self._run_ocr)
        self.btn_ocr.setStyleSheet("""
            QPushButton {
                background-color: #68a385;
                border: none;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4a9f6e;
            }
            QPushButton:pressed {
                background-color: #3d8b5f;
            }
        """)
        btn_layout.addWidget(self.btn_ocr)

        self.btn_export = QPushButton("Экспорт")
        self.btn_export.clicked.connect(self._export_regions)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #ebf8ff;
                border-color: #bee3f8;
                color: #3182ce;
            }
            QPushButton:hover {
                background-color: #bee3f8;
                border-color: #3182ce;
            }
        """)
        btn_layout.addWidget(self.btn_export)

        left_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, stretch=2)

        # ===== ПРАВАЯ ЧАСТЬ: Информация =====
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # Статус
        status_group = QGroupBox("Статус")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)

        self.label_status = QLabel("Изображение не загружено")
        self.label_status.setStyleSheet("color: #718096; font-style: italic;")
        status_layout.addWidget(self.label_status)

        self.label_progress = QLabel("Области: 0/10")
        self.label_progress.setStyleSheet("font-weight: 600; color: #68a385;")
        status_layout.addWidget(self.label_progress)

        self.label_image_size = QLabel("Размер: —")
        self.label_image_size.setStyleSheet("color: #a0aec0;")
        status_layout.addWidget(self.label_image_size)

        right_layout.addWidget(status_group)
        
        # Список областей
        regions_group = QGroupBox("Выделенные области")
        regions_layout = QVBoxLayout(regions_group)
        regions_layout.setSpacing(0)
        
        self.table_regions = QTableWidget()
        self.table_regions.setColumnCount(5)
        self.table_regions.setHorizontalHeaderLabels(
            ["ID", "Область", "Размер", "Текст", "Статус"]
        )
        self.table_regions.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table_regions.itemChanged.connect(self._on_table_item_changed)
        self.table_regions.horizontalHeader().setStretchLastSection(True)
        self.table_regions.setColumnWidth(0, 45)
        self.table_regions.setColumnWidth(1, 100)
        self.table_regions.setColumnWidth(2, 85)
        self.table_regions.setColumnWidth(3, 180)
        self.table_regions.verticalHeader().setVisible(False)
        regions_layout.addWidget(self.table_regions)
        
        right_layout.addWidget(regions_group)
        
        # Предпросмотр
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(0)
        
        self.label_preview = QLabel()
        self.label_preview.setMinimumSize(200, 100)
        self.label_preview.setMaximumHeight(120)
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setStyleSheet("""
            background-color: #f7fafc;
            border: 2px dashed #e2e8f0;
            border-radius: 8px;
        """)
        preview_layout.addWidget(self.label_preview)
        
        right_layout.addWidget(preview_group)
        
        # Результат OCR
        ocr_group = QGroupBox("Результат OCR")
        ocr_layout = QVBoxLayout(ocr_group)
        ocr_layout.setSpacing(0)
        
        self.text_ocr_result = QLabel("Распознанный текст появится здесь...")
        self.text_ocr_result.setWordWrap(True)
        self.text_ocr_result.setStyleSheet("""
            background-color: #f8faf9;
            color: #4a5568;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        """)
        self.text_ocr_result.setMinimumHeight(150)
        ocr_layout.addWidget(self.text_ocr_result)
        
        right_layout.addWidget(ocr_group)

        # Кнопка "Применить данные"
        self.btn_apply = QPushButton(" Применить данные")
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_apply.setEnabled(False)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #68a385;
                border: none;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #4a9f6e;
            }
            QPushButton:pressed {
                background-color: #3d8b5f;
            }
            QPushButton:disabled {
                background-color: #cbd5e0;
            }
        """)
        right_layout.addWidget(self.btn_apply)
        
        right_layout.addStretch()
        
        main_layout.addLayout(right_layout, stretch=1)

        # ===== Подключение сигналов =====
        self.image_widget.region_selected.connect(self._on_region_selected)
        self.image_widget.region_completed.connect(self._on_region_completed)
        self.image_widget.image_loaded.connect(self._on_image_loaded)
    
    def _load_image(self):
        """Загрузить изображение."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите изображение титульного листа", 
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)"
        )
        
        if file_path:
            print(f" Выбран файл: {file_path}")
            
            if not os.path.exists(file_path):
                print(f" Файл не существует: {file_path}")
                QMessageBox.warning(self, "Ошибка", f"Файл не найден:\n{file_path}")
                return
            
            self.image_widget.load_image(file_path)
    
    def _on_image_loaded(self, path: str):
        """Изображение загружено."""
        self.label_status.setText(f"Загружено: {os.path.basename(path)}")
        self.label_progress.setText("Области: 0/10")
        
        self.label_image_size.setText(f"Размер: {self.image_widget.source_pixmap.width()}x{self.image_widget.source_pixmap.height()}")
        
        self._reset_image_settings()
        self._update_table()
    
    def _on_brightness_changed(self, value):
        """Изменение яркости."""
        self.label_brightness_value.setText(str(value))
        # Restart timer on each slider change
        self._adjustment_timer.stop()
        self._adjustment_timer.start()

    def _on_contrast_changed(self, value):
        """Изменение контраста."""
        self.label_contrast_value.setText(str(value))
        # Restart timer on each slider change
        self._adjustment_timer.stop()
        self._adjustment_timer.start()

    def _apply_image_settings_delayed(self):
        """Apply image settings after debounce delay."""
        brightness = self.slider_brightness.value()
        contrast = self.slider_contrast.value()
        self.image_widget.apply_image_adjustments(brightness, contrast)
    
    def _reset_image_settings(self):
        """Сбросить настройки изображения."""
        self.slider_brightness.setValue(0)
        self.slider_contrast.setValue(0)
        self.image_widget.reset_image_settings()

    def _on_region_selected(self, region_id: int, rect: QRect):
        """Область выделена."""
        self.label_progress.setText(f"Области: {region_id + 1}/10")
        self._update_table()

        #  Предпросмотр с применёнными настройками (яркость/контраст)
        cropped = self.image_widget.get_region_image(region_id, use_adjusted=True)
        if not cropped.isNull():
            self.label_preview.setPixmap(
                cropped.scaled(200, 100, Qt.KeepAspectRatio)
            )
    
    def _on_region_completed(self, regions: list):
        """Все 7 областей выделены."""
        self.label_status.setText(" Все области выделены!")
        self.label_progress.setText("Области: 10/10 — Готово!")
        self.btn_apply.setEnabled(True)

        QMessageBox.information(
            self, "Завершено",
            "Все 7 областей выделены!\n\n"
            "Нажмите 'Распознать текст (OCR)' для распознавания."
        )
    
    def _update_table(self):
        """Обновить таблицу областей."""
        self.table_regions.blockSignals(True) # Block signals to avoid recursion during update
        regions = self.image_widget.regions
        self.table_regions.setRowCount(len(regions))
        
        for i, region in enumerate(regions):
            self.table_regions.setItem(i, 0, QTableWidgetItem(str(region.id)))
            self.table_regions.setItem(i, 1, QTableWidgetItem(region.name))
            self.table_regions.setItem(i, 2, 
                QTableWidgetItem(f"{region.rect.width()}x{region.rect.height()}"))
            
            ocr_text = region.ocr_text if hasattr(region, 'ocr_text') else "-"
            item_text = QTableWidgetItem(ocr_text[:30] + "..." if len(ocr_text) > 30 else ocr_text)
            # Allow editing for the text column
            item_text.setFlags(item_text.flags() | Qt.ItemIsEditable)
            self.table_regions.setItem(i, 3, item_text)
            
            self.table_regions.setItem(i, 4, QTableWidgetItem(""))
        self.table_regions.blockSignals(False)
    
    def _on_table_item_changed(self, item):
        """Update OcrRegion data when table cell is edited."""
        row = item.row()
        col = item.column()
        
        if col == 3: # Text column
            regions = self.image_widget.regions
            if row < len(regions):
                regions[row].ocr_text = item.text()
                print(f" Updated region {regions[row].id} text: {item.text()}")
    
    def _run_ocr(self):
        """Запустить распознавание текста."""
        if not self.image_widget.regions:
            QMessageBox.warning(self, "Ошибка", "Сначала выделите области!")
            return

        #  Получаем выбранный язык
        lang = self.combo_lang.currentData()
        lang_name = self.combo_lang.currentText()

        print("\n" + "="*60)
        print("НАЧАЛО РАСПОЗНАВАНИЯ ТЕКСТА (OCR)")
        print("="*60)
        print(f" Язык: {lang_name} ({lang})")

        #  Проверяем, есть ли отличия от оригинала
        has_adjustments = (
            self.image_widget.brightness_value != 0 or
            self.image_widget.contrast_value != 0
        )

        # if has_adjustments:
        #     print(f" Используются настройки: яркость={self.image_widget.brightness_value}, контраст={self.image_widget.contrast_value}")

        ocr_results = []

        for region in self.image_widget.regions:
            #  Получаем область с применёнными настройками яркости/контраста
            cropped = self.image_widget.get_region_image(region.id, use_adjusted=True)
            if not cropped.isNull():
                text = self.image_widget.recognize_text(cropped, lang=lang)
                region.ocr_text = text

                ocr_results.append({
                    'id': region.id,
                    'name': region.name,
                    'text': text
                })

                print(f"\nОбласть #{region.id} — {region.name}:")
                print(f"   Размер: {region.rect.width()}x{region.rect.height()}")
                print(f"   Текст: {text if text else '(не распознано)'}")
                print("-"*60)
        
        self._update_table()
        
        full_text = "\n".join([f"{r['name']}: {r['text']}" for r in ocr_results])
        self.text_ocr_result.setText(full_text if full_text else "Текст не распознан")
        
        print("\n" + "="*60)
        print(" РАСПОЗНАВАНИЕ ЗАВЕРШЕНО")
        print("="*60 + "\n")
        
        QMessageBox.information(
            self, "OCR завершён",
            f"Распознано {len(ocr_results)} областей!\n"
            "Результат выведен в консоль и в окно."
        )
    
    def _reset_regions(self):
        """Сбросить все области."""
        self.image_widget.reset_regions()
        self.label_status.setText("Области сброшены")
        self.label_progress.setText("Области: 0/10")
        self.table_regions.setRowCount(0)
        self.label_preview.clear()
        self.text_ocr_result.setText("Распознанный текст появится здесь...")
    
    def _export_regions(self):
        """Экспортировать области."""
        if not self.image_widget.regions:
            QMessageBox.warning(self, "Ошибка", "Сначала выделите области!")
            return
        
        os.makedirs("temp/ocr_regions", exist_ok=True)
        
        for region in self.image_widget.regions:
            cropped = self.image_widget.get_region_image(region.id)
            if not cropped.isNull():
                filename = f"temp/ocr_regions/region_{region.id}_{region.name}.png"
                cropped.save(filename)
        
        QMessageBox.information(
            self, "Экспорт завершён",
            f"Сохранено {len(self.image_widget.regions)} областей\n"
            "в папку: temp/ocr_regions/"
        )

    def _close_window(self):
        """Close the MDI subwindow containing this widget."""
        from PyQt5.QtWidgets import QMdiSubWindow
        parent = self.parent()
        if isinstance(parent, QMdiSubWindow):
            parent.close()
        else:
            self.close()

    def _on_apply(self):
        """Применить данные и закрыть окно."""
        ocr_data = self._get_recognized_data()
        if ocr_data:
            self.ocr_data_ready.emit(ocr_data)
        
        self._close_window()
        
        # Дополнительное уведомление для уверенности в перенаправлении
        print(" OCR data emitted, closing OCR window...")

    def _get_recognized_data(self) -> dict:
        """Получить распознанные данные для AddBookWidget."""
        data = {}
        for region in self.image_widget.regions:
            if region.ocr_text:
                if region.id == 0:  # Author
                    data['author'] = region.ocr_text
                elif region.id == 1:  # Title
                    data['title'] = region.ocr_text
                elif region.id == 2:  # Place
                    data['place'] = region.ocr_text
                elif region.id == 3:  # Publisher
                    data['publisher'] = region.ocr_text
                elif region.id == 4:  # Year
                    data['year'] = region.ocr_text
                elif region.id == 5:  # ISBN
                    data['isbn'] = region.ocr_text
                elif region.id == 6:  # UDC
                    data['udc'] = region.ocr_text
                elif region.id == 7:  # BBK
                    data['bbk'] = region.ocr_text
                elif region.id == 8:  # Annotation
                    data['annotation'] = region.ocr_text
                elif region.id == 9:  # Author Mark
                    data['author_mark'] = region.ocr_text
        return data


def run_test():
    """Запустить тестовое окно."""
    app = QApplication(sys.argv)
    window = OcrWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_test()
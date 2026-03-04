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
        print(f"✅ Qt plugins path: {plugin_path}")
        break
# ==========================

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QApplication,
    QSlider, QScrollArea, QComboBox
)
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPixmap, QImageReader, QImage


from widgets.ocr_image_widget import OcrImageWidget


class TestOcrWindow(QMainWindow):
    """Тестовое окно для проверки OcrImageWidget с 7 областями."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OCR — Разметка титульного листа (7 областей)")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # ===== ЛЕВАЯ ЧАСТЬ: Изображение =====
        left_layout = QVBoxLayout()
        
        # 🔧 Скролл-область для изображения
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: #1a1a1a;")
        scroll_area.setMinimumSize(800, 600)
        
        self.image_widget = OcrImageWidget()
        scroll_area.setWidget(self.image_widget)
        
        left_layout.addWidget(scroll_area, stretch=1)
        
        # 🔧 Панель настроек изображения
        settings_group = QGroupBox("🎨 Настройки изображения")
        settings_layout = QVBoxLayout(settings_group)
        
        # Яркость
        brightness_layout = QHBoxLayout()
        brightness_label = QLabel("☀️ Яркость:")
        brightness_label.setFixedWidth(80)
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(-100, 100)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(self._on_brightness_changed)
        self.label_brightness_value = QLabel("0")
        self.label_brightness_value.setFixedWidth(30)
        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(self.slider_brightness)
        brightness_layout.addWidget(self.label_brightness_value)
        settings_layout.addLayout(brightness_layout)
        
        # Контраст
        contrast_layout = QHBoxLayout()
        contrast_label = QLabel("🔲 Контраст:")
        contrast_label.setFixedWidth(80)
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(-100, 100)
        self.slider_contrast.setValue(0)
        self.slider_contrast.valueChanged.connect(self._on_contrast_changed)
        self.label_contrast_value = QLabel("0")
        self.label_contrast_value.setFixedWidth(30)
        contrast_layout.addWidget(contrast_label)
        contrast_layout.addWidget(self.slider_contrast)
        contrast_layout.addWidget(self.label_contrast_value)
        settings_layout.addLayout(contrast_layout)

        # Кнопка сброса настроек
        btn_reset_settings = QPushButton("🔄 Сбросить настройки")
        btn_reset_settings.clicked.connect(self._reset_image_settings)
        settings_layout.addWidget(btn_reset_settings)

        left_layout.addWidget(settings_group)
        
        # 🔧 Настройки языка распознавания
        lang_group = QGroupBox("🌐 Язык распознавания")
        lang_layout = QVBoxLayout(lang_group)
        
        lang_info_label = QLabel("Выберите приоритетный язык:")
        lang_info_label.setStyleSheet("color: #aaa;")
        lang_layout.addWidget(lang_info_label)
        
        # 🔧 Выпадающий список языков
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇷🇺 Русский", "rus")
        self.combo_lang.addItem("🇬🇧 English", "eng")
        self.combo_lang.addItem("🇷🇺🇬🇧 Русский + English (смешанный)", "rus+eng")
        self.combo_lang.addItem("🇬🇧🇷🇺 English + Русский (приоритет EN)", "eng+rus")
        self.combo_lang.addItem("🔢 Цифры и символы", "digits")
        self.combo_lang.setCurrentIndex(2)  # По умолчанию rus+eng
        self.combo_lang.setStyleSheet("""
            QComboBox {
                padding: 5px;
                background-color: #2a2a2a;
                color: #fff;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #aaa;
                margin-right: 5px;
            }
        """)
        lang_layout.addWidget(self.combo_lang)
        
        left_layout.addWidget(lang_group)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.btn_load = QPushButton("📁 Загрузить изображение")
        self.btn_load.clicked.connect(self._load_image)
        btn_layout.addWidget(self.btn_load)

        self.btn_reset = QPushButton("🗑 Сбросить области")
        self.btn_reset.clicked.connect(self._reset_regions)
        btn_layout.addWidget(self.btn_reset)

        self.btn_ocr = QPushButton("🔍 Распознать текст (OCR)")
        self.btn_ocr.clicked.connect(self._run_ocr)
        self.btn_ocr.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_layout.addWidget(self.btn_ocr)

        self.btn_export = QPushButton("💾 Экспорт областей")
        self.btn_export.clicked.connect(self._export_regions)
        btn_layout.addWidget(self.btn_export)

        left_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, stretch=2)

        # ===== ПРАВАЯ ЧАСТЬ: Информация =====
        right_layout = QVBoxLayout()

        # Статус
        status_group = QGroupBox("📊 Статус")
        status_layout = QVBoxLayout(status_group)

        self.label_status = QLabel("Изображение не загружено")
        status_layout.addWidget(self.label_status)

        self.label_progress = QLabel("Области: 0/7")
        status_layout.addWidget(self.label_progress)

        self.label_image_size = QLabel("Размер: -")
        status_layout.addWidget(self.label_image_size)

        right_layout.addWidget(status_group)
        
        # Список областей
        regions_group = QGroupBox("📋 Выделенные области")
        regions_layout = QVBoxLayout(regions_group)
        
        self.table_regions = QTableWidget()
        self.table_regions.setColumnCount(5)
        self.table_regions.setHorizontalHeaderLabels(
            ["ID", "Область", "Размер", "Текст", "Статус"]
        )
        self.table_regions.horizontalHeader().setStretchLastSection(True)
        self.table_regions.setColumnWidth(0, 40)
        self.table_regions.setColumnWidth(1, 100)
        self.table_regions.setColumnWidth(2, 80)
        self.table_regions.setColumnWidth(3, 200)
        regions_layout.addWidget(self.table_regions)
        
        right_layout.addWidget(regions_group)
        
        # Предпросмотр
        preview_group = QGroupBox("👁 Предпросмотр последней области")
        preview_layout = QVBoxLayout(preview_group)
        
        self.label_preview = QLabel()
        self.label_preview.setMinimumSize(200, 100)
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setStyleSheet("background-color: #333;")
        preview_layout.addWidget(self.label_preview)
        
        right_layout.addWidget(preview_group)
        
        # Результат OCR
        ocr_group = QGroupBox("📝 Результат OCR")
        ocr_layout = QVBoxLayout(ocr_group)
        
        self.text_ocr_result = QLabel("Распознанный текст появится здесь...")
        self.text_ocr_result.setWordWrap(True)
        self.text_ocr_result.setStyleSheet("background-color: #2a2a2a; color: #0f0; padding: 10px;")
        self.text_ocr_result.setMinimumHeight(150)
        ocr_layout.addWidget(self.text_ocr_result)
        
        right_layout.addWidget(ocr_group)
        
        right_layout.addStretch()
        
        self.btn_close = QPushButton("❌ Закрыть")
        self.btn_close.clicked.connect(self.close)
        right_layout.addWidget(self.btn_close)
        
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
            print(f"📁 Выбран файл: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"❌ Файл не существует: {file_path}")
                QMessageBox.warning(self, "Ошибка", f"Файл не найден:\n{file_path}")
                return
            
            self.image_widget.load_image(file_path)
    
    def _on_image_loaded(self, path: str):
        """Изображение загружено."""
        self.label_status.setText(f"Загружено: {os.path.basename(path)}")
        self.label_progress.setText("Области: 0/7")
        
        self.label_image_size.setText(f"Размер: {self.image_widget.source_pixmap.width()}x{self.image_widget.source_pixmap.height()}")
        
        self._reset_image_settings()
        self._update_table()
    
    def _on_brightness_changed(self, value):
        """Изменение яркости."""
        self.label_brightness_value.setText(str(value))
        self._apply_image_settings(silent=True)
    
    def _on_contrast_changed(self, value):
        """Изменение контраста."""
        self.label_contrast_value.setText(str(value))
        self._apply_image_settings(silent=True)
    
    def _reset_image_settings(self):
        """Сбросить настройки изображения."""
        self.slider_brightness.setValue(0)
        self.slider_contrast.setValue(0)
        self.image_widget.reset_image_settings()
    
    def _apply_image_settings(self, silent: bool = False):
        """Применить настройки яркости и контраста."""
        brightness = self.slider_brightness.value()
        contrast = self.slider_contrast.value()
        
        self.image_widget.apply_image_adjustments(brightness, contrast)
    
    def _on_region_selected(self, region_id: int, rect: QRect):
        """Область выделена."""
        self.label_progress.setText(f"Области: {region_id + 1}/7")
        self._update_table()

        # 🔧 Предпросмотр с применёнными настройками (яркость/контраст)
        cropped = self.image_widget.get_region_image(region_id, use_adjusted=True)
        if not cropped.isNull():
            self.label_preview.setPixmap(
                cropped.scaled(200, 100, Qt.KeepAspectRatio)
            )
    
    def _on_region_completed(self, regions: list):
        """Все 7 областей выделены."""
        self.label_status.setText("✅ Все области выделены!")
        self.label_progress.setText("Области: 7/7 — Готово!")
        
        QMessageBox.information(
            self, "Завершено",
            "Все 7 областей выделены!\n\n"
            "Нажмите '🔍 Распознать текст (OCR)' для распознавания."
        )
    
    def _update_table(self):
        """Обновить таблицу областей."""
        regions = self.image_widget.regions
        self.table_regions.setRowCount(len(regions))
        
        for i, region in enumerate(regions):
            self.table_regions.setItem(i, 0, QTableWidgetItem(str(region.id)))
            self.table_regions.setItem(i, 1, QTableWidgetItem(region.name))
            self.table_regions.setItem(i, 2, 
                QTableWidgetItem(f"{region.rect.width()}x{region.rect.height()}"))
            
            ocr_text = region.ocr_text if hasattr(region, 'ocr_text') else "-"
            self.table_regions.setItem(i, 3, QTableWidgetItem(ocr_text[:30] + "..." if len(ocr_text) > 30 else ocr_text))
            
            self.table_regions.setItem(i, 4, QTableWidgetItem("✅"))
    
    def _run_ocr(self):
        """Запустить распознавание текста."""
        if not self.image_widget.regions:
            QMessageBox.warning(self, "Ошибка", "Сначала выделите области!")
            return

        # 🔧 Получаем выбранный язык
        lang = self.combo_lang.currentData()
        lang_name = self.combo_lang.currentText()

        print("\n" + "="*60)
        print("🔍 НАЧАЛО РАСПОЗНАВАНИЯ ТЕКСТА (OCR)")
        print("="*60)
        print(f"🌐 Язык: {lang_name} ({lang})")

        # 🔧 Проверяем, есть ли отличия от оригинала
        has_adjustments = (
            self.image_widget.brightness_value != 0 or
            self.image_widget.contrast_value != 0
        )

        # if has_adjustments:
        #     print(f"🎨 Используются настройки: яркость={self.image_widget.brightness_value}, контраст={self.image_widget.contrast_value}")

        ocr_results = []

        for region in self.image_widget.regions:
            # 🔧 Получаем область с применёнными настройками яркости/контраста
            cropped = self.image_widget.get_region_image(region.id, use_adjusted=True)
            if not cropped.isNull():
                text = self.image_widget.recognize_text(cropped, lang=lang)
                region.ocr_text = text

                ocr_results.append({
                    'id': region.id,
                    'name': region.name,
                    'text': text
                })

                print(f"\n📋 Область #{region.id} — {region.name}:")
                print(f"   Размер: {region.rect.width()}x{region.rect.height()}")
                print(f"   Текст: {text if text else '(не распознано)'}")
                print("-"*60)
        
        self._update_table()
        
        full_text = "\n".join([f"{r['name']}: {r['text']}" for r in ocr_results])
        self.text_ocr_result.setText(full_text if full_text else "Текст не распознан")
        
        print("\n" + "="*60)
        print("✅ РАСПОЗНАВАНИЕ ЗАВЕРШЕНО")
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
        self.label_progress.setText("Области: 0/7")
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


def run_test():
    """Запустить тестовое окно."""
    app = QApplication(sys.argv)
    window = TestOcrWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_test()
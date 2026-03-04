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

# Пути к плагинам
plugin_paths = [
    os.path.join(pyqt5_path, 'Qt5', 'plugins'),
    os.path.join(pyqt5_path, 'Qt', 'plugins'),
    os.path.join(pyqt5_path, 'plugins'),
]

for plugin_path in plugin_paths:
    if os.path.exists(plugin_path):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(plugin_path, 'platforms')
        os.environ['QT_IMAGEFORMATS_PATH'] = plugin_path  # 🔧 ВАЖНО ДЛЯ ИЗОБРАЖЕНИЙ
        print(f"✅ Qt plugins path: {plugin_path}")
        break
# ==========================

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QRect, Qt  # ← Qt добавлен
from PyQt5.QtGui import QPixmap, QImageReader  # ← Добавь QImageReader


from widgets.ocr_image_widget import OcrImageWidget


class TestOcrWindow(QMainWindow):
    """Тестовое окно для проверки OcrImageWidget с 7 областями."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("OCR — Разметка титульного листа (7 областей)")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # ===== ЛЕВАЯ ЧАСТЬ: Изображение =====
        left_layout = QVBoxLayout()
        
        self.image_widget = OcrImageWidget()
        left_layout.addWidget(self.image_widget, stretch=1)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("📁 Загрузить изображение")
        self.btn_load.clicked.connect(self._load_image)
        btn_layout.addWidget(self.btn_load)
        
        self.btn_reset = QPushButton("🗑 Сбросить области")
        self.btn_reset.clicked.connect(self._reset_regions)
        btn_layout.addWidget(self.btn_reset)
        
        self.btn_export = QPushButton("💾 Экспорт областей")
        self.btn_export.clicked.connect(self._export_regions)
        btn_layout.addWidget(self.btn_export)
        
        left_layout.addLayout(btn_layout)
        
        main_layout.addLayout(left_layout, stretch=2)
        
        # ===== ПРАВАЯ ЧАСТЬ: Информация =====
        right_layout = QVBoxLayout()
        
        # Статус
        status_group = QGroupBox("Статус")
        status_layout = QVBoxLayout(status_group)
        
        self.label_status = QLabel("Изображение не загружено")
        status_layout.addWidget(self.label_status)
        
        self.label_progress = QLabel("Области: 0/7")
        status_layout.addWidget(self.label_progress)
        
        right_layout.addWidget(status_group)
        
        # Список областей
        regions_group = QGroupBox("Выделенные области")
        regions_layout = QVBoxLayout(regions_group)
        
        self.table_regions = QTableWidget()
        self.table_regions.setColumnCount(4)
        self.table_regions.setHorizontalHeaderLabels(
            ["ID", "Область", "Размер", "Статус"]
        )
        self.table_regions.horizontalHeader().setStretchLastSection(True)
        regions_layout.addWidget(self.table_regions)
        
        right_layout.addWidget(regions_group)
        
        # Предпросмотр
        preview_group = QGroupBox("Предпросмотр последней области")
        preview_layout = QVBoxLayout(preview_group)
        
        self.label_preview = QLabel()
        self.label_preview.setMinimumSize(200, 100)
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setStyleSheet("background-color: #333;")
        preview_layout.addWidget(self.label_preview)
        
        right_layout.addWidget(preview_group)
        
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
            self, "Выберите изображение титульного листа", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            print(f"📁 Выбран файл: {file_path}")
            
            # 🔧 ПРОВЕРКА: какие форматы поддерживает Qt
            supported = QImageReader.supportedImageFormats()
            print(f"📋 Поддерживаемые форматы: {[f.data().decode() for f in supported]}")
            
            # 🔧 ПРОВЕРКА: существует ли файл
            if not os.path.exists(file_path):
                print(f"❌ Файл не существует: {file_path}")
                return
            
            self.image_widget.load_image(file_path)
    
    def _on_image_loaded(self, path: str):
        """Изображение загружено."""
        self.label_status.setText(f"Загружено: {os.path.basename(path)}")
        self.label_progress.setText("Области: 0/7")
        self._update_table()
    
    def _on_region_selected(self, region_id: int, rect: QRect):
        """Область выделена."""
        self.label_progress.setText(f"Области: {region_id + 1}/7")
        self._update_table()
        
        # Предпросмотр
        cropped = self.image_widget.get_region_image(region_id)
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
            "Теперь можно экспортировать их для OCR распознавания."
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
            self.table_regions.setItem(i, 3, QTableWidgetItem("✅"))
    
    def _reset_regions(self):
        """Сбросить все области."""
        self.image_widget.reset_regions()
        self.label_status.setText("Области сброшены")
        self.label_progress.setText("Области: 0/7")
        self.table_regions.setRowCount(0)
        self.label_preview.clear()
    
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
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = TestOcrWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_test()
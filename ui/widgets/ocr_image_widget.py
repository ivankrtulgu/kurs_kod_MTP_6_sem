# ui/widgets/ocr_image_widget.py

from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QImage
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
import os
import tempfile


class OcrRegion:
    """Класс одной области выделения."""
    
    COLORS = [
        (QColor(255, 0, 0), "Автор"),
        (QColor(0, 255, 0), "Название"),
        (QColor(0, 0, 255), "Издательство"),
        (QColor(255, 255, 0), "Год"),
        (QColor(255, 0, 255), "ISBN"),
        (QColor(0, 255, 255), "УДК"),
        (QColor(255, 165, 0), "ББК"),
    ]
    
    def __init__(self, rect: QRect, region_id: int):
        self.rect = rect
        self.id = region_id
        self.color, self.name = self.COLORS[region_id % len(self.COLORS)]
        self.enabled = True
    
    def draw(self, painter: QPainter):
        """Отрисовка области."""
        if not self.enabled:
            return
        
        brush = QBrush(QColor(self.color.red(), self.color.green(), 
                              self.color.blue(), 50))
        painter.setBrush(brush)
        
        pen = QPen(self.color, 2)
        painter.setPen(pen)
        
        painter.drawRect(self.rect)
        
        painter.setPen(QColor(255, 255, 255))
        painter.fillRect(self.rect.x(), self.rect.y() - 20, 
                        100, 20, QBrush(self.color))
        painter.drawText(self.rect.x(), self.rect.y() - 5, self.name)


class OcrImageWidget(QWidget):
    """Виджет для отображения изображения с 7 областями для OCR."""
    
    region_selected = pyqtSignal(int, QRect)
    region_completed = pyqtSignal(list)
    image_loaded = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pixmap = QPixmap()
        self.regions = []
        self.current_region_id = 0
        self.max_regions = 7
        
        self.is_selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.temp_rect = QRect()
        
        # 🔧 Храним путь к временному PNG
        self.temp_png_path = None
        
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setCursor(Qt.CrossCursor)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _convert_to_png(self, file_path: str) -> str:
        """
        🔧 Конвертировать изображение в PNG через Pillow.
        Возвращает путь к временному PNG файлу.
        """
        try:
            from PIL import Image
            
            # Открываем исходное изображение
            img = Image.open(file_path)
            
            # Конвертируем в RGB (если нужно)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Создаём временный файл
            temp_dir = tempfile.gettempdir()
            temp_filename = f"ocr_temp_{os.path.basename(file_path)}.png"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Сохраняем как PNG
            img.save(temp_path, 'PNG')
            
            print(f"✅ Конвертировано: {file_path} → {temp_path}")
            
            self.temp_png_path = temp_path
            return temp_path
            
        except Exception as e:
            print(f"❌ Ошибка конвертации: {e}")
            return None
    
    def load_image(self, file_path: str):
        """Загрузить изображение с авто-конвертацией в PNG."""
        
        print(f"\n📁 Загрузка: {file_path}")
        
        # 🔧 Очищаем предыдущий временный файл
        if self.temp_png_path and os.path.exists(self.temp_png_path):
            try:
                os.remove(self.temp_png_path)
            except:
                pass
            self.temp_png_path = None
        
        # 🔧 Проверяем формат
        ext = os.path.splitext(file_path)[1].lower()
        needs_conversion = ext in ['.jpg', '.jpeg']
        
        # 🔧 Если JPG/JPEG — конвертируем в PNG
        if needs_conversion:
            print("🔄 JPG обнаружен, конвертируем в PNG...")
            converted_path = self._convert_to_png(file_path)
            if converted_path:
                file_path = converted_path
            else:
                print("❌ Конвертация не удалась!")
                return
        
        # 🔧 Загружаем через QPixmap (теперь это точно PNG)
        self.pixmap = QPixmap(file_path)
        
        if self.pixmap.isNull():
            print("⚠️ QPixmap не загрузил, пробуем QImage...")
            image = QImage(file_path)
            if not image.isNull():
                self.pixmap = QPixmap.fromImage(image)
                print("✅ Загружено через QImage")
            else:
                print("❌ ОШИБКА: Не удалось загрузить изображение")
                return
        
        print(f"✅ Изображение загружено: {self.pixmap.width()}x{self.pixmap.height()}")
        
        self.setMaximumSize(self.pixmap.size())
        self.setMinimumSize(self.pixmap.size())
        self.resize(self.pixmap.size())
        
        self.regions = []
        self.current_region_id = 0
        self.update()
        self.image_loaded.emit(file_path)
    
    def reset_regions(self):
        self.regions = []
        self.current_region_id = 0
        self.update()
    
    def remove_last_region(self):
        if self.regions:
            self.regions.pop()
            self.current_region_id = max(0, self.current_region_id - 1)
            self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_region_id < self.max_regions:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_selecting = True
            self.temp_rect = QRect()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.temp_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()
            rect = QRect(self.start_point, self.end_point).normalized()
            
            if rect.width() > 20 and rect.height() > 20:
                region = OcrRegion(rect, self.current_region_id)
                self.regions.append(region)
                self.region_selected.emit(self.current_region_id, rect)
                self.current_region_id += 1
                
                if self.current_region_id >= self.max_regions:
                    self.region_completed.emit(self.regions)
            
            self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawPixmap(0, 0, self.pixmap)
            
            for region in self.regions:
                region.draw(painter)
            
            if self.is_selecting and not self.temp_rect.isEmpty():
                color = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][0]
                pen = QPen(color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 30)))
                painter.drawRect(self.temp_rect)
                
                name = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][1]
                painter.setPen(QColor(255, 255, 255))
                painter.fillRect(self.temp_rect.x(), self.temp_rect.y() - 20, 120, 20, QBrush(color))
                painter.drawText(self.temp_rect.x() + 5, self.temp_rect.y() - 5, 
                                f"{name} ({self.current_region_id + 1}/{self.max_regions})")
            
            self._draw_info_panel(painter)
    
    def _draw_info_panel(self, painter: QPainter):
        painter.setPen(QColor(255, 255, 255))
        painter.fillRect(10, 10, 200, 100, QBrush(QColor(0, 0, 0, 150)))
        
        y_offset = 25
        painter.drawText(20, y_offset, f"Области: {len(self.regions)}/{self.max_regions}")
        
        if self.current_region_id < self.max_regions:
            next_name = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][1]
            painter.drawText(20, y_offset + 20, f"Следующая: {next_name}")
        else:
            painter.drawText(20, y_offset + 20, "Готово!")
        
        painter.drawText(20, y_offset + 40, "ЛКМ - выделить область")
        painter.drawText(20, y_offset + 60, "ПКМ - меню")
    
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        
        reset_action = QAction("Сбросить все области", self)
        reset_action.triggered.connect(self.reset_regions)
        menu.addAction(reset_action)
        
        if self.regions:
            remove_action = QAction("Удалить последнюю", self)
            remove_action.triggered.connect(self.remove_last_region)
            menu.addAction(remove_action)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def get_region_image(self, region_id: int) -> QPixmap:
        if 0 <= region_id < len(self.regions):
            return self.pixmap.copy(self.regions[region_id].rect)
        return QPixmap()
    
    def get_all_regions_data(self) -> list:
        data = []
        for region in self.regions:
            data.append({
                'id': region.id,
                'name': region.name,
                'rect': region.rect,
                'color': region.color,
                'image': self.get_region_image(region.id)
            })
        return data
    
    def closeEvent(self, event):
        """🔧 Очистка временных файлов при закрытии."""
        if self.temp_png_path and os.path.exists(self.temp_png_path):
            try:
                os.remove(self.temp_png_path)
                print(f"🗑 Удалён временный файл: {self.temp_png_path}")
            except:
                pass
        super().closeEvent(event)
# ui/widgets/ocr_image_widget.py
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal


class OcrRegion:
    """Класс одной области выделения."""
    
    COLORS = [
        (QColor(255, 0, 0), "Автор"),           # Красный
        (QColor(0, 255, 0), "Название"),        # Зелёный
        (QColor(0, 0, 255), "Издательство"),    # Синий
        (QColor(255, 255, 0), "Год"),           # Жёлтый
        (QColor(255, 0, 255), "ISBN"),          # Пурпурный
        (QColor(0, 255, 255), "УДК"),           # Голубой
        (QColor(255, 165, 0), "ББК"),           # Оранжевый
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
        
        # Полупрозрачная заливка
        brush = QBrush(QColor(self.color.red(), self.color.green(), 
                              self.color.blue(), 50))
        painter.setBrush(brush)
        
        # Рамка
        pen = QPen(self.color, 2)
        painter.setPen(pen)
        
        painter.drawRect(self.rect)
        
        # Подпись
        painter.setPen(QColor(255, 255, 255))
        painter.fillRect(self.rect.x(), self.rect.y() - 20, 
                        100, 20, QBrush(self.color))
        painter.drawText(self.rect.x(), self.rect.y() - 5, self.name)


class OcrImageWidget(QWidget):
    """
    Виджет для отображения изображения с 7 областями для OCR.
    """
    
    # Сигналы
    region_selected = pyqtSignal(int, QRect)      # (id области, прямоугольник)
    region_completed = pyqtSignal(list)           # Все области выделены
    image_loaded = pyqtSignal(str)                # Путь к изображению
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pixmap = QPixmap()
        self.regions: list[OcrRegion] = []
        self.current_region_id = 0
        self.max_regions = 7
        
        # Для выделения
        self.is_selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.temp_rect = QRect()
        
        # Настройки
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setCursor(Qt.CrossCursor)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def load_image(self, file_path: str):
        """Загрузить изображение."""
        self.pixmap = QPixmap(file_path)
        
        # 🔧 ПРОВЕРКА: загрузилось ли изображение
        if self.pixmap.isNull():
            print(f"❌ ОШИБКА: Не удалось загрузить изображение: {file_path}")
            return
        
        print(f"✅ Изображение загружено: {file_path}")
        print(f"   Размер: {self.pixmap.width()}x{self.pixmap.height()}")
        
        # 🔧 РЕСАЙЗ ВИДЖЕТА ПОД ИЗОБРАЖЕНИЕ
        self.setMaximumSize(self.pixmap.size())
        self.setMinimumSize(self.pixmap.size())
        self.resize(self.pixmap.size())
        
        self.regions = []
        self.current_region_id = 0
        self.update()
        self.image_loaded.emit(file_path)
    
    def reset_regions(self):
        """Сбросить все выделенные области."""
        self.regions = []
        self.current_region_id = 0
        self.update()
    
    def remove_last_region(self):
        """Удалить последнюю область."""
        if self.regions:
            self.regions.pop()
            self.current_region_id = max(0, self.current_region_id - 1)
            self.update()
    
    def mousePressEvent(self, event):
        """Начало выделения."""
        if event.button() == Qt.LeftButton and self.current_region_id < self.max_regions:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_selecting = True
            self.temp_rect = QRect()
    
    def mouseMoveEvent(self, event):
        """Процесс выделения."""
        if self.is_selecting:
            self.end_point = event.pos()
            self.temp_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Конец выделения."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_point = event.pos()
            rect = QRect(self.start_point, self.end_point).normalized()
            
            # Минимальный размер области
            if rect.width() > 20 and rect.height() > 20:
                region = OcrRegion(rect, self.current_region_id)
                self.regions.append(region)
                
                # Отправляем сигнал
                self.region_selected.emit(self.current_region_id, rect)
                
                # Переход к следующей области
                self.current_region_id += 1
                
                # Проверка завершения
                if self.current_region_id >= self.max_regions:
                    self.region_completed.emit(self.regions)
            
            self.update()
    
    def paintEvent(self, event):
        """Отрисовка изображения и областей."""
        super().paintEvent(event)
        
        if not self.pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Рисуем изображение
            painter.drawPixmap(0, 0, self.pixmap)
            
            # Рисуем выделенные области
            for region in self.regions:
                region.draw(painter)
            
            # Рисуем текущую выделяемую область
            if self.is_selecting and not self.temp_rect.isEmpty():
                color = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][0]
                pen = QPen(color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(color.red(), color.green(), 
                                               color.blue(), 30)))
                painter.drawRect(self.temp_rect)
                
                # Подпись текущей области
                name = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][1]
                painter.setPen(QColor(255, 255, 255))
                painter.fillRect(self.temp_rect.x(), self.temp_rect.y() - 20, 
                                120, 20, QBrush(color))
                painter.drawText(self.temp_rect.x() + 5, self.temp_rect.y() - 5, 
                                f"{name} ({self.current_region_id + 1}/{self.max_regions})")
            
            # Инфо-панель
            self._draw_info_panel(painter)
    
    def _draw_info_panel(self, painter: QPainter):
        """Отрисовка информационной панели."""
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
        """Контекстное меню."""
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
        """Получить изображение конкретной области."""
        if 0 <= region_id < len(self.regions):
            return self.pixmap.copy(self.regions[region_id].rect)
        return QPixmap()
    
    def get_all_regions_data(self) -> list[dict]:
        """Получить данные всех областей."""
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
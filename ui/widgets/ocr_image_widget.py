# ui/widgets/ocr_image_widget.py

from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QImage
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QBuffer, QByteArray
import os
import tempfile


class OcrRegion:
    """Класс одной области выделения."""

    COLORS = [
        (QColor(255, 0, 0), "Автор"),
        (QColor(0, 255, 0), "Название"),
        (QColor(0, 255, 255), "Место издания"),
        (QColor(0, 0, 255), "Издательство"),
        (QColor(255, 255, 0), "Год"),
        (QColor(255, 0, 255), "ISBN"),
        (QColor(0, 255, 255), "УДК"),
        (QColor(255, 165, 0), "ББК"),
        (QColor(128, 0, 128), "Аннотация"),
        (QColor(0, 128, 0), "Авторский знак"),
    ]

    def __init__(self, rect: QRect, region_id: int):
        self.rect = rect  #  Координаты ОТНОСИТЕЛЬНО source_pixmap (оригинала)
        self.id = region_id
        self.color, self.name = self.COLORS[region_id % len(self.COLORS)]
        self.enabled = True
        self.ocr_text = ""

    def draw(self, painter: QPainter, offset_x: int, offset_y: int, scale_x: float, scale_y: float):
        """ Отрисовка с масштабированием."""
        if not self.enabled:
            return

        #  Масштабируем координаты для отображения
        scaled_rect = QRect(
            int(self.rect.x() * scale_x) + offset_x,
            int(self.rect.y() * scale_y) + offset_y,
            int(self.rect.width() * scale_x),
            int(self.rect.height() * scale_y)
        )

        # Полупрозрачная заливка
        brush = QBrush(QColor(self.color.red(), self.color.green(),
                              self.color.blue(), 50))
        painter.setBrush(brush)

        # Рамка
        pen = QPen(self.color, 2)
        painter.setPen(pen)

        painter.drawRect(scaled_rect)

        # Подпись
        painter.setPen(QColor(255, 255, 255))
        painter.fillRect(scaled_rect.x(), scaled_rect.y() - 20,
                        100, 20, QBrush(self.color))
        painter.drawText(scaled_rect.x(), scaled_rect.y() - 5, self.name)


class OcrImageWidget(QWidget):
    """Виджет для отображения изображения с 7 областями для OCR."""

    region_selected = pyqtSignal(int, QRect)
    region_completed = pyqtSignal(list)
    image_loaded = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()

        #  ТРИ УРОВНЯ PIXMAP
        self.source_pixmap = QPixmap()      # Оригинальное изображение
        self.adjusted_pixmap = QPixmap()    # С яркостью/контрастом
        self.display_pixmap = QPixmap()     # Масштабированное для отображения

        #  КЭШИРОВАНИЕ для оптимизации
        self._source_image = None  # PIL Image оригинал
        self._last_brightness = 0
        self._last_contrast = 0

        self.regions = []
        self.current_region_id = 0
        self.max_regions = 10

        self.is_selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.temp_rect = QRect()

        #  Коэффициенты масштабирования
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0

        #  Текущие настройки
        self.brightness_value = 0
        self.contrast_value = 0
        self.zoom_factor = 1.0
        
        self.temp_png_path = None

        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setCursor(Qt.CrossCursor)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _convert_to_png(self, file_path: str) -> str:
        """Конвертировать изображение в PNG через Pillow."""
        try:
            from PIL import Image
            
            img = Image.open(file_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            temp_dir = tempfile.gettempdir()
            temp_filename = f"ocr_temp_{os.path.basename(file_path)}.png"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            img.save(temp_path, 'PNG')
            
            print(f" Конвертировано: {file_path} → {temp_path}")
            
            self.temp_png_path = temp_path
            return temp_path
            
        except Exception as e:
            print(f" Ошибка конвертации: {e}")
            return None
    
    def load_image(self, file_path: str):
        """Загрузить изображение с авто-конвертацией в PNG."""
        
        print(f"\n Загрузка: {file_path}")
        
        if self.temp_png_path and os.path.exists(self.temp_png_path):
            try:
                os.remove(self.temp_png_path)
            except:
                pass
            self.temp_png_path = None
        
        ext = os.path.splitext(file_path)[1].lower()
        needs_conversion = ext in ['.jpg', '.jpeg']
        
        if needs_conversion:
            print(" JPG обнаружен, конвертируем в PNG...")
            converted_path = self._convert_to_png(file_path)
            if converted_path:
                file_path = converted_path
            else:
                print(" Конвертация не удалась!")
                return
        
        #  Загружаем в source_pixmap (оригинал)
        self.source_pixmap = QPixmap(file_path)
        
        if self.source_pixmap.isNull():
            print(" QPixmap не загрузил, пробуем QImage...")
            image = QImage(file_path)
            if not image.isNull():
                self.source_pixmap = QPixmap.fromImage(image)
                print(" Загружено через QImage")
            else:
                print(" ОШИБКА: Не удалось загрузить изображение")
                return
        
        print(f" Изображение загружено: {self.source_pixmap.width()}x{self.source_pixmap.height()}")
        
        #  Сбрасываем настройки
        self.brightness_value = 0
        self.contrast_value = 0
        
        #  Применяем настройки (создаст adjusted_pixmap)
        self._apply_adjustments_to_pixmap()
        
        self.regions = []
        self.current_region_id = 0
        
        #  Обновляем отображение (создаст display_pixmap и коэффициенты)
        self._update_display_pixmap()
        
        self.image_loaded.emit(file_path)
    
    def _apply_adjustments_to_pixmap(self, silent: bool = False):
        """
        Применить яркость/контраст к source_pixmap → adjusted_pixmap.
        
        Args:
            silent: Если True — не выводить сообщения в консоль
        """
        if self.source_pixmap.isNull():
            return

        try:
            from PIL import Image, ImageEnhance
            import io

            #  Используем кэшированное PIL Image или создаём новое
            if self._source_image is None:
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QBuffer.WriteOnly)
                self.source_pixmap.save(buffer, 'PNG')
                buffer.close()
                self._source_image = Image.open(io.BytesIO(byte_array.data()))

            img = self._source_image

            # Применяем яркость
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.0 + self.brightness_value / 100.0)

            # Применяем контраст
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.0 + self.contrast_value / 100.0)

            # Конвертируем обратно в QPixmap
            buffer_out = io.BytesIO()
            img.save(buffer_out, 'PNG')
            buffer_out.seek(0)

            self.adjusted_pixmap = QPixmap()
            self.adjusted_pixmap.loadFromData(buffer_out.read())

            # if not silent:
                # print(f" Настройки применены: яркость={self.brightness_value}, контраст={self.contrast_value}")

        except Exception as e:
            if not silent:
                print(f" Ошибка применения настроек: {e}")
                import traceback
                traceback.print_exc()
    
    def _update_display_pixmap(self):
        """Обновить отображаемый pixmap с учётом коэффициента масштабирования."""
        if self.adjusted_pixmap.isNull():
            return
        
        # Рассчитываем целевой размер на основе zoom_factor
        target_width = int(self.source_pixmap.width() * self.zoom_factor)
        target_height = int(self.source_pixmap.height() * self.zoom_factor)
        
        scaled_pixmap = self.adjusted_pixmap.scaled(
            target_width, 
            target_height, 
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.display_pixmap = scaled_pixmap
        
        # Обновляем размер виджета, чтобы QScrollArea правильно работала
        self.setFixedSize(self.display_pixmap.width(), self.display_pixmap.height())
        
        # Вычисляем коэффициенты масштабирования (ОТ source к display)
        if not self.source_pixmap.isNull() and self.source_pixmap.width() > 0:
            self.scale_factor_x = self.display_pixmap.width() / self.source_pixmap.width()
            self.scale_factor_y = self.display_pixmap.height() / self.source_pixmap.height()
        else:
            self.scale_factor_x = 1.0
            self.scale_factor_y = 1.0
        
        # Вычисляем offset (теперь он всегда 0, так как виджет равен размеру картинки)
        self.image_offset_x = 0
        self.image_offset_y = 0
        
        self.update()
    
    def apply_image_adjustments(self, brightness: int, contrast: int):
        """Применить настройки яркости и контраста."""
        self.brightness_value = brightness
        self.contrast_value = contrast
        self._apply_adjustments_to_pixmap()
        self._update_display_pixmap()
    
    def reset_image_settings(self):
        """Сбросить настройки к оригиналу."""
        self.brightness_value = 0
        self.contrast_value = 0
        self._apply_adjustments_to_pixmap()
        self._update_display_pixmap()
    
    def reset_regions(self):
        self.regions = []
        self.current_region_id = 0
        self.update()
    
    def remove_last_region(self):
        if self.regions:
            self.regions.pop()
            self.current_region_id = max(0, self.current_region_id - 1)
            self.update()
    
    def _screen_to_source(self, pos: QPoint) -> QPoint:
        """ Конвертировать координаты экрана в координаты source_pixmap."""
        # Вычитаем offset изображения
        x = pos.x() - self.image_offset_x
        y = pos.y() - self.image_offset_y
        
        # Делим на коэффициент масштабирования
        src_x = int(x / self.scale_factor_x) if self.scale_factor_x > 0 else x
        src_y = int(y / self.scale_factor_y) if self.scale_factor_y > 0 else y
        
        return QPoint(src_x, src_y)
    
    def wheelEvent(self, event):
        """Обработка колесика мыши для зума (Ctrl + Wheel)."""
        if event.modifiers() & Qt.ControlModifier:
            # Изменяем zoom_factor
            if event.angleDelta().y() > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor /= 1.1
            
            # Ограничиваем зум (от 10% до 500%)
            self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
            
            self._update_display_pixmap()
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        """ Начало выделения — конвертируем в координаты source."""
        if event.button() == Qt.LeftButton and self.current_region_id < self.max_regions:
            #  Конвертируем в координаты оригинального изображения
            source_pos = self._screen_to_source(event.pos())
            self.start_point = source_pos
            self.end_point = source_pos
            self.is_selecting = True
            self.temp_rect = QRect()
    
    def mouseMoveEvent(self, event):
        """ Процесс выделения — конвертируем в координаты source."""
        if self.is_selecting:
            #  Конвертируем в координаты оригинального изображения
            source_pos = self._screen_to_source(event.pos())
            self.end_point = source_pos
            self.temp_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """ Конец выделения — сохраняем в координатах source."""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            source_pos = self._screen_to_source(event.pos())
            self.end_point = source_pos
            rect = QRect(self.start_point, self.end_point).normalized()
            
            # Минимальный размер области (в координатах source)
            if rect.width() > 5 and rect.height() > 5:
                region = OcrRegion(rect, self.current_region_id)
                self.regions.append(region)
                self.region_selected.emit(self.current_region_id, rect)
                self.current_region_id += 1
                
                if self.current_region_id >= self.max_regions:
                    self.region_completed.emit(self.regions)
            
            self.update()
    
    def paintEvent(self, event):
        """Отрисовка изображения и областей."""
        super().paintEvent(event)
        
        if not self.display_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            #  Рисуем изображение по центру
            painter.drawPixmap(self.image_offset_x, self.image_offset_y, self.display_pixmap)
            
            #  Рисуем выделенные области (с масштабированием)
            for region in self.regions:
                region.draw(painter, self.image_offset_x, self.image_offset_y, 
                           self.scale_factor_x, self.scale_factor_y)
            
            #  Рисуем текущую выделяемую область
            if self.is_selecting and not self.temp_rect.isEmpty():
                # Масштабируем временный прямоугольник для отображения
                display_rect = QRect(
                    int(self.temp_rect.x() * self.scale_factor_x) + self.image_offset_x,
                    int(self.temp_rect.y() * self.scale_factor_y) + self.image_offset_y,
                    int(self.temp_rect.width() * self.scale_factor_x),
                    int(self.temp_rect.height() * self.scale_factor_y)
                )
                
                color = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][0]
                pen = QPen(color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 30)))
                painter.drawRect(display_rect)
                
                name = OcrRegion.COLORS[self.current_region_id % len(OcrRegion.COLORS)][1]
                painter.setPen(QColor(255, 255, 255))
                painter.fillRect(display_rect.x(), display_rect.y() - 20, 120, 20, QBrush(color))
                painter.drawText(display_rect.x() + 5, display_rect.y() - 5, 
                                f"{name} ({self.current_region_id + 1}/{self.max_regions})")
            
            self._draw_info_panel(painter)
    
    def resizeEvent(self, event):
        """При изменении размера виджета обновляем отображение."""
        super().resizeEvent(event)
        self._update_display_pixmap()
    
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
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px 8px 20px;
                background-color: transparent;
                color: #2d3748;
            }
            QMenu::item:selected {
                background-color: #f0fff4;
                color: #68a385;
            }
        """)
        
        reset_action = QAction("Сбросить все области", self)
        reset_action.triggered.connect(self.reset_regions)
        menu.addAction(reset_action)
        
        reset_settings_action = QAction(" Сбросить настройки изображения", self)
        reset_settings_action.triggered.connect(self.reset_image_settings)
        menu.addAction(reset_settings_action)
        
        if self.regions:
            remove_action = QAction("Удалить последнюю", self)
            remove_action.triggered.connect(self.remove_last_region)
            menu.addAction(remove_action)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def get_region_image(self, region_id: int, use_adjusted: bool = False) -> QPixmap:
        """
         Получить изображение области.
        
        Args:
            region_id: ID области
            use_adjusted: Если True — использовать adjusted_pixmap (с яркостью/контрастом),
                         иначе — source_pixmap (оригинал)
        """
        if 0 <= region_id < len(self.regions):
            rect = self.regions[region_id].rect
            
            #  Используем обработанное изображение если запрошено
            if use_adjusted and not self.adjusted_pixmap.isNull():
                return self.adjusted_pixmap.copy(rect)
            else:
                return self.source_pixmap.copy(rect)
        
        return QPixmap()
    
    def recognize_text(self, pixmap: QPixmap, lang: str = 'auto') -> str:
        """
        Распознать текст на изображении через Tesseract.
        
        Args:
            pixmap: Изображение для распознавания
            lang: Язык распознавания:
                  - 'rus' — только русский
                  - 'eng' — только английский
                  - 'rus+eng' — русский + английский (смешанный)
                  - 'eng+rus' — английский + русский (приоритет английский)
                  - 'digits' — только цифры и базовые символы
        """
        try:
            import pytesseract
            from PIL import Image
            import io

            #  Указываем путь к Tesseract
            pytesseract.pytesseract.tesseract_cmd = r'd:\Main_programms\Tesseract\Tesseract-OCR\tesseract.exe'

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            pixmap.save(buffer, 'PNG')
            buffer.close()

            img = Image.open(io.BytesIO(byte_array.data()))

            #  Определяем язык и конфиг в зависимости от режима
            lang_map = {
                'rus': ('rus', r'--oem 3 --psm 6'),
                'eng': ('eng', r'--oem 3 --psm 6'),
                'rus+eng': ('rus+eng', r'--oem 3 --psm 6'),
                'eng+rus': ('eng+rus', r'--oem 3 --psm 6'),
                'digits': ('eng', r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,-:;()/'),
                'auto': ('rus+eng', r'--oem 3 --psm 6'),  # по умолчанию
            }
            
            ocr_lang, config = lang_map.get(lang, ('rus+eng', r'--oem 3 --psm 6'))
            text = pytesseract.image_to_string(img, lang=ocr_lang, config=config)

            return text.strip()

        except Exception as e:
            print(f" OCR ошибка: {e}")
            return f"(OCR ошибка: {str(e)})"
    
    def get_all_regions_data(self) -> list:
        data = []
        for region in self.regions:
            data.append({
                'id': region.id,
                'name': region.name,
                'rect': region.rect,
                'color': region.color,
                'image': self.get_region_image(region.id),
                'ocr_text': region.ocr_text
            })
        return data
    
    def closeEvent(self, event):
        """Очистка временных файлов при закрытии."""
        if self.temp_png_path and os.path.exists(self.temp_png_path):
            try:
                os.remove(self.temp_png_path)
                print(f"🗑 Удалён временный файл: {self.temp_png_path}")
            except:
                pass
        super().closeEvent(event)
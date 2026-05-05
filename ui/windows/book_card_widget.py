# ui/windows/book_card_widget.py
"""Book card widget with repository integration."""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout, QGroupBox, QMdiSubWindow,
    QRadioButton, QSpinBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from pathlib import Path
from ui.generated.ui_book_card_widget import Ui_BookCardWidget

from core.services.book_service import BookService
from core.services.inventory_service import InventoryService
from core.services.printing_service import PrintingService
from core.services.qr_service import QRService
from core.models.book import Book
from ui.windows.add_book_dialog import AddBookDialog
from ui.style_manager import StyleManager
from ui.icon_manager import IconManager


class BookPrintSettingsWidget(QWidget):
    """Widget for configuring QR print settings for a Book with a live preview."""
    def __init__(self, parent_widget, book_service: BookService, inventory_service: InventoryService, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self._book_service = book_service
        self._inventory_service = inventory_service
        
        self.setWindowTitle("Настройки печати QR (Произведение)")
        self.setMinimumSize(700, 400)
        
        main_layout = QHBoxLayout(self)
        
        # --- Left Side: Settings ---
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        
        # Mode Selection
        mode_group = QGroupBox("Режим печати")
        mode_layout = QVBoxLayout(mode_group)
        self.rb_book_only = QRadioButton("Только произведение")
        self.rb_book_only.setChecked(True)
        self.rb_book_only.toggled.connect(self.update_preview)
        self.rb_items_only = QRadioButton("Все экземпляры")
        self.rb_items_only.toggled.connect(self.update_preview)
        self.rb_both = QRadioButton("Экземпляры + Произведение (попарно)")
        self.rb_both.toggled.connect(self.update_preview)
        mode_layout.addWidget(self.rb_book_only)
        mode_layout.addWidget(self.rb_items_only)
        mode_layout.addWidget(self.rb_both)
        settings_layout.addWidget(mode_group)
        
        # Column Selection
        col_group = QGroupBox("Сетка")
        col_layout = QFormLayout(col_group)
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 10)
        self.spin_cols.setValue(3)
        self.spin_cols.valueChanged.connect(self.update_preview)
        col_layout.addRow("Кол-во столбцов:", self.spin_cols)
        settings_layout.addWidget(col_group)
        
        settings_layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_print = QPushButton("Печатать")
        self.btn_print.clicked.connect(self._on_print)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_print)
        btn_layout.addWidget(self.btn_close)
        settings_layout.addLayout(btn_layout)
        
        main_layout.addWidget(settings_container, 1)
        
        # --- Right Side: Preview ---
        preview_group = QGroupBox("Предпросмотр листа (A4)")
        preview_main_layout = QVBoxLayout(preview_group)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.preview_page = QFrame()
        self.preview_page.setFixedSize(400, 565) # Proportional A4 (210:297)
        self.preview_page.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
        # Layout for elements on the "page"
        self.page_layout = QGridLayout(self.preview_page)
        self.page_layout.setContentsMargins(20, 20, 20, 20)
        self.page_layout.setSpacing(0)
        
        self.scroll_area.setWidget(self.preview_page)
        preview_main_layout.addWidget(self.scroll_area)
        
        main_layout.addWidget(preview_group, 2)
        
        self.update_preview()

    def update_preview(self):
        """Updates the mock-up preview of the PDF page."""
        while self.page_layout.count():
            item = self.page_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        cols = self.spin_cols.value()
        mode = "book_only" if self.rb_book_only.isChecked() else ("items_only" if self.rb_items_only.isChecked() else "both")
        usable_w = 360
        cell_w = usable_w / cols
        
        def create_mock_cell(text):
            cell = QFrame()
            cell.setFixedSize(int(cell_w), 50)
            cell.setStyleSheet("border: 1px solid #aaa; background-color: #f9f9f9;")
            
            layout = QVBoxLayout(cell)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(2)
            
            qr_mock = QFrame()
            qr_mock.setFixedSize(int(cell_w * 0.6), int(cell_w * 0.6))
            qr_mock.setStyleSheet("background-color: #ddd; border: 1px solid #bbb;")
            layout.addWidget(qr_mock, 0, Qt.AlignCenter)
            
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedWidth(int(cell_w))
            lbl.setStyleSheet("font-size: 8pt; color: #666;")
            layout.addWidget(lbl, 0, Qt.AlignCenter)
            
            return cell

        if mode == "book_only":
            self.page_layout.addWidget(create_mock_cell("Произведение"), 0, 0)
        elif mode == "items_only":
            for r in range(2):
                for c in range(cols):
                    self.page_layout.addWidget(create_mock_cell(f"Экз. #{r*cols+c+1}"), r, c)
        else:  # both
            for r in range(2):
                for c in range(cols):
                    pair_container = QWidget()
                    pair_layout = QVBoxLayout(pair_container)
                    pair_layout.setContentsMargins(0,0,0,0)
                    pair_layout.setSpacing(0)
                    
                    cell_item = create_mock_cell(f"Экз. #{r*cols+c+1}")
                    cell_book = create_mock_cell("ISBN: ...")
                    
                    pair_layout.addWidget(cell_item)
                    pair_layout.addWidget(cell_book)
                    pair_container.setStyleSheet("border: 1px solid #aaa; background-color: #f9f9f9;")
                    self.page_layout.addWidget(pair_container, r, c)

    def _on_print(self):
        """Triggers the printing process in the parent widget."""
        settings = {
            "mode": "book_only" if self.rb_book_only.isChecked() else ("items_only" if self.rb_items_only.isChecked() else "both"),
            "cols": self.spin_cols.value()
        }
        self.parent_widget._execute_print_qr(settings)
        
        # Close only the MDI subwindow containing this widget
        parent = self.parent()
        while parent:
            if isinstance(parent, QMdiSubWindow):
                parent.close()
                break
            parent = parent.parent()

    def get_settings(self):
        return {
            "mode": "book_only" if self.rb_book_only.isChecked() else ("items_only" if self.rb_items_only.isChecked() else "both"),
            "cols": self.spin_cols.value()
        }


class BookCardWidget(QWidget, Ui_BookCardWidget):
    """Виджет карточки книги с интеграцией репозитория."""
    WINDOW_TITLE = "Карточка книги"

    def __init__(
        self,
        book_id: int = 0,
        parent=None,
        book_service: BookService | None = None,
        inventory_service: InventoryService | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        self.setWindowIcon(IconManager.get_default_icon())
        
        # Update layouts
        if hasattr(self, 'verticalLayout'):
            self.verticalLayout.setSpacing(10)
            self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        if hasattr(self, 'horizontalLayout_header'):
            self.horizontalLayout_header.setSpacing(10)
        if hasattr(self, 'horizontalLayout_actions'):
            self.horizontalLayout_actions.setSpacing(10)
        
        # Inject service
        self._book_service = book_service or BookService()
        self._inventory_service = inventory_service
        
        # Store book data
        self._book: Book | None = None
        self._book_id = book_id
        
        self._setup_print_button()
        self._connect_signals()
        
        # Load book data
        if book_id:
            self._load_book(book_id)

    def _setup_print_button(self):
        """Setup the Print QR button dynamically."""
        self.btn_print_qr = QPushButton("Печать QR")
        self.btn_print_qr.setMinimumHeight(40)
        if hasattr(self, 'horizontalLayout_actions'):
            self.horizontalLayout_actions.addWidget(self.btn_print_qr)

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_qr.clicked.connect(self._on_qr)
        if hasattr(self, 'btn_print_qr'):
            self.btn_print_qr.clicked.connect(self._on_print_qr)

    def _load_book(self, book_id: int):
        """Load book data from repository."""
        try:
            self._book = self._book_service.get_book(book_id)
            
            if not self._book:
                QMessageBox.warning(self, "Ошибка", f"Книга с ID {book_id} не найдена")
                return
            
            self._display_book(self._book)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить книгу: {e}")

    def _display_book(self, book: Book):
        """Display book data in widget."""
        # Main info
        self.label_author_value.setText(book.author)
        self.label_title_value.setText(book.title)
        self.label_year_value.setText(str(book.year))
        self.label_isbn_value.setText(book.isbn)
        self.label_udc_value.setText(book.udc or "—")
        self.label_bbk_value.setText(book.bbk or "—")
        
        # Display images
        self._load_image_to_label(book.cover_image_path, self.label_cover, "Обложка не найдена", "Нет обложки")
        self._load_image_to_label(book.qr_code_path, self.label_qr, "QR-код не найден", "QR-код не сгенерирован")
        
        # Bibliographic record
        biblio = book.format_bibliographic_record()
        self.text_biblio_record.setPlainText(biblio)
        
        # Additional info in group box
        additional_info = []
        if book.place:
            additional_info.append(f"Место издания: {book.place}")
        if book.publisher:
            additional_info.append(f"Издательство: {book.publisher}")
        if book.pages:
            additional_info.append(f"Страниц: {book.pages}")
        if book.edition:
            additional_info.append(f"Издание: {book.edition}")
        if book.annotation:
            additional_info.append(f"Аннотация: {book.annotation}")
        if book.doi:
            additional_info.append(f"DOI: {book.doi}")
        
        if additional_info:
            self.groupBox_additional.setTitle("Дополнительная информация")
            self.label_udc_value.setText(book.udc or "—")
            self.label_bbk_value.setText(book.bbk or "—")

    def _load_image_to_label(self, image_path: str | None, label, not_found_text: str, no_path_text: str):
        """Helper to load an image into a QLabel using Pillow."""
        if not image_path:
            label.setText(no_path_text)
            return

        path = Path(image_path)
        if not (path.exists() and path.is_file()):
            label.setText(not_found_text)
            return

        try:
            from PIL import Image
            with Image.open(path) as img:
                img = img.convert("RGBA")
                data = img.tobytes("raw", "RGBA")
                qimg = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                
                label_size = label.size()
                if not label_size.isEmpty():
                    scaled_pixmap = pixmap.scaled(
                        label_size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    label.setPixmap(scaled_pixmap)
                    label.setText("")
                else:
                    label.setText("Ошибка размера\nвиджета")
        except ImportError:
            label.setText("Установите\nPillow")
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            label.setText("Ошибка загрузки\nфайла")

    def get_book_title(self) -> str:
        """Get book title for window title."""
        if self._book:
            return self._book.title
        return "Карточка книги"

    def _on_edit(self):
        """Open edit dialog for current book."""
        try:
            if not self._book:
                QMessageBox.warning(self, "Редактирование", "Книга не загружена")
                return
             
            # Open add book dialog in edit mode with current book ID
            dialog = AddBookDialog(
                book_service=self._book_service, 
                parent=self,
                book_id=self._book.id
            )
             
            if dialog.exec_() == AddBookDialog.Accepted:
                # Refresh book data
                self._load_book(self._book_id)
                 
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактирование: {e}")

    def _on_delete(self):
        """Delete current book."""
        try:
            if not self._book:
                QMessageBox.warning(self, "Удаление", "Книга не загружена")
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Вы действительно хотите удалить книгу:\n\n"
                f"{self._book.author}. {self._book.title} ({self._book.year})\n\n"
                f"Это действие нельзя отменить.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self._book_service.delete_book(self._book_id)
                if success:
                    QMessageBox.information(
                        self, "Удалено",
                        f"Книга '{self._book.title}' успешно удалена"
                    )
                    # Close parent window if exists
                    parent = self.parent()
                    if parent:
                        parent.close()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить книгу")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка удаления: {e}")

    def _on_export(self):
        """Export book bibliographic record."""
        try:
            if not self._book:
                QMessageBox.warning(self, "Экспорт", "Книга не загружена")
                return
            
            # Save to file
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Экспорт библиографической записи",
                f"{self._book.author}_{self._book.year}.txt",
                "Text files (*.txt);;All files (*)"
            )
            
            if file_path:
                biblio = self._book.format_bibliographic_record()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(biblio)
                QMessageBox.information(
                    self, "Экспорт",
                    f"Библиографическая запись экспортирована:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {e}")

    def _on_qr(self):
        """Generate QR code for book."""
        try:
            if not self._book:
                QMessageBox.warning(self, "QR-код", "Книга не загружена")
                return
            
            # Generate QR code using qrcode library
            import qrcode
            from config.settings import settings
            
            settings.ensure_dirs()
            
            # Create QR code with data in JSON format
            import json
            qr_dict = {
                "isbn": self._book.isbn,
                "doi": self._book.doi,
                "biblio": self._book.format_bibliographic_record()
            }
            qr_data = json.dumps(qr_dict, ensure_ascii=False)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_dir = settings.RESOURCES_PATH / "qr_codes"
            qr_dir.mkdir(parents=True, exist_ok=True)
            
            # Unique filename: id + isbn + random salt
            import secrets
            import string
            random_salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            
            filename = f"qr_{self._book.id}_{self._book.isbn}_{random_salt}.png"
            qr_path = qr_dir / filename
            img.save(qr_path)
            
            QMessageBox.information(
                self, "QR-код",
                f"QR-код сгенерирован и сохранен:\n{qr_path}"
            )
            
            # Update book record with QR path
            self._book.qr_code_path = str(qr_path)
            self._book_service.update_book(self._book)
            
        except ImportError:
            QMessageBox.warning(
                self, "QR-код",
                "Библиотека qrcode не установлена.\n"
                "Установите: pip install qrcode[pil]"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации QR: {e}")

    def _on_print_qr(self):
        """Handle QR printing process for the book."""
        if not self._book:
            return
            
        try:
            # Open Print Settings as MDI Window
            print_widget = self._main_window._open_book_print_settings(
                self._book_id, 
                self._book_service, 
                self._inventory_service, 
                self
            )
            
            # Establish dependency: close print window when card closes
            self._main_window.add_close_dependency(self, print_widget)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии настроек печати: {e}")

    def _execute_print_qr(self, settings_data):
        """The actual printing logic called from the settings widget."""
        try:
            mode = settings_data["mode"]
            cols = settings_data["cols"]
            
            if not self._book:
                QMessageBox.warning(self, "Ошибка", "Книга не загружена")
                return

            from config.settings import settings
            settings.ensure_dirs()
            
            print_dir = settings.RESOURCES_PATH / "printed_qrs"
            print_dir.mkdir(parents=True, exist_ok=True)
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qr_book_print_{self._book.id}_{timestamp}.pdf"
            output_path = str(print_dir / filename)

            # Prepare Book QR
            book_qr_path = None
            book_label = None
            
            # If mode needs book QR
            if mode in ["book_only", "both"]:
                if not self._book.qr_code_path:
                    reply = QMessageBox.question(
                        self, "QR-код произведения",
                        "QR-код произведения не найден. Сгенерировать его сейчас?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        generated_path = QRService.generate_book_qr(self._book)
                        if generated_path:
                            self._book.qr_code_path = generated_path
                            self._book_service.update_book(self._book)
                            book_qr_path = generated_path
                            book_label = f"ISBN: {self._book.isbn}" if self._book.isbn else "Произведение"
                        else:
                            QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать QR-код произведения")
                            return
                    else:
                        if mode == "book_only":
                            return # User canceled and mode requires book
                else:
                    book_qr_path = self._book.qr_code_path
                    book_label = f"ISBN: {self._book.isbn}" if self._book.isbn else "Произведение"

            if mode == "book_only":
                success = PrintingService.generate_qr_pdf(
                    item_qr_path=book_qr_path,
                    item_label=book_label,
                    output_path=output_path,
                    cols=cols
                )
            else:
                # Get all items
                items = self._inventory_service.get_items_by_book(self._book.id)
                if not items:
                    QMessageBox.warning(self, "Предупреждение", "Нет экземпляров для печати")
                    return

                items_data = []
                for item in items:
                    if not item.qr_code_path:
                        # Generate item QR on the fly
                        generated_item_qr = QRService.generate_item_qr(item, self._book.isbn)
                        if generated_item_qr:
                            item.qr_code_path = generated_item_qr
                            self._inventory_service._repo.update_item_qr_path(item.id, generated_item_qr)
                            items_data.append({"qr_path": generated_item_qr, "label": f"Экз. {item.inventory_number}"})
                    else:
                        items_data.append({"qr_path": item.qr_code_path, "label": f"Экз. {item.inventory_number}"})

                success = PrintingService.generate_batch_qr_pdf(
                    items_data=items_data,
                    book_qr_path=book_qr_path,
                    book_label=book_label,
                    output_path=output_path,
                    cols=cols,
                    mode=mode
                )
            
            if success:
                QMessageBox.information(self, "Успех", f"PDF-файл успешно создан:\n{output_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать PDF-файл")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при печати QR: {e}")

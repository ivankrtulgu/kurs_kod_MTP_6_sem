"""
Book Item Card Widget module.

Provides a high-fidelity detailed view for a specific physical book copy.
Mirrors the design of the BookCardWidget.
"""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout, QInputDialog, QLineEdit, QGroupBox, QMdiSubWindow,
    QDialog, QRadioButton, QSpinBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QColor, QPalette
from pathlib import Path
import json
import secrets
import string

from core.services.inventory_service import InventoryService
from core.services.book_service import BookService
from core.services.printing_service import PrintingService
from core.services.qr_service import QRService
from core.models.inventory import BookItem, ItemStatus
from ui.style_manager import StyleManager

class PrintSettingsWidget(QWidget):
    """Widget for configuring QR print settings with a live preview."""
    def __init__(self, parent_widget, inventory_service, book_service, parent=None):
        super().__init__(parent)
        self.parent_widget = parent_widget
        self._inventory_service = inventory_service
        self._book_service = book_service
        
        self.setWindowTitle("Настройки печати QR")
        self.setMinimumSize(700, 400)
        
        main_layout = QHBoxLayout(self)
        
        # --- Left Side: Settings ---
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        
        # Mode Selection
        mode_group = QGroupBox("Режим печати")
        mode_layout = QVBoxLayout(mode_group)
        self.rb_item_only = QRadioButton("Только экземпляр")
        self.rb_item_only.setChecked(True)
        self.rb_item_only.toggled.connect(self.update_preview)
        self.rb_both = QRadioButton("Экземпляр + Произведение")
        self.rb_both.toggled.connect(self.update_preview)
        mode_layout.addWidget(self.rb_item_only)
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
        is_pair = self.rb_both.isChecked()
        usable_w = 360
        cell_w = usable_w / cols
        
        def create_mock_cell(text):
            cell = QFrame()
            cell.setFixedSize(int(cell_w), 50 if not is_pair else 80)
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

        if not is_pair:
            for r in range(2):
                for c in range(cols):
                    self.page_layout.addWidget(create_mock_cell("Экземпляр"), r, c)
        else:
            for r in range(2):
                for c in range(cols):
                    pair_container = QWidget()
                    pair_layout = QVBoxLayout(pair_container)
                    pair_layout.setContentsMargins(0,0,0,0)
                    pair_layout.setSpacing(0)
                    
                    cell_item = create_mock_cell("Экземпляр")
                    cell_book = create_mock_cell("ISBN: ...")
                    
                    pair_layout.addWidget(cell_item)
                    pair_layout.addWidget(cell_book)
                    pair_container.setStyleSheet("border: 1px solid #aaa; background-color: #f9f9f9;")
                    self.page_layout.addWidget(pair_container, r, c)

    def _on_print(self):
        """Triggers the printing process in the parent widget."""
        settings = {
            "mode": "both" if self.rb_both.isChecked() else "item_only",
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
            "mode": "both" if self.rb_both.isChecked() else "item_only",
            "cols": self.spin_cols.value()
        }

class BookItemCardWidget(QWidget):

    """
    Professional card for a physical book item.
    Replicates the BookCardWidget design.
    """

    STATUS_MAP = {
        ItemStatus.AVAILABLE: "Доступен",
        ItemStatus.LOANED: "Выдан",
        ItemStatus.REPAIR: "В ремонте",
        ItemStatus.LOST: "Утерян",
        ItemStatus.WRITTEN_OFF: "Списан"
    }

    def __init__(self, item_id: int, inventory_service: InventoryService, book_service: BookService, main_window, parent=None):
        super().__init__(parent)
        self._item_id = item_id
        self._inventory_service = inventory_service
        self._book_service = book_service
        self._main_window = main_window
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        self._item: BookItem | None = None
        
        self.setWindowTitle(f"Карточка экземпляра #{item_id}")
        self._init_ui()
        self._load_item()

    def _init_ui(self):
        """Replicates the BookCardWidget layout manually."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Top Header Area ---
        header_group = QGroupBox(" Основная информация")
        header_layout = QHBoxLayout(header_group)
        header_layout.setSpacing(10)
        
        self.lbl_inv_num = QLabel("Инв. №: ---")
        self.lbl_inv_num.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2c3e50;")
        
        self.lbl_status = QLabel("Статус: ---")
        self.lbl_status.setStyleSheet("font-size: 12pt; color: #7f8c8d;")
        
        header_layout.addWidget(self.lbl_inv_num)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_status)
        
        main_layout.addWidget(header_group)

        # --- Main Content Area ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Left Column: Details
        details_group = QGroupBox(" Сведения о книге")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(10, 10, 10, 10)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.lbl_book_title = QLabel("---")
        self.lbl_book_author = QLabel("---")
        self.lbl_book_isbn = QLabel("---")
        self.lbl_location = QLabel("---")
        
        # Row 0: Book Title (Bold)
        grid.addWidget(QLabel("<b>Произведение:</b>"), 0, 0)
        grid.addWidget(self.lbl_book_title, 0, 1)
        
        # Row 1: Author
        grid.addWidget(QLabel("<b>Автор:</b>"), 1, 0)
        grid.addWidget(self.lbl_book_author, 1, 1)
        
        # Row 2: ISBN
        grid.addWidget(QLabel("<b>ISBN:</b>"), 2, 0)
        grid.addWidget(self.lbl_book_isbn, 2, 1)
        
        # Row 3: Location
        grid.addWidget(QLabel("<b>Местоположение:</b>"), 3, 0)
        
        loc_container = QWidget()
        loc_layout = QHBoxLayout(loc_container)
        loc_layout.setContentsMargins(0, 0, 0, 0)
        loc_layout.setSpacing(8)
        
        self.edit_location = QLineEdit()
        self.edit_location.setPlaceholderText("Введите местоположение...")
        
        self.btn_save_loc = QPushButton("Сохранить")
        self.btn_save_loc.setFixedWidth(80)
        self.btn_save_loc.clicked.connect(self._on_save_location)
        
        loc_layout.addWidget(self.edit_location)
        loc_layout.addWidget(self.btn_save_loc)
        
        grid.addWidget(loc_container, 3, 1)
        
        details_layout.addLayout(grid)
        details_layout.addStretch()
        
        content_layout.addWidget(details_group, 2)

        # Right Column: QR Display
        qr_group = QGroupBox(" QR-код")
        qr_layout = QVBoxLayout(qr_group)
        qr_layout.setContentsMargins(10, 10, 10, 10)
        
        self.label_qr = QLabel("QR-код\nне сгенерирован")
        self.label_qr.setAlignment(Qt.AlignCenter)
        self.label_qr.setWordWrap(True)
        self.label_qr.setMinimumSize(200, 200)
        qr_layout.addWidget(self.label_qr)
        
        content_layout.addWidget(qr_group, 1)
        
        main_layout.addLayout(content_layout)

        # --- Bottom Action Area ---
        actions_group = QGroupBox(" Действия")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setContentsMargins(10, 10, 10, 10)
        actions_layout.setSpacing(10)
        
        self.btn_qr = QPushButton("Сгенерировать QR")
        self.btn_qr.setMinimumHeight(40)
        self.btn_qr.clicked.connect(self._on_qr)
        
        self.btn_print_qr = QPushButton("Печать QR")
        self.btn_print_qr.setMinimumHeight(40)
        self.btn_print_qr.clicked.connect(self._on_print_qr)
        
        self.btn_change_status = QPushButton("Изменить статус")
        self.btn_change_status.setMinimumHeight(40)
        self.btn_change_status.clicked.connect(self._on_change_status)
        
        self.btn_issue = QPushButton("Оформить выдачу")
        self.btn_issue.setMinimumHeight(40)
        self.btn_issue.clicked.connect(self._on_issue)
        
        self.btn_return = QPushButton("Оформить возврат")
        self.btn_return.setMinimumHeight(40)
        self.btn_return.clicked.connect(self._on_return)
        
        # ...
        
        actions_layout.addWidget(self.btn_qr)
        actions_layout.addWidget(self.btn_print_qr)
        actions_layout.addWidget(self.btn_change_status)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_issue)
        actions_layout.addWidget(self.btn_return)
        
        main_layout.addWidget(actions_group)
        main_layout.addStretch()

    def _load_item(self):
        """Fetch and display item and book data."""
        try:
            self._item = self._inventory_service._repo.get_item_by_id(self._item_id)
            if not self._item:
                QMessageBox.critical(self, "Ошибка", "Экземпляр не найден")
                return

            book = self._book_service.get_book_by_id(self._item.book_id)
            
            # Update Header
            self.lbl_inv_num.setText(f"Инв. № {self._item.inventory_number}")
            self.lbl_status.setText(f"Статус: {self.STATUS_MAP.get(self._item.status, self._item.status.value)}")
            
            # Update Details
            self.edit_location.setText(self._item.location if self._item.location else "")
            
            if book:
                self.lbl_book_title.setText(book.title)
                self.lbl_book_author.setText(book.author)
                self.lbl_book_isbn.setText(book.isbn or "Не указан")
            else:
                self.lbl_book_title.setText("Произведение не найдено")
                self.lbl_book_author.setText("---")
                self.lbl_book_isbn.setText("N/A")
                
            # Load QR Image
            self._load_image_to_label(self._item.qr_code_path)
            
            # Update Button States based on status
            status = self._item.status
            self.btn_issue.setEnabled(status == ItemStatus.AVAILABLE)
            self.btn_return.setEnabled(status == ItemStatus.LOANED)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e}")

    def _load_image_to_label(self, image_path: str | None):
        """Helper to load QR image from path with fixed scaling to avoid cropping."""
        if not image_path:
            self.label_qr.setText("QR-код\nне сгенерирован")
            return

        path = Path(image_path)
        if not (path.exists() and path.is_file()):
            self.label_qr.setText("Файл не найден")
            return

        try:
            from PIL import Image
            with Image.open(path) as img:
                img = img.convert("RGBA")
                data = img.tobytes("raw", "RGBA")
                qimg = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                
                # Use fixed container size (200x200) instead of label.size() 
                # because label.size() might be (0,0) during init.
                scaled_pixmap = pixmap.scaled(
                    200, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.label_qr.setPixmap(scaled_pixmap)
                self.label_qr.setText("")
        except Exception as e:
            self.label_qr.setText("Ошибка загрузки")

    def _on_qr(self):
        """Generate actual QR code and save to disk."""
        try:
            if not self._item:
                return
            
            import qrcode
            from config.settings import settings
            
            settings.ensure_dirs()
            
            # Get book for ISBN
            book = self._book_service.get_book_by_id(self._item.book_id)
            isbn = book.isbn if book else "unknown"
            
            # Data format: JSON for structure
            qr_dict = {
                "item_inv": self._item.inventory_number,
                "book_id": self._item.book_id,
                "isbn": isbn
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
            
            # Save Path: resources/qr_codes/items/qr_item_{inv}_{isbn}_{salt}.png
            qr_dir = settings.RESOURCES_PATH / "qr_codes" / "items"
            qr_dir.mkdir(parents=True, exist_ok=True)
            
            import secrets
            import string
            random_salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            
            filename = f"qr_item_{self._item.inventory_number}_{isbn}_{random_salt}.png"
            qr_path = qr_dir / filename
            img.save(qr_path)
            
            # Persist path to DB
            self._inventory_service._repo.update_item_qr_path(self._item_id, str(qr_path))
            
            # Update local object and UI
            self._item.qr_code_path = str(qr_path)
            self._load_image_to_label(self._item.qr_code_path)
            
            QMessageBox.information(self, "QR-код", f"QR-код сгенерирован и сохранен:\n{qr_path}")
            
        except ImportError:
            QMessageBox.warning(self, "QR-код", "Установите: pip install qrcode[pil]")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации QR: {e}")

    def _on_issue(self):
        """Open issue window with pre-filled item."""
        if self._item:
            self._issue_window = self._main_window._open_issue_window(self._item.inventory_number)
            # Link lifecycles
            self._main_window.add_close_dependency(self, self._issue_window)

    def _on_return(self):
        """Open return window with pre-filled item."""
        if self._item:
            self._return_window = self._main_window._open_return_window(self._item.inventory_number)
            # Link lifecycles
            self._main_window.add_close_dependency(self, self._return_window)

    def _on_save_location(self):
        """Update the item's location in the database."""
        if not self._item:
            return
            
        new_loc = self.edit_location.text().strip()
        try:
            success = self._inventory_service.update_item_location(self._item_id, new_loc)
            if success:
                QMessageBox.information(self, "Успех", "Местоположение обновлено")
                self._load_item() # Refresh UI to sync object
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить местоположение")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {e}")

    def _on_change_status(self):
        """Change the item status using a selection dialog.
        Available can be set if currently in Repair, Lost or Written Off.
        """
        if not self._item:
            return
        
        try:
            # Base statuses that can always be set
            manual_statuses = [
                ItemStatus.REPAIR,
                ItemStatus.LOST,
                ItemStatus.WRITTEN_OFF
            ]
            
            # Add AVAILABLE if current status is a "problem" status
            current_status = self._item.status
            if current_status in [ItemStatus.REPAIR, ItemStatus.LOST, ItemStatus.WRITTEN_OFF]:
                manual_statuses.insert(0, ItemStatus.AVAILABLE)
            
            # Prepare list with Russian translation
            status_options = [
                (self.STATUS_MAP[s], s) for s in manual_statuses
            ]
            status_labels = [opt[0] for opt in status_options]
            
            # Open combo dialog
            item, ok = QInputDialog.getItem(
                self, "Изменение статуса", 
                f"Выберите новый статус для инв. № {self._item.inventory_number}:", 
                status_labels, 
                0, False
            )
            
            if ok and item:
                # Find corresponding ItemStatus enum
                new_status = next(s for label, s in status_options if label == item)
                
                # Call service with validation
                success = self._inventory_service.update_item_status(self._item_id, new_status)
                if success:
                    QMessageBox.information(self, "Успех", f"Статус изменен на {item}")
                    self._load_item() # Refresh UI
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось изменить статус")
                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {e}")

    def _on_print_qr(self):
        """Handle QR printing process."""
        if not self._item:
            return
            
        try:
            # Open Print Settings as MDI Window
            print_widget = self._main_window._open_print_settings(
                self._item_id, 
                self._inventory_service, 
                self._book_service, 
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
            
            # Gather Data
            item_qr = self._item.qr_code_path
            if not item_qr:
                QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте QR-код экземпляра")
                return
                
            book_qr = None
            if mode == "both":
                book = self._book_service.get_book_by_id(self._item.book_id)
                if book:
                    if not book.qr_code_path:
                        reply = QMessageBox.question(
                            self, "QR-код произведения",
                            "QR-код произведения не найден. Сгенерировать его сейчас?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )
                        if reply == QMessageBox.Yes:
                            generated_path = QRService.generate_book_qr(book)
                            if generated_path:
                                book.qr_code_path = generated_path
                                self._book_service.update_book(book)
                                book_qr = generated_path
                            else:
                                QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать QR-код произведения")
                                return
                    else:
                        book_qr = book.qr_code_path
                else:
                    QMessageBox.warning(self, "Предупреждение", "Произведение не найдено, будет напечатан только QR экземпляра")
            
            # Setup Paths
            from config.settings import settings
            settings.ensure_dirs()
            
            print_dir = settings.RESOURCES_PATH / "printed_qrs"
            print_dir.mkdir(parents=True, exist_ok=True)
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qr_print_{self._item.inventory_number}_{timestamp}.pdf"
            output_path = str(print_dir / filename)
            
            # Generate PDF
            item_label = f"Экземпляр: {self._item.inventory_number}"
            book_label = None
            if book_qr:
                book = self._book_service.get_book_by_id(self._item.book_id)
                book_label = f"ISBN: {book.isbn}" if book and book.isbn else "Произведение"
            
            success = PrintingService.generate_qr_pdf(
                item_qr_path=item_qr,
                item_label=item_label,
                book_qr_path=book_qr,
                book_label=book_label,
                output_path=output_path,
                cols=cols
            )
            
            if success:
                QMessageBox.information(self, "Успех", f"PDF-файл успешно создан:\n{output_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать PDF-файл")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при печати QR: {e}")

    def closeEvent(self, event):
        """Remove dependencies and let window close."""
        event.accept()

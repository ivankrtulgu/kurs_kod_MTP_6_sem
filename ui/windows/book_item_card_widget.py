"""
Book Item Card Widget module.

Provides a high-fidelity detailed view for a specific physical book copy.
Mirrors the design of the BookCardWidget.
"""

from PyQt5.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGridLayout, QInputDialog, QLineEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from pathlib import Path
import json
import secrets
import string

from core.services.inventory_service import InventoryService
from core.services.book_service import BookService
from core.models.inventory import BookItem, ItemStatus
from ui.style_manager import StyleManager

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
        
        self.btn_change_status = QPushButton("Изменить статус")
        self.btn_change_status.setMinimumHeight(40)
        self.btn_change_status.clicked.connect(self._on_change_status)
        
        self.btn_issue = QPushButton("Оформить выдачу")
        self.btn_issue.setMinimumHeight(40)
        self.btn_issue.clicked.connect(self._on_issue)
        
        self.btn_return = QPushButton("Оформить возврат")
        self.btn_return.setMinimumHeight(40)
        self.btn_return.clicked.connect(self._on_return)
        
        actions_layout.addWidget(self.btn_qr)
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

    def closeEvent(self, event):
        """Remove dependencies and let window close."""
        event.accept()

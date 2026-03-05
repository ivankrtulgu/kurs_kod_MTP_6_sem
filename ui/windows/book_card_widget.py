# ui/windows/book_card_widget.py
"""Book card widget with repository integration."""

from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog
from ui.generated.ui_book_card_widget import Ui_BookCardWidget

from core.services.book_service import BookService, ValidationError
from core.models.book import Book
from ui.windows.add_book_dialog import AddBookDialog


class BookCardWidget(QWidget, Ui_BookCardWidget):
    """Виджет карточки книги с интеграцией репозитория."""

    def __init__(
        self,
        book_id: int = 0,
        parent=None,
        book_service: BookService | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        
        # Inject service
        self._book_service = book_service or BookService()
        
        # Store book data
        self._book: Book | None = None
        self._book_id = book_id
        
        self._connect_signals()
        
        # Load book data
        if book_id:
            self._load_book(book_id)

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_export.clicked.connect(self._on_export)
        self.btn_qr.clicked.connect(self._on_qr)

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
            
            # Open add book dialog with current book data
            dialog = AddBookDialog(book_service=self._book_service, parent=self)
            
            # Pre-fill with current book data
            if self._book:
                dialog.input_author.setText(self._book.author)
                dialog.input_title.setText(self._book.title)
                dialog.input_subtitle.setText(self._book.subtitle or "")
                dialog.input_responsibility.setText(self._book.responsibility or "")
                dialog.input_edition.setText(self._book.edition or "")
                dialog.input_place.setText(self._book.place)
                dialog.input_publisher.setText(self._book.publisher)
                dialog.input_year.setValue(self._book.year)
                dialog.input_pages.setValue(self._book.pages)
                dialog.input_isbn.setText(self._book.isbn)
                dialog.input_copyright.setText(self._book.copyright or "")
                dialog.input_udc.setText(self._book.udc or "")
                dialog.input_bbk.setText(self._book.bbk or "")
                dialog.input_author_mark.setText(self._book.author_mark or "")
                dialog.text_reviewers.setPlainText(self._book.reviewers or "")
                dialog.text_annotation.setPlainText(self._book.annotation or "")
                dialog.input_doi.setText(self._book.doi or "")
                if self._book.cover_image_path:
                    dialog.input_cover_path.setText(self._book.cover_image_path)
            
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
            from pathlib import Path
            from config.settings import settings
            
            settings.ensure_dirs()
            
            # Create QR code with bibliographic record or DOI
            qr_data = self._book.doi or self._book.isbn or self._book.format_bibliographic_record()
            
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
            qr_path = qr_dir / f"book_{self._book_id}_qr.png"
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

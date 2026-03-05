# ui/windows/add_book_dialog.py
"""Add book dialog with validation and service integration."""

from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from ui.generated.ui_add_book_dialog import Ui_AddBookDialog

from core.models.book import Book
from core.services.book_service import BookService, ValidationError
from ui.windows.ocr_dialog import OcrDialog


class AddBookDialog(QDialog, Ui_AddBookDialog):
    """Диалог добавления книги с валидацией и интеграцией сервиса."""

    def __init__(
        self,
        parent=None,
        book_service: BookService | None = None,
        ocr_data: dict | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        
        # Inject service
        self._book_service = book_service or BookService()
        self._ocr_data = ocr_data or {}
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        
        self._connect_signals()
        
        # Pre-fill with OCR data if available
        if self._ocr_data:
            self._fill_from_ocr()

    def _connect_signals(self):
        """Connect button signals."""
        self.btn_ocr.clicked.connect(self._on_ocr)
        self.btn_select_cover.clicked.connect(self._on_select_cover)

    def _fill_from_ocr(self):
        """Fill form fields from OCR data."""
        if 'author' in self._ocr_data:
            self.input_author.setText(self._ocr_data['author'])
        if 'title' in self._ocr_data:
            self.input_title.setText(self._ocr_data['title'])
        if 'publisher' in self._ocr_data:
            self.input_publisher.setText(self._ocr_data['publisher'])
        if 'year' in self._ocr_data:
            self.input_year.setValue(int(self._ocr_data['year']))
        if 'isbn' in self._ocr_data:
            self.input_isbn.setText(self._ocr_data['isbn'])
        if 'udc' in self._ocr_data:
            self.input_udc.setText(self._ocr_data['udc'])
        if 'bbk' in self._ocr_data:
            self.input_bbk.setText(self._ocr_data['bbk'])
        if 'pages' in self._ocr_data:
            self.input_pages.setValue(int(self._ocr_data['pages']))
        if 'place' in self._ocr_data:
            self.input_place.setText(self._ocr_data['place'])

    def _validate_inputs(self) -> tuple[bool, str]:
        """
        Validate all required input fields.

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Validate author
        author = self.input_author.text().strip()
        if not author:
            return False, "Поле 'Автор' обязательно для заполнения"

        # Validate title
        title = self.input_title.text().strip()
        if not title:
            return False, "Поле 'Название' обязательно для заполнения"

        # Validate year (1900-2100) - already validated by QSpinBox
        year = self.input_year.value()
        if not (1900 <= year <= 2100):
            return False, "Год должен быть в диапазоне 1900-2100"

        # Validate pages - already validated by QSpinBox
        pages = self.input_pages.value()
        if pages <= 0:
            return False, "Количество страниц должно быть больше 0"

        # Validate ISBN
        isbn = self.input_isbn.text().strip()
        if not isbn:
            return False, "Поле 'ISBN' обязательно для заполнения"

        # Validate place
        place = self.input_place.text().strip()
        if not place:
            return False, "Поле 'Место издания' обязательно для заполнения"

        # Validate publisher
        publisher = self.input_publisher.text().strip()
        if not publisher:
            return False, "Поле 'Издательство' обязательно для заполнения"

        # Validate cover image exists if specified
        cover_path = self.input_cover_path.text().strip()
        if cover_path:
            from pathlib import Path
            if not Path(cover_path).exists():
                return False, f"Файл обложки не найден: {cover_path}"

        return True, ""

    def _on_ocr(self):
        """Open OCR dialog and populate fields with recognized text."""
        try:
            dialog = OcrDialog(parent=self)
            if dialog.exec_() == OcrDialog.Accepted:
                ocr_data = dialog.get_recognized_data()
                if ocr_data:
                    self._fill_from_ocr()
                    QMessageBox.information(
                        self, "OCR",
                        "Данные успешно распознаны и заполнены в форму"
                    )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка OCR", f"Ошибка распознавания: {e}")

    def _on_select_cover(self):
        """Select cover image file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                from pathlib import Path
                if Path(file_path).exists():
                    self.input_cover_path.setText(file_path)
                else:
                    QMessageBox.warning(self, "Ошибка", f"Файл не найден: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выбора файла: {e}")

    def _on_save(self):
        """Validate and save book to repository."""
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs()
            if not is_valid:
                QMessageBox.warning(self, "Ошибка валидации", error_msg)
                return

            # Create Book object from form data
            book = Book(
                id=0,  # Will be assigned by repository
                author=self.input_author.text().strip(),
                title=self.input_title.text().strip(),
                subtitle=self.input_subtitle.text().strip(),
                responsibility=self.input_responsibility.text().strip(),
                edition=self.input_edition.text().strip(),
                place=self.input_place.text().strip(),
                publisher=self.input_publisher.text().strip(),
                year=self.input_year.value(),
                pages=self.input_pages.value(),
                isbn=self.input_isbn.text().strip(),
                copyright=self.input_copyright.text().strip(),
                udc=self.input_udc.text().strip(),
                bbk=self.input_bbk.text().strip(),
                author_mark=self.input_author_mark.text().strip(),
                reviewers=self.text_reviewers.toPlainText().strip(),
                annotation=self.text_annotation.toPlainText().strip(),
                abstract="",  # Not in UI
                doi=self.input_doi.text().strip(),
                content_type=self.input_content_type.text().strip() if hasattr(self, 'input_content_type') else "Текст",
                access_method=self.input_access_method.text().strip() if hasattr(self, 'input_access_method') else "непосредственный",
                cover_image_path=self.input_cover_path.text().strip(),
            )

            # Save via service
            book_id = self._book_service.add_book(book)
            
            QMessageBox.information(
                self, "Успешно",
                f"Книга '{book.title}' успешно добавлена с ID: {book_id}"
            )
            self.accept()

        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить книгу: {e}")

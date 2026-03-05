# ui/windows/add_book_widget.py
"""Add book widget for MDI - Professional implementation."""

from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog
from ui.generated.ui_add_book_dialog import Ui_AddBookDialog

from core.models.book import Book
from core.services.book_service import BookService, ValidationError
from ui.windows.ocr_window import OcrWindow


class AddBookWidget(QWidget, Ui_AddBookDialog):
    """Виджет добавления книги с валидацией и интеграцией сервиса (для MDI)."""

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
        self.button_box.rejected.connect(self._on_cancel)

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
        Required fields match UI markers (*): Author, Title, Place, Publisher, Year, Pages, ISBN

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        # Validate author (*)
        author = self.input_author.text().strip()
        if not author:
            return False, "Поле 'Автор' обязательно для заполнения"

        # Validate title (*)
        title = self.input_title.text().strip()
        if not title:
            return False, "Поле 'Название' обязательно для заполнения"

        # Validate place (*)
        place = self.input_place.text().strip()
        if not place:
            return False, "Поле 'Место издания' обязательно для заполнения"

        # Validate publisher (*)
        publisher = self.input_publisher.text().strip()
        if not publisher:
            return False, "Поле 'Издательство' обязательно для заполнения"

        # Validate year (*) - already validated by QSpinBox (1900-2100)
        year = self.input_year.value()
        if not (1900 <= year <= 2100):
            return False, "Год должен быть в диапазоне 1900-2100"

        # Validate pages (*) - already validated by QSpinBox (minimum 1)
        pages = self.input_pages.value()
        if pages <= 0:
            return False, "Количество страниц должно быть больше 0"

        # Validate ISBN (*)
        isbn = self.input_isbn.text().strip()
        if not isbn:
            return False, "Поле 'ISBN' обязательно для заполнения"

        # Validate cover image exists if specified
        cover_path = self.input_cover_path.text().strip()
        if cover_path:
            from pathlib import Path
            if not Path(cover_path).exists():
                return False, f"Файл обложки не найден: {cover_path}"

        return True, ""

    def _on_ocr(self):
        """Open OCR widget and populate fields with recognized text."""
        try:
            # Find parent main window and open OCR as MDI child
            parent_window = self.window()
            if hasattr(parent_window, 'mdi_area'):
                # Open OCR in the main MDI area
                ocr_widget = OcrWidget()
                
                from PyQt5.QtWidgets import QMdiSubWindow
                from PyQt5.QtCore import Qt
                
                sub_window = QMdiSubWindow()
                sub_window.setWidget(ocr_widget)
                sub_window.setWindowTitle("OCR для добавления книги")
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                sub_window.resize(1000, 750)
                
                parent_window.mdi_area.addSubWindow(sub_window)
                sub_window.show()
                
                # Connect OCR data signal to fill form
                ocr_widget.ocr_data_ready.connect(self._fill_from_ocr_data)
                
            else:
                # Fallback: use embedded OCR
                QMessageBox.information(self, "OCR", "Откройте главное окно для полноценного OCR")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка OCR", f"Ошибка распознавания: {e}")

    def _fill_from_ocr_data(self, ocr_data: dict):
        """Fill form with OCR data and activate this window."""
        self._ocr_data = ocr_data
        self._fill_from_ocr()
        
        # Activate this window
        parent = self.parent()
        if parent:
            from PyQt5.QtWidgets import QMdiSubWindow
            if isinstance(parent, QMdiSubWindow):
                parent.showNormal()
                parent.activateWindow()
        
        QMessageBox.information(
            self, "OCR",
            "Данные успешно распознаны и заполнены в форму"
        )

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
                return  # Don't close widget, let user fix errors

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
                abstract=self.text_abstract.toPlainText().strip(),
                doi=self.input_doi.text().strip(),
                content_type=self.input_content_type.text().strip(),
                access_method=self.input_access_method.text().strip(),
                cover_image_path=self.input_cover_path.text().strip(),
            )

            # Save via service
            book_id = self._book_service.add_book(book)

            QMessageBox.information(
                self, "Успешно",
                f"Книга '{book.title}' успешно добавлена с ID: {book_id}"
            )
            
            # Close the add book window after successful save
            self._close_window()

        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
            # Don't close widget, let user fix validation errors
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить книгу: {e}")
            # Don't close widget on error

    def _close_window(self):
        """Close the add book window."""
        parent = self.parent()
        from PyQt5.QtWidgets import QMdiSubWindow
        if isinstance(parent, QMdiSubWindow):
            parent.close()
        else:
            self.close()

    def _on_cancel(self):
        """Handle cancel button - close the widget."""
        # Check if form has data
        if self._has_data():
            reply = QMessageBox.question(
                self, "Подтверждение",
                "В форме есть незавершённые данные. Закрыть?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Close parent subwindow if exists
        from PyQt5.QtWidgets import QMdiSubWindow
        parent = self.parent()
        if isinstance(parent, QMdiSubWindow):
            parent.close()
        else:
            self.close()

    def _has_data(self) -> bool:
        """Check if form has any data entered."""
        if self.input_author.text().strip():
            return True
        if self.input_title.text().strip():
            return True
        if self.input_place.text().strip():
            return True
        if self.input_publisher.text().strip():
            return True
        if self.input_isbn.text().strip():
            return True
        return False

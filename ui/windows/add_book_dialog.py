# ui/windows/add_book_dialog.py
"""Add book dialog with validation and service integration."""

from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog, QGroupBox, QVBoxLayout, QFormLayout
from ui.generated.ui_add_book_dialog import Ui_AddBookDialog
from ui.style_manager import StyleManager

from core.models.book import Book
from core.services.book_service import BookService, ValidationError
from ui.windows.ocr_window import OcrWindow


class AddBookDialog(QDialog, Ui_AddBookDialog):
    """Диалог добавления книги с валидацией и интеграцией сервиса."""

    def __init__(
        self,
        parent=None,
        book_service: BookService | None = None,
        ocr_data: dict | None = None,
        book_id: int | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet(StyleManager.get_stylesheet())

        # Standardize main layout
        if self.verticalLayout:
            self.verticalLayout.setSpacing(10)
            self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        
        # Inject service
        self._book_service = book_service or BookService()
        self._ocr_data = ocr_data or {}
        self._book_id = book_id  # Store book_id for edit mode
        
        self._setup_eco_tabs()
        
        # Set window title based on mode
        if self._book_id:
            self.setWindowTitle("Редактировать книгу")
        else:
            self.setWindowTitle("Добавить книгу")
        
        # Connect button box signals
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        
        self._connect_signals()
        
        # Pre-fill with OCR data if available
        if self._ocr_data:
            self._fill_from_ocr()
            
        # If in edit mode, load book data for pre-filling
        if self._book_id:
            self._load_book_for_edit()

    def _setup_eco_tabs(self):
        """Wrap tab contents in QGroupBoxes to match Eco-Style design."""
        # For tab_main
        self.main_group = QGroupBox("Основные данные")
        self.main_group_layout = QVBoxLayout(self.main_group)
        self.main_group_layout.setSpacing(10)
        
        for i in range(self.formLayout_main.rowCount()):
            label = self.formLayout_main.itemAt(i, QFormLayout.LabelRole).widget()
            field = self.formLayout_main.itemAt(i, QFormLayout.FieldRole).widget()
            if label: self.main_group_layout.addWidget(label)
            if field: self.main_group_layout.addWidget(field)
        
        self.tab_main.setLayout(QVBoxLayout())
        self.tab_main.layout().setContentsMargins(10, 10, 10, 10)
        self.tab_main.layout().addWidget(self.main_group)

        # For tab_classification
        self.class_group = QGroupBox("Классификация")
        self.class_group_layout = QVBoxLayout(self.class_group)
        self.class_group_layout.setSpacing(10)
        
        for i in range(self.formLayout_classification.rowCount()):
            label = self.formLayout_classification.itemAt(i, QFormLayout.LabelRole).widget()
            field = self.formLayout_classification.itemAt(i, QFormLayout.FieldRole).widget()
            if label: self.class_group_layout.addWidget(label)
            if field: self.class_group_layout.addWidget(field)
            
        self.tab_classification.setLayout(QVBoxLayout())
        self.tab_classification.layout().setContentsMargins(10, 10, 10, 10)
        self.tab_classification.layout().addWidget(self.class_group)

        # For tab_additional
        self.additional_group = QGroupBox("Дополнительная информация")
        self.additional_group_layout = QVBoxLayout(self.additional_group)
        self.additional_group_layout.setSpacing(10)
        
        while self.verticalLayout_additional.count():
            item = self.verticalLayout_additional.takeAt(0)
            if item.widget():
                self.additional_group_layout.addWidget(item.widget())
            elif item.layout():
                self.additional_group_layout.addLayout(item.layout())
        
        self.tab_additional.setLayout(QVBoxLayout())
        self.tab_additional.layout().setContentsMargins(10, 10, 10, 10)
        self.tab_additional.layout().addWidget(self.additional_group)

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
            # Sanitize year: remove all non-digit characters
            year_str = ''.join(filter(str.isdigit, str(self._ocr_data['year'])))
            if year_str:
                self.input_year.setValue(int(year_str))
        if 'isbn' in self._ocr_data:
            self.input_isbn.setText(self._ocr_data['isbn'])
        if 'udc' in self._ocr_data:
            self.input_udc.setText(self._ocr_data['udc'])
        if 'bbk' in self._ocr_data:
            self.input_bbk.setText(self._ocr_data['bbk'])
        if 'pages' in self._ocr_data:
            pages_str = ''.join(filter(str.isdigit, str(self._ocr_data['pages'])))
            if pages_str:
                self.input_pages.setValue(int(pages_str))
        if 'place' in self._ocr_data:
            self.input_place.setText(self._ocr_data['place'])
        if 'annotation' in self._ocr_data:
            self.text_annotation.setPlainText(self._ocr_data['annotation'])
        if 'author_mark' in self._ocr_data:
            self.input_author_mark.setText(self._ocr_data['author_mark'])

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
        """Open OCR window and populate fields with recognized text."""
        try:
            # Find parent main window and open OCR as MDI child
            parent_window = self.window()
            if hasattr(parent_window, 'mdi_area'):
                # Open OCR in the main MDI area
                ocr_window = OcrWindow()
                
                from PyQt5.QtWidgets import QMdiSubWindow
                from PyQt5.QtCore import Qt
                
                sub_window = QMdiSubWindow()
                sub_window.setWidget(ocr_window)
                sub_window.setWindowTitle("OCR для добавления книги")
                sub_window.setAttribute(Qt.WA_DeleteOnClose)
                sub_window.resize(1400, 900)
                
                parent_window.mdi_area.addSubWindow(sub_window)
                sub_window.show()
                
                # Connect OCR data signal to fill form
                ocr_window.ocr_data_ready.connect(self._fill_from_ocr_data)
                
            else:
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

    def _load_book_for_edit(self):
        """Load book data for editing."""
        try:
            book = self._book_service.get_book(self._book_id)
            if book:
                self.input_author.setText(book.author)
                self.input_title.setText(book.title)
                self.input_subtitle.setText(book.subtitle or "")
                self.input_responsibility.setText(book.responsibility or "")
                self.input_edition.setText(book.edition or "")
                self.input_place.setText(book.place)
                self.input_publisher.setText(book.publisher)
                self.input_year.setValue(book.year)
                self.input_pages.setValue(book.pages)
                self.input_isbn.setText(book.isbn)
                self.input_copyright.setText(book.copyright or "")
                self.input_udc.setText(book.udc or "")
                self.input_bbk.setText(book.bbk or "")
                self.input_author_mark.setText(book.author_mark or "")
                self.text_reviewers.setPlainText(book.reviewers or "")
                self.text_annotation.setPlainText(book.annotation or "")
                self.text_abstract.setPlainText(book.abstract or "")
                self.input_doi.setText(book.doi or "")
                self.input_content_type.setText(book.content_type or "")
                self.input_access_method.setText(book.access_method or "")
                if book.cover_image_path:
                    self.input_cover_path.setText(book.cover_image_path)
            else:
                QMessageBox.warning(self, "Ошибка", f"Книга с ID {self._book_id} не найдена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить книгу для редактирования: {e}")

    def _on_save(self):
        """Validate and save book to repository."""
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs()
            if not is_valid:
                QMessageBox.warning(self, "Ошибка валидации", error_msg)
                return  # Don't close dialog, let user fix errors

            # Create Book object from form data
            book = Book(
                id=self._book_id if self._book_id else 0,  # Use existing ID for edit mode
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
            if self._book_id:  # Edit mode
                success = self._book_service.update_book(book)
                if success:
                    QMessageBox.information(
                        self, "Успешно",
                        f"Книга '{book.title}' успешно обновлена"
                    )
                    self.accept()  # Close dialog only on success
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось обновить книгу")
            else:  # Add mode
                book_id = self._book_service.add_book(book)
                QMessageBox.information(
                    self, "Успешно",
                    f"Книга '{book.title}' успешно добавлена с ID: {book_id}"
                )
                self.accept()  # Close dialog only on success

        except ValidationError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
            # Don't close dialog, let user fix validation errors
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить книгу: {e}")
            # Don't close dialog on error

# ui/windows/add_book_widget.py
"""Add book widget for MDI - Professional implementation."""

from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog, QGroupBox, QVBoxLayout, QFormLayout
from ui.generated.ui_add_book_dialog import Ui_AddBookDialog
from ui.style_manager import StyleManager

from core.models.book import Book
from core.services.book_service import BookService, ValidationError
from ui.windows.ocr_window import OcrWindow
from ui.icon_manager import IconManager


class AddBookWidget(QWidget, Ui_AddBookDialog):
    """Виджет добавления книги с валидацией и интеграцией сервиса (для MDI)."""
    WINDOW_TITLE = "Добавление книги"

    def __init__(
        self,
        parent=None,
        book_service: BookService | None = None,
        ocr_data: dict | None = None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet(StyleManager.get_stylesheet())
        self.setWindowIcon(IconManager.get_default_icon())

        # Standardize main layout
        if self.layout():
            self.layout().setSpacing(10)
            self.layout().setContentsMargins(10, 10, 10, 10)
        
        # Inject service
        self._book_service = book_service or BookService()
        self._ocr_data = ocr_data or {}
        
        self._setup_eco_tabs()
        
        # Connect button box signals

        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self._on_cancel)

        self._connect_signals()

        # Pre-fill with OCR data if available
        if self._ocr_data:
            self._fill_from_ocr()

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
            # Find parent main window
            parent_window = self.window()
            if not hasattr(parent_window, 'mdi_area'):
                QMessageBox.information(self, "OCR", "Откройте главное окно для полноценного OCR")
                return

            # Create the OCR widget
            ocr_widget = OcrWindow()
            
            # Use the main window's managed window creator to ensure it's a ManagedMdiSubWindow
            if hasattr(parent_window, '_create_sub_window'):
                sub_window = parent_window._create_sub_window(
                    ocr_widget, 
                    "OCR для добавления книги", 
                    1000, 750
                )
                parent_window.mdi_area.addSubWindow(sub_window)
                sub_window.show()
                
                # Link lifecycles: close OCR window if this widget is closed
                if hasattr(parent_window, 'add_close_dependency'):
                    parent_window.add_close_dependency(self, ocr_widget)
            else:
                # Fallback for safety
                from PyQt5.QtWidgets import QMdiSubWindow
                sub_window = QMdiSubWindow()
                sub_window.setWidget(ocr_widget)
                sub_window.setWindowTitle("OCR для добавления книги")
                parent_window.mdi_area.addSubWindow(sub_window)
                sub_window.show()

            # Connect OCR data signal to fill form
            ocr_widget.ocr_data_ready.connect(self._fill_from_ocr_data)
            
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
        self._close_window()

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

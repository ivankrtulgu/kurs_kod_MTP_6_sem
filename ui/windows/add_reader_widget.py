"""
Add Reader Widget module.

Provides a widget for adding and editing library readers in an MDI environment.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QComboBox, QTextEdit, QMessageBox
)

from PyQt5.QtCore import Qt
from core.services.inventory_service import InventoryService
from core.models.inventory import Reader

class AddReaderWidget(QWidget):
    """
    Widget for adding or editing a library reader.
    Designed to be hosted within a QMdiSubWindow.
    """

    def __init__(self, service: InventoryService, reader_id: int | None = None, main_window=None, parent=None):
        super().__init__(parent)
        self._service = service
        self._reader_id = reader_id
        self._main_window = main_window
        
        self.setWindowTitle("Добавление читателя" if reader_id is None else "Редактирование читателя")
        self._init_ui()
        
        if reader_id:
            self._load_reader(reader_id)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Name fields
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Введите фамилию")
        form.addRow("Фамилия*:", self.last_name_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Введите имя")
        form.addRow("Имя*:", self.first_name_input)

        self.middle_name_input = QLineEdit()
        self.middle_name_input.setPlaceholderText("Введите отчество")
        form.addRow("Отчество:", self.middle_name_input)

        # Contact info
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Введите номер телефона")
        form.addRow("Телефон:", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("example@mail.com")
        form.addRow("Email:", self.email_input)

        # Personal details
        self.birth_date_input = QLineEdit()
        self.birth_date_input.setPlaceholderText("ГГГГ-ММ-ДД")
        form.addRow("Дата рождения:", self.birth_date_input)

        self.passport_series_input = QLineEdit()
        self.passport_series_input.setPlaceholderText("Серия")
        form.addRow("Серия паспорта:", self.passport_series_input)

        self.passport_number_input = QLineEdit()
        self.passport_number_input.setPlaceholderText("Номер")
        form.addRow("Номер паспорта:", self.passport_number_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Улица, дом, квартира")
        form.addRow("Адрес проживания:", self.address_input)

        self.reg_date_input = QLineEdit()
        self.reg_date_input.setPlaceholderText("ГГГГ-ММ-ДД")
        form.addRow("Дата регистрации:", self.reg_date_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "blocked", "expired"])
        form.addRow("Статус:", self.status_combo)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        form.addRow("Заметки:", self.notes_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self._handle_save)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self._close_window)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _load_reader(self, reader_id: int):
        """Load existing reader data for editing."""
        try:
            reader = self._service._repo.get_reader_by_id(reader_id)
            if reader:
                self.last_name_input.setText(reader.last_name)
                self.first_name_input.setText(reader.first_name)
                self.middle_name_input.setText(reader.middle_name)
                self.birth_date_input.setText(reader.birth_date)
                self.passport_series_input.setText(reader.passport_series)
                self.passport_number_input.setText(reader.passport_number)
                self.phone_input.setText(reader.phone)
                self.email_input.setText(reader.email)
                self.address_input.setText(reader.home_address)
                self.reg_date_input.setText(reader.registration_date)
                self.status_combo.setCurrentText(reader.status)
                self.notes_input.setPlainText(reader.notes)
        except Exception as e:
            if self._main_window:
                self._main_window.notify(f"Не удалось загрузить данные читателя: {e}", "Ошибка", "error")

    def _handle_save(self):
        try:
            last_name = self.last_name_input.text().strip()
            first_name = self.first_name_input.text().strip()
            middle_name = self.middle_name_input.text().strip()
            birth_date = self.birth_date_input.text().strip()
            passport_series = self.passport_series_input.text().strip()
            passport_number = self.passport_number_input.text().strip()
            phone = self.phone_input.text().strip()
            email = self.email_input.text().strip()
            address = self.address_input.text().strip()
            reg_date = self.reg_date_input.text().strip()
            status = self.status_combo.currentText()
            notes = self.notes_input.toPlainText().strip()

            if not last_name or not first_name:
                if self._main_window:
                    self._main_window.notify("Фамилия и Имя обязательны для заполнения", "Ошибка ввода", "warning")
                return

            if self._reader_id:
                # Update
                reader = Reader(
                    id=self._reader_id,
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    birth_date=birth_date,
                    phone=phone,
                    email=email,
                    home_address=address,
                    registration_date=reg_date,
                    status=status,
                    notes=notes,
                    passport_series=passport_series,
                    passport_number=passport_number
                )
                self._service.update_reader(reader)
                QMessageBox.information(self, "Успех", "Данные читателя обновлены")
            else:
                # Create
                reader = Reader(
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    birth_date=birth_date,
                    phone=phone,
                    email=email,
                    home_address=address,
                    registration_date=reg_date,
                    status=status,
                    notes=notes,
                    passport_series=passport_series,
                    passport_number=passport_number
                )
                self._service.add_reader(reader)
                QMessageBox.information(self, "Успех", "Читатель добавлен")
            
            self._close_window()

        except Exception as e:
            if self._main_window:
                self._main_window.notify(f"Ошибка при сохранении: {e}", "Ошибка системы", "error")

    def _close_window(self):
        """Close the MDI subwindow containing this widget."""
        from PyQt5.QtWidgets import QMdiSubWindow
        parent = self.parent()
        if isinstance(parent, QMdiSubWindow):
            parent.close()
        else:
            self.close()

"""
Add Reader Widget module.

Provides a widget for adding and editing library readers in an MDI environment.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QCheckBox, QMessageBox
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

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите ФИО")
        form.addRow("ФИО:", self.name_input)

        # Phone input
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Введите номер телефона")
        form.addRow("Телефон:", self.phone_input)

        # Active status
        self.active_checkbox = QCheckBox("Активен")
        self.active_checkbox.setChecked(True)
        form.addRow("Статус:", self.active_checkbox)

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
                self.name_input.setText(reader.full_name)
                self.phone_input.setText(reader.phone)
                self.active_checkbox.setChecked(reader.is_active)
        except Exception as e:
            if self._main_window:
                self._main_window.notify(f"Не удалось загрузить данные читателя: {e}", "Ошибка", "error")

    def _handle_save(self):
        try:
            name = self.name_input.text().strip()
            phone = self.phone_input.text().strip()
            is_active = self.active_checkbox.isChecked()

            if not name or not phone:
                if self._main_window:
                    self._main_window.notify("Поля ФИО и Телефон обязательны для заполнения", "Ошибка ввода", "warning")
                return

            if self._reader_id:
                # Update
                reader = Reader(
                    id=self._reader_id,
                    full_name=name,
                    phone=phone,
                    is_active=is_active
                )
                self._service.update_reader(reader)
                QMessageBox.information(self, "Успех", "Данные читателя обновлены")
            else:
                # Create
                reader = Reader(
                    full_name=name,
                    phone=phone,
                    is_active=is_active
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

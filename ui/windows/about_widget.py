# ui/windows/about_widget.py
"""About widget - for MDI child window."""

from PyQt5.QtWidgets import QWidget
from ui.generated.ui_about_dialog import Ui_AboutDialog


class AboutWidget(QWidget, Ui_AboutDialog):
    """Виджет 'О программе' (для MDI)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

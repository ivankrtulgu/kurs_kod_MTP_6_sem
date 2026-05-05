# ui/windows/about_dialog.py
from PyQt5.QtWidgets import QDialog
from ui.generated.ui_about_dialog import Ui_AboutDialog
from ui.style_manager import StyleManager
from ui.icon_manager import IconManager


class AboutDialog(QDialog, Ui_AboutDialog):
    """Диалог 'О программе'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        self.setWindowIcon(IconManager.get_default_icon())

        # Update layout
        if hasattr(self, 'verticalLayout'):
            self.verticalLayout.setSpacing(10)
            self.verticalLayout.setContentsMargins(10, 10, 10, 10)

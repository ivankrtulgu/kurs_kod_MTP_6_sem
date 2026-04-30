# ui/windows/about_widget.py
"""About widget - for MDI child window."""

from PyQt5.QtWidgets import QWidget
from ui.generated.ui_about_dialog import Ui_AboutDialog
from ui.style_manager import StyleManager


class AboutWidget(QWidget, Ui_AboutDialog):
    """Виджет 'О программе' (для MDI)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # Apply Eco-Style
        self.setStyleSheet(StyleManager.get_stylesheet())
        
        # Update layout
        if hasattr(self, 'verticalLayout'):
            self.verticalLayout.setSpacing(10)
            self.verticalLayout.setContentsMargins(10, 10, 10, 10)

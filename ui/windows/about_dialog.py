# ui/windows/about_dialog.py
from PyQt5.QtWidgets import QDialog
from ui.generated.ui_about_dialog import Ui_AboutDialog


class AboutDialog(QDialog, Ui_AboutDialog):
    """Диалог 'О программе'."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
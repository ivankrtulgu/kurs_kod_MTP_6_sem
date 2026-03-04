# main.py
import os
import sys

import PyQt5
pyqt5_path = os.path.dirname(PyQt5.__file__)
plugins_path = os.path.join(pyqt5_path, 'Qt5', 'plugins', 'platforms')

if os.path.exists(plugins_path):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

from PyQt5.QtWidgets import QApplication
from ui.windows.main_window import MainWindow


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    app.setApplicationName("Библиотека OCR")
    app.setOrganizationName("LibraryOCR")
    
    # Создаём главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
"""
Application entry point (Composition Root).

This file handles the initialization of the entire system, creating dependencies
and injecting them into the UI layer.
"""

import os
import sys
import PyQt5
from PyQt5.QtWidgets import QApplication

# Setup Qt plugins path for environments where it's not automatically found
pyqt5_path = os.path.dirname(PyQt5.__file__)
plugins_path = os.path.join(pyqt5_path, 'Qt5', 'plugins', 'platforms')
if os.path.exists(plugins_path):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

from infrastructure.database.connection import DatabaseManager
from infrastructure.database.inventory_repository import SQLiteInventoryRepository
from core.services.book_service import BookService
from core.services.inventory_service import InventoryService
from ui.windows.main_window import MainWindow


def main():
    """
    Application entry point.
    Implements the Composition Root pattern to manage dependencies.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("Библиотека OCR")
    app.setOrganizationName("LibraryOCR")

    # 1. Infrastructure Layer
    # DatabaseManager requires the path to the .db file
    db_path = "library.db"
    db_manager = DatabaseManager(db_path)
    
    # Initialize Repositories
    inventory_repo = SQLiteInventoryRepository(db_manager)
    # Note: BookRepository is usually instantiated inside BookService or passed here
    # Based on current architecture, BookService often handles its own repo or takes one.

    # 2. Service Layer
    # Create services and inject repositories
    book_service = BookService() 
    inventory_service = InventoryService(inventory_repo)

    # 3. UI Layer
    # Inject services into the Main Window
    window = MainWindow(
        book_service=book_service, 
        inventory_service=inventory_service
    )
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

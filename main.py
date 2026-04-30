"""
Application entry point (Composition Root).

This file handles the initialization of the entire system, creating dependencies
and injecting them into the UI layer.
"""

import os
import sys
import PyQt5
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Setup Qt plugins path for environments where it's not automatically found
pyqt5_path = os.path.dirname(PyQt5.__file__)
plugins_path = os.path.join(pyqt5_path, 'Qt5', 'plugins', 'platforms')
if os.path.exists(plugins_path):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path

from infrastructure.database.connection import DatabaseManager
from infrastructure.database.book_repository import SQLiteBookRepository
from infrastructure.database.inventory_repository import SQLiteInventoryRepository
from core.services.book_service import BookService
from core.services.inventory_service import InventoryService
from ui.windows.main_window import MainWindow
from ui.scanner_filter import BarcodeEventFilter


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
    # Use path relative to the application folder to match init_db.py
    app_dir = Path(__file__).parent
    db_path = app_dir / "library.db"
    db_manager = DatabaseManager(db_path)
    
    # 2. Repository Layer
    book_repo = SQLiteBookRepository(db_manager)
    inventory_repo = SQLiteInventoryRepository(db_manager)
    
    # 3. Service Layer
    # Create services and inject repositories
    book_service = BookService(db_manager) 
    inventory_service = InventoryService(inventory_repo)

    # 4. UI Layer
    # Inject services into the Main Window
    window = MainWindow(
        book_service=book_service, 
        inventory_service=inventory_service
    )
    
    # 5. Global Scanner Integration
    # Attach filter to window to prevent garbage collection
    window.scanner_filter = BarcodeEventFilter(window)
    app.installEventFilter(window.scanner_filter)
    
    # Connect scanner signals to MainWindow handlers
    def handle_scan(scan_type, identifier):
        if scan_type == "item":
            window.open_item_card(identifier)
        elif scan_type == "book":
            window.open_book_card(identifier)
            
    window.scanner_filter.scan_detected.connect(handle_scan)
    
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

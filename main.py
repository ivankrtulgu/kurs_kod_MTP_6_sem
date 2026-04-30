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
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

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
    
    # 1. Set Modern Flat Style
    app.setStyle('Fusion')
    
    # 2. Define Eco-Palette for a modern Windows 11 look
    palette = QPalette()
    
    # Light background colors
    palette.setColor(QPalette.Window, QColor("#f5f9f6"))
    palette.setColor(QPalette.WindowText, QColor("#2d3748"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f0fff4"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#2d3748"))
    
    # Accent colors (Sage Green)
    palette.setColor(QPalette.Highlight, QColor("#68a385"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    
    # Other colors
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#4a5568"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Link, QColor("#3182ce"))
    palette.setColor(QPalette.PlaceholderText, QColor("#a0aec0"))
    
    app.setPalette(palette)
    app.setApplicationName("Библиотека OCR")
    app.setOrganizationName("LibraryOCR")
    
    # 1. Infrastructure Layer
    # DatabaseManager requires the path to the .db file
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

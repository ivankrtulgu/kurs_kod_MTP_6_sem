
# library_app/ui/style_manager.py

class StyleManager:
    """
    Central manager for the 'Eco-Style' theme of the application.
    Provides a unified QSS stylesheet to ensure consistency across all windows.
    """
    
    ECO_STYLE_SHEET = """
        QMainWindow {
            background-color: #f5f9f6;
        }
        QWidget {
            background-color: #f5f9f6;
            color: #2d3748;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: 600;
            color: #4a5568;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 16px;
            padding: 0 8px;
            color: #68a385;
        }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px 20px;
            color: #4a5568;
            font-weight: 500;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #f0fff4;
            border-color: #68a385;
            color: #68a385;
        }
        QPushButton:pressed {
            background-color: #e8f5e9;
            border-color: #4a9f6e;
        }
        QPushButton:disabled {
            background-color: #f7fafc;
            border-color: #e2e8f0;
            color: #cbd5e0;
        }
        QComboBox {
            padding: 8px 12px;
            background-color: #ffffff;
            color: #4a5568;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            font-size: 13px;
        }
        QComboBox:hover {
            border-color: #68a385;
        }
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #68a385;
            margin-right: 8px;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            selection-background-color: #f0fff4;
            selection-color: #68a385;
            outline: none;
            padding: 4px;
        }
        QComboBox QAbstractItemView::item {
            padding: 8px 12px;
            border-radius: 6px;
            margin: 2px;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #f0fff4;
        }
        QSlider::groove:horizontal {
            background: #e2e8f0;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #68a385;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::handle:horizontal:hover {
            background: #4a9f6e;
        }
        QSlider::sub-page:horizontal {
            background: #68a385;
            border-radius: 3px;
        }
        QLabel {
            color: #4a5568;
            font-size: 13px;
        }
        QMenu {
            background-color: #ffffff;
            color: #2d3748;
            border: 1px solid #e2e8f0;
            padding: 4px;
        }
        QMenu::item {
            padding: 8px 24px 8px 20px;
            background-color: transparent;
            color: #2d3748;
        }
        QMenu::item:selected {
            background-color: #f0fff4;
            color: #68a385;
        }
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            gridline-color: #f0f4f1;
            font-size: 12px;
        }
        QTableWidget::item {
            padding: 8px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: #f0fff4;
            color: #68a385;
        }
        QHeaderView::section {
            background-color: #f8faf9;
            color: #68a385;
            font-weight: 600;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e2e8f0;
            border-radius: 0;
        }
        QScrollArea {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background-color: #ffffff;
        }
        QMessageBox {
            background-color: #ffffff;
        }
        QMessageBox QLabel {
            color: #4a5568;
        }
        QMessageBox QPushButton {
            min-width: 80px;
        }
    """

    @classmethod
    def get_stylesheet(cls) -> str:
        """Returns the global Eco-Style stylesheet."""
        return cls.ECO_STYLE_SHEET

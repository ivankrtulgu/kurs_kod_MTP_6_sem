# ui/icon_manager.py
"""Icon manager for the application."""

from pathlib import Path
from PyQt5.QtGui import QIcon


class IconManager:
    """Manages application icons."""

    _RESOURCES_DIR = Path(__file__).parent.parent / "resources" / "icons"
    _DEFAULT_ICON = "icon-open-book.png"

    @classmethod
    def get_icon(cls, icon_name: str = None) -> QIcon:
        """
        Get an icon by name.

        Args:
            icon_name: Name of the icon file (e.g., "icon-open-book.png").
                      If None, returns the default application icon.

        Returns:
            QIcon object, or empty QIcon if file doesn't exist.
        """
        if icon_name is None:
            icon_name = cls._DEFAULT_ICON

        icon_path = cls._RESOURCES_DIR / icon_name

        if icon_path.exists():
            return QIcon(str(icon_path))

        return QIcon()

    @classmethod
    def get_default_icon(cls) -> QIcon:
        """Get the default application icon."""
        return cls.get_icon(cls._DEFAULT_ICON)

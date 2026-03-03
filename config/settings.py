"""Application settings module."""

import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    """Application settings loaded from .env file."""

    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", BASE_DIR / "library.db"))
    RESOURCES_PATH: Path = Path(os.getenv("RESOURCES_PATH", BASE_DIR / "resources"))
    TEMP_PATH: Path = Path(os.getenv("TEMP_PATH", BASE_DIR / "temp"))

    @classmethod
    def ensure_dirs(cls) -> None:
        """Ensure all configured directories exist."""
        cls.RESOURCES_PATH.mkdir(parents=True, exist_ok=True)
        cls.TEMP_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()

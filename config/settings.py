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

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/library_db")
    RESOURCES_PATH: Path = Path(os.getenv("RESOURCES_PATH", BASE_DIR / "resources"))
    TEMP_PATH: Path = Path(os.getenv("TEMP_PATH", BASE_DIR / "temp"))
    QR_SALT: str = os.getenv("QR_SALT", "lib_unique_salt_2026")

    @classmethod
    def ensure_dirs(cls) -> None:
        """Ensure all configured directories exist."""
        cls.RESOURCES_PATH.mkdir(parents=True, exist_ok=True)
        cls.TEMP_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()

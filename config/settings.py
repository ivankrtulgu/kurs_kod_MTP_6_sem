"""Application settings module."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Determine base directory
# When running as PyInstaller bundle, use the directory where the EXE is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent.parent

# Load .env file from the directory where EXE is located
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # .env file is required - fail with clear error
    raise RuntimeError(
        f"Configuration error: .env file not found!\n"
        f"Expected location: {env_path}\n"
        f"Please create .env file with required settings:\n"
        f"  DATABASE_URL=postgresql://user:password@host:port/database\n"
        f"  RESOURCES_PATH=resources\n"
        f"  TEMP_PATH=temp\n"
        f"  QR_SALT=your_salt_here"
    )


class Settings:
    """Application settings loaded from .env file."""

    def __init__(self):
        # Required settings - must be in .env
        self.DATABASE_URL: str = os.getenv("DATABASE_URL")
        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not set in .env file!\n"
                "Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/library_db"
            )

        # Optional settings with defaults
        self.RESOURCES_PATH: Path = Path(os.getenv("RESOURCES_PATH", BASE_DIR / "resources"))
        self.TEMP_PATH: Path = Path(os.getenv("TEMP_PATH", BASE_DIR / "temp"))
        self.QR_SALT: str = os.getenv("QR_SALT", "lib_unique_salt_2026")
        self.TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", "")  # Empty string means auto-detect

        # Ensure directories exist
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        """Ensure all configured directories exist."""
        self.RESOURCES_PATH.mkdir(parents=True, exist_ok=True)
        self.TEMP_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()

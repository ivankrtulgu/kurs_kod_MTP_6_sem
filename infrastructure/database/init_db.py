"""Скрипт инициализации базы данных."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "postgres_schema.sql"


def init_database() -> None:
    """Инициализировать базу данных со схемой."""
    with PostgresDatabaseManager(settings.DATABASE_URL).get_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = f.read()
        
        with conn.cursor() as cursor:
            cursor.execute(schema)
        conn.commit()
    
    print(f"[OK] База данных инициализирована с использованием PostgreSQL")


if __name__ == "__main__":
    init_database()

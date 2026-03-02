"""Скрипт инициализации базы данных."""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
DB_PATH = BASE_DIR.parent.parent / "library.db"


def init_database(db_path: Path | None = None) -> None:
    """Инициализировать базу данных со схемой.
    
    Args:
        db_path: Путь к файлу БД. По умолчанию - library.db в корне проекта.
    """
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    
    conn.executescript(schema)
    conn.commit()
    conn.close()
    
    print(f"[OK] База данных создана: {db_path.absolute()}")


if __name__ == "__main__":
    init_database()

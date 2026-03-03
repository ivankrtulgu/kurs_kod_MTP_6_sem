"""Database migration script."""

import logging
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.database.connection import DatabaseManager

logger = logging.getLogger(__name__)

CURRENT_VERSION = 1


def create_schema_versions_table(conn: sqlite3.Connection) -> None:
    """Create schema_versions table if not exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_applied_versions(conn: sqlite3.Connection) -> set[int]:
    """Get list of applied migration versions."""
    cursor = conn.execute("SELECT version FROM schema_versions")
    return {row[0] for row in cursor.fetchall()}


def apply_migration(conn: sqlite3.Connection, version: int, sql: str) -> None:
    """Apply a single migration."""
    conn.executescript(sql)
    conn.execute(
        "INSERT INTO schema_versions (version) VALUES (?)",
        (version,)
    )
    conn.commit()
    logger.info(f"Migration v{version} applied")


def migrate(db_manager: DatabaseManager, schema_path: Path) -> None:
    """
    Run database migrations.
    
    Args:
        db_manager: Database connection manager.
        schema_path: Path to schema.sql file.
    """
    with db_manager.get_connection() as conn:
        create_schema_versions_table(conn)
        applied = get_applied_versions(conn)

        if CURRENT_VERSION not in applied:
            logger.info(f"Applying migration v{CURRENT_VERSION}")
            
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            
            apply_migration(conn, CURRENT_VERSION, schema_sql)
            logger.info(f"Database migrated to version {CURRENT_VERSION}")
        else:
            logger.info(f"Database is up to date (v{CURRENT_VERSION})")


def run_migrations(db_path: str | Path, schema_path: str | Path) -> None:
    """
    Run migrations from command line.
    
    Args:
        db_path: Path to database file.
        schema_path: Path to schema.sql file.
    """
    db_path = Path(db_path)
    schema_path = Path(schema_path)

    if not db_path.exists():
        logger.info(f"Creating new database: {db_path}")

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    db_manager = DatabaseManager(db_path)
    migrate(db_manager, schema_path)
    print(f"[OK] Database migrated: {db_path}")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    SCHEMA_PATH = BASE_DIR / "schema.sql"
    DB_PATH = BASE_DIR.parent.parent / "library.db"

    run_migrations(DB_PATH, SCHEMA_PATH)

"""Database migration script."""

import logging
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager

logger = logging.getLogger(__name__)

CURRENT_VERSION = 2


def create_schema_versions_table(conn) -> None:
    """Create schema_versions table if not exists."""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version SERIAL PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()


def get_applied_versions(conn) -> set[int]:
    """Get list of applied migration versions."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_versions")
        return {row['version'] for row in cursor.fetchall()}


def apply_migration(conn, version: int, sql: str) -> None:
    """Apply a single migration."""
    with conn.cursor() as cursor:
        cursor.execute(sql)
        cursor.execute(
            "INSERT INTO schema_versions (version) VALUES (%s)",
            (version,)
        )
    conn.commit()
    logger.info(f"Migration v{version} applied")


def migrate(db_manager: PostgresDatabaseManager, schema_path: Path) -> None:
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


def run_migrations(schema_path: str | Path) -> None:
    """
    Run migrations from command line.
    
    Args:
        schema_path: Path to schema.sql file.
    """
    schema_path = Path(schema_path)

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    db_manager = PostgresDatabaseManager(settings.DATABASE_URL)
    migrate(db_manager, schema_path)
    print(f"[OK] Database migrated using PostgreSQL")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    SCHEMA_PATH = BASE_DIR / "postgres_schema.sql"

    run_migrations(SCHEMA_PATH)

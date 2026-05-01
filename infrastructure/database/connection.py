"""Database connection manager module."""

import logging
import sqlite3
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)


class SQLiteDatabaseManager:
    """
    Manager for SQLite database connections.
    
    Provides context manager for safe connection handling.
    """

    def __init__(self, db_path: str | Path) -> None:
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get database connection context manager.
        
        Yields:
            sqlite3.Connection: Database connection.
            
        Raises:
            sqlite3.DatabaseError: On connection errors.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            logger.debug(f"Connected to database: {self.db_path}")
            yield conn
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")


class PostgresDatabaseManager:
    """
    Manager for PostgreSQL database connections.
    
    Provides context manager for safe connection handling.
    """

    def __init__(self, db_url: str) -> None:
        """
        Initialize database manager.
        
        Args:
            db_url: Connection URL for PostgreSQL database.
        """
        self.db_url = db_url

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get database connection context manager.
        
        Yields:
            psycopg2.extensions.connection: Database connection.
            
        Raises:
            psycopg2.DatabaseError: On connection errors.
        """
        conn = None
        try:
            conn = psycopg2.connect(self.db_url, cursor_factory=psycopg2.extras.RealDictCursor)
            logger.debug("Connected to PostgreSQL database")
            yield conn
        except psycopg2.DatabaseError as e:
            logger.error(f"PostgreSQL database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("PostgreSQL database connection closed")

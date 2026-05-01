import pytest
import psycopg2
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager
from infrastructure.database.init_db import init_database

# Use a dedicated test database if possible, otherwise use the main one
# In a real scenario, we would use a separate TEST_DATABASE_URL
TEST_DB_URL = settings.DATABASE_URL

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize the database schema once per session."""
    init_database()

@pytest.fixture
def db_manager():
    """Provide a PostgresDatabaseManager instance."""
    return PostgresDatabaseManager(TEST_DB_URL)

@pytest.fixture
def db_connection():
    """
    Provide a database connection that is rolled back after each test.
    This ensures tests are isolated and don't pollute the database.
    """
    import psycopg2.extras
    conn = psycopg2.connect(TEST_DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    try:
        # Clear tables before each test
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE loan_records, book_items, readers, books RESTART IDENTITY CASCADE")
        conn.commit()
        yield conn
    finally:
        conn.rollback()
        conn.close()

@pytest.fixture
def mock_db_manager(db_connection):
    """
    A mock DatabaseManager that returns the controlled test connection.
    """
    class MockManager:
        def get_connection(self):
            from contextlib import contextmanager
            @contextmanager
            def _get():
                yield db_connection
            return _get()
    
    return MockManager()

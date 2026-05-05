import pytest
import psycopg2
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager
from infrastructure.database.init_db import init_database

# Use a dedicated test database if possible, otherwise use the main one
# In a real scenario, we would use a separate TEST_DATABASE_URL
TEST_DB_URL = settings.DATABASE_URL


# ===== PYTEST CONFIGURATION =====

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests requiring Qt"
    )


# ===== DATABASE FIXTURES =====

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


# ===== QT FIXTURES =====

@pytest.fixture(scope="session")
def qapp_args():
    """Arguments for QApplication."""
    return []


@pytest.fixture(scope="session")
def qapp_cls():
    """QApplication class to use."""
    from PyQt5.QtWidgets import QApplication
    return QApplication


# ===== TEMPORARY DIRECTORY FIXTURES =====

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def temp_resources_dir(tmp_path, monkeypatch):
    """Provide a temporary resources directory and configure settings."""
    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()

    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()

    monkeypatch.setattr(settings, 'RESOURCES_PATH', resources_dir)
    monkeypatch.setattr(settings, 'TEMP_PATH', temp_dir)

    return resources_dir


# ===== HELPER FIXTURES =====

@pytest.fixture
def sample_book_data():
    """Provide sample book data for testing."""
    return {
        "author": "Иванов И.И.",
        "title": "Тестовая книга",
        "place": "Москва",
        "publisher": "Наука",
        "year": 2024,
        "pages": 200,
        "isbn": "978-5-699-12345-2"
    }


@pytest.fixture
def sample_reader_data():
    """Provide sample reader data for testing."""
    return {
        "last_name": "Петров",
        "first_name": "Петр",
        "middle_name": "Петрович",
        "phone": "+7 (999) 123-45-67",
        "email": "petrov@example.com",
        "home_address": "ул. Тестовая, д. 1"
    }


# ===== CLEANUP FIXTURES =====

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Cleanup temporary files after each test."""
    yield
    # Cleanup is automatic with tmp_path


# ===== ENVIRONMENT FIXTURES =====

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    monkeypatch.setenv("QR_SALT", "test_salt")
    return monkeypatch

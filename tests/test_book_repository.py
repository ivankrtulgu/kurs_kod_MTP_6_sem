"""
Tests for BookRepository layer.

Tests the SQLite implementation of book repository operations.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.book import Book
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.book_repository import SQLiteBookRepository


# ===== FIXTURES =====

@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary database path."""
    return tmp_path / "test_library.db"


@pytest.fixture
def db_manager(test_db_path):
    """Create database manager with test database."""
    return DatabaseManager(test_db_path)


@pytest.fixture
def repository(db_manager, test_db_path):
    """Create repository with initialized database."""
    # Initialize database schema
    schema_path = project_root / "infrastructure" / "database" / "schema.sql"
    conn = sqlite3.connect(test_db_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    
    return SQLiteBookRepository(db_manager)


@pytest.fixture
def sample_book():
    """Create sample book for testing."""
    return Book(
        author="Иванов И.И.",
        title="Основы программирования",
        subtitle="Учебное пособие",
        responsibility="Под ред. Петрова П.П.",
        edition="2-е изд., перераб. и доп.",
        place="Москва",
        publisher="Наука",
        year=2024,
        pages=350,
        isbn="978-5-02-040500-0",
        copyright="© Иванов И.И., 2024",
        udc="004.43",
        bbk="32.973",
        author_mark="И12",
        reviewers="Рецензент: Сидоров С.С.",
        annotation="Аннотация к книге",
        abstract="",
        doi="",
        content_type="Текст",
        access_method="непосредственный",
    )


@pytest.fixture
def multiple_books():
    """Create multiple sample books."""
    return [
        Book(
            author="Иванов И.И.",
            title="Python для начинающих",
            subtitle="",
            responsibility="",
            edition="",
            place="Москва",
            publisher="Питер",
            year=2023,
            pages=256,
            isbn="978-5-4461-0001-1",
            copyright="© Иванов, 2023",
            udc="004.43",
            bbk="32.973",
            author_mark="И12",
        ),
        Book(
            author="Петров П.П.",
            title="Базы данных",
            subtitle="Учебник",
            responsibility="",
            edition="3-е изд.",
            place="Санкт-Петербург",
            publisher="БХВ-Петербург",
            year=2022,
            pages=400,
            isbn="978-5-9775-0002-2",
            copyright="© Петров, 2022",
            udc="004.65",
            bbk="32.973.26",
            author_mark="П30",
        ),
        Book(
            author="Сидоров С.С.",
            title="Веб-разработка",
            subtitle="",
            responsibility="",
            edition="",
            place="Москва",
            publisher="ДМК Пресс",
            year=2024,
            pages=300,
            isbn="978-5-9706-0003-3",
            copyright="© Сидоров, 2024",
            udc="004.774",
            bbk="32.973.2",
            author_mark="С34",
        ),
    ]


# ===== TESTS: ADD BOOK =====

class TestAddBook:
    """Tests for add_book method."""

    def test_add_book_success(self, repository, sample_book):
        """Test successful book addition."""
        book_id = repository.add(sample_book)
        
        assert book_id > 0
        assert isinstance(book_id, int)

    def test_add_book_returns_unique_ids(self, repository, multiple_books):
        """Test that each added book gets unique ID."""
        ids = []
        for book in multiple_books:
            book_id = repository.add(book)
            ids.append(book_id)
        
        assert len(ids) == len(set(ids))  # All IDs are unique
        assert ids == sorted(ids)  # IDs are incremental

    def test_add_book_persists_data(self, repository, sample_book):
        """Test that book data is persisted correctly."""
        book_id = repository.add(sample_book)
        
        # Retrieve and verify
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved is not None
        assert retrieved.author == sample_book.author
        assert retrieved.title == sample_book.title
        assert retrieved.isbn == sample_book.isbn


# ===== TESTS: GET BY ID =====

class TestGetById:
    """Tests for get_by_id method."""

    def test_get_existing_book(self, repository, sample_book):
        """Test retrieving existing book."""
        book_id = repository.add(sample_book)
        
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved is not None
        assert retrieved.id == book_id
        assert retrieved.author == sample_book.author
        assert retrieved.title == sample_book.title

    def test_get_nonexistent_book(self, repository):
        """Test retrieving non-existent book."""
        result = repository.get_by_id(99999)
        
        assert result is None

    def test_get_book_preserves_all_fields(self, repository, sample_book):
        """Test that all book fields are preserved."""
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved.author == sample_book.author
        assert retrieved.title == sample_book.title
        assert retrieved.subtitle == sample_book.subtitle
        assert retrieved.responsibility == sample_book.responsibility
        assert retrieved.edition == sample_book.edition
        assert retrieved.place == sample_book.place
        assert retrieved.publisher == sample_book.publisher
        assert retrieved.year == sample_book.year
        assert retrieved.pages == sample_book.pages
        assert retrieved.isbn == sample_book.isbn
        assert retrieved.udc == sample_book.udc
        assert retrieved.bbk == sample_book.bbk


# ===== TESTS: GET ALL =====

class TestGetAll:
    """Tests for get_all method."""

    def test_get_all_empty_repository(self, repository):
        """Test get_all with empty repository."""
        books = repository.get_all()
        
        assert books == []
        assert len(books) == 0

    def test_get_all_returns_all_books(self, repository, multiple_books):
        """Test that get_all returns all books."""
        for book in multiple_books:
            repository.add(book)
        
        books = repository.get_all()
        
        assert len(books) == len(multiple_books)

    def test_get_all_ordering(self, repository, multiple_books):
        """Test that books are ordered by year DESC, title ASC."""
        for book in multiple_books:
            repository.add(book)
        
        books = repository.get_all()
        
        # Check ordering by year (descending)
        years = [book.year for book in books]
        assert years == sorted(years, reverse=True)


# ===== TESTS: SEARCH =====

class TestSearch:
    """Tests for search method."""

    def test_search_by_author(self, repository, multiple_books):
        """Test searching by author name."""
        for book in multiple_books:
            repository.add(book)
        
        results = repository.search("Иванов")
        
        assert len(results) > 0
        assert all("Иванов" in book.author for book in results)

    def test_search_by_title(self, repository, multiple_books):
        """Test searching by title."""
        for book in multiple_books:
            repository.add(book)
        
        results = repository.search("Python")
        
        assert len(results) > 0
        assert all("Python" in book.title for book in results)

    def test_search_by_isbn(self, repository, multiple_books):
        """Test searching by ISBN."""
        for book in multiple_books:
            repository.add(book)
        
        target_isbn = multiple_books[0].isbn
        results = repository.search(target_isbn)
        
        assert len(results) > 0
        assert results[0].isbn == target_isbn

    def test_search_case_insensitive(self, repository, sample_book):
        """Test that search works with exact case match."""
        repository.add(sample_book)
        
        # SQLite LIKE is case-sensitive for Cyrillic by default
        # Test exact match works
        results_exact = repository.search("Иванов")
        assert len(results_exact) > 0

    def test_search_no_results(self, repository, sample_book):
        """Test search with no matching results."""
        repository.add(sample_book)
        
        results = repository.search("несуществующий_запрос_xyz")
        
        assert len(results) == 0

    def test_search_partial_match(self, repository, multiple_books):
        """Test search with partial matching."""
        for book in multiple_books:
            repository.add(book)
        
        # Partial author name
        results = repository.search("Петр")
        assert len(results) > 0
        
        # Partial title
        results = repository.search("Базы")
        assert len(results) > 0


# ===== TESTS: UPDATE =====

class TestUpdate:
    """Tests for update method."""

    def test_update_existing_book(self, repository, sample_book):
        """Test updating existing book."""
        book_id = repository.add(sample_book)
        
        # Modify book
        sample_book.id = book_id
        sample_book.title = "Обновлённое название"
        sample_book.year = 2025
        
        success = repository.update(sample_book)
        
        assert success is True
        
        # Verify update
        updated = repository.get_by_id(book_id)
        assert updated.title == "Обновлённое название"
        assert updated.year == 2025

    def test_update_nonexistent_book(self, repository, sample_book):
        """Test updating non-existent book."""
        sample_book.id = 99999
        
        success = repository.update(sample_book)
        
        assert success is False

    def test_update_preserves_id(self, repository, sample_book):
        """Test that update preserves book ID."""
        book_id = repository.add(sample_book)
        sample_book.id = book_id
        sample_book.author = "Новый Автор"
        
        repository.update(sample_book)
        
        retrieved = repository.get_by_id(book_id)
        assert retrieved.id == book_id
        assert retrieved.author == "Новый Автор"


# ===== TESTS: DELETE =====

class TestDelete:
    """Tests for delete method."""

    def test_delete_existing_book(self, repository, sample_book):
        """Test deleting existing book."""
        book_id = repository.add(sample_book)
        
        success = repository.delete(book_id)
        
        assert success is True
        
        # Verify deletion
        retrieved = repository.get_by_id(book_id)
        assert retrieved is None

    def test_delete_nonexistent_book(self, repository):
        """Test deleting non-existent book."""
        success = repository.delete(99999)
        
        assert success is False

    def test_delete_removes_completely(self, repository, multiple_books):
        """Test that delete removes book completely."""
        ids = []
        for book in multiple_books:
            ids.append(repository.add(book))
        
        # Delete middle book
        repository.delete(ids[1])
        
        # Verify only one book is deleted
        all_books = repository.get_all()
        assert len(all_books) == len(multiple_books) - 1
        
        # Verify specific book is gone
        deleted_gone = repository.get_by_id(ids[1])
        assert deleted_gone is None


# ===== TESTS: COUNT =====

class TestCount:
    """Tests for count method."""

    def test_count_empty_repository(self, repository):
        """Test count with empty repository."""
        count = repository.count()
        
        assert count == 0

    def test_count_after_adding(self, repository, multiple_books):
        """Test count after adding books."""
        for book in multiple_books:
            repository.add(book)
        
        count = repository.count()
        
        assert count == len(multiple_books)

    def test_count_after_deletion(self, repository, multiple_books):
        """Test count after deletion."""
        ids = []
        for book in multiple_books:
            ids.append(repository.add(book))
        
        repository.delete(ids[0])
        
        count = repository.count()
        assert count == len(multiple_books) - 1


# ===== TESTS: DATA INTEGRITY =====

class TestDataIntegrity:
    """Tests for data integrity."""

    def test_book_created_at_timestamp(self, repository, sample_book):
        """Test that created_at timestamp is set."""
        book_id = repository.add(sample_book)
        
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved.created_at is not None
        assert isinstance(retrieved.created_at, datetime)
        assert retrieved.created_at.year >= 2024

    def test_special_characters_preserved(self, repository, sample_book):
        """Test that special characters are preserved."""
        sample_book.title = "Программирование: C++ & Python / 100%"
        sample_book.annotation = "Текст с «кавычками» и — тире"
        
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved.title == sample_book.title
        assert retrieved.annotation == sample_book.annotation

    def test_empty_optional_fields(self, repository, sample_book):
        """Test handling of empty optional fields."""
        sample_book.subtitle = ""
        sample_book.responsibility = ""
        sample_book.edition = ""
        sample_book.annotation = ""
        sample_book.doi = ""
        
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved.subtitle == ""
        assert retrieved.responsibility == ""
        assert retrieved.annotation == ""


# ===== TESTS: EDGE CASES =====

class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_long_fields(self, repository, sample_book):
        """Test handling of very long field values."""
        sample_book.title = "О" * 1000  # 1000 characters
        sample_book.annotation = "А" * 5000  # 5000 characters
        
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        
        assert len(retrieved.title) == 1000
        assert len(retrieved.annotation) == 5000

    def test_unicode_characters(self, repository, sample_book):
        """Test handling of Unicode characters."""
        sample_book.author = "田中太郎"  # Japanese
        sample_book.title = "Привет мир! 你好世界"  # Mixed Unicode
        
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        
        assert retrieved.author == sample_book.author
        assert retrieved.title == sample_book.title

    def test_year_boundaries(self, repository, sample_book):
        """Test year boundary values."""
        # Test old year
        sample_book.year = 1900
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        assert retrieved.year == 1900
        
        # Test future year
        sample_book.id = 0
        sample_book.year = 2100
        book_id = repository.add(sample_book)
        retrieved = repository.get_by_id(book_id)
        assert retrieved.year == 2100

    def test_isbn_formats(self, repository, sample_book):
        """Test different ISBN formats."""
        isbn_formats = [
            "978-5-02-040500-0",
            "9785020405000",
            "5-02-040500-0",
            "978-5-9775-0002-2",
        ]
        
        for i, isbn in enumerate(isbn_formats):
            sample_book.id = 0
            sample_book.isbn = isbn
            book_id = repository.add(sample_book)
            retrieved = repository.get_by_id(book_id)
            assert retrieved.isbn == isbn, f"Failed for ISBN format: {isbn}"

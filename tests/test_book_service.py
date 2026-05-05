"""
Tests for BookService layer (business logic).

Tests the service layer including validation, ISBN validation,
and file operations.
"""

import pytest
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.book import Book
from core.services.book_service import (
    BookService,
    ISBNValidator,
    ValidationError,
    BookServiceError,
    FileOperationError
)
from config.settings import settings
from infrastructure.database.connection import PostgresDatabaseManager


# ===== FIXTURES =====

@pytest.fixture
def test_resources_path(tmp_path):
    """Create temporary resources path."""
    resources = tmp_path / "resources"
    resources.mkdir()
    return resources


@pytest.fixture
def book_service(test_resources_path, monkeypatch, mock_db_manager):
    """Create book service with test configuration."""
    # Monkeypatch settings
    monkeypatch.setattr(settings, 'RESOURCES_PATH', test_resources_path)
    
    return BookService(db_manager=mock_db_manager)


@pytest.fixture
def sample_book():
    """Create sample book for testing with required fields only per GOST R 7.0.4-2020."""
    return Book(
        author="Иванов И.И.",
        title="Основы программирования",
        place="Москва",
        publisher="Наука",
        year=2024,
        pages=350,
        isbn="978-5-699-12345-2",  # Valid ISBN-13 with correct check digit
        # Optional fields
        subtitle="Учебное пособие",
        responsibility="Под ред. Петрова П.П.",
        edition="2-е изд., перераб. и доп.",
        copyright="© Иванов И.И., 2024",
        udc="004.43",
        bbk="32.973",
        author_mark="И12",
        # Additional fields
        reviewers="Рецензент: Сидоров С.С.",
        annotation="Аннотация к книге",
        abstract="Краткое содержание",
        doi="",
        content_type="Текст",
        access_method="непосредственный",
    )


@pytest.fixture
def sample_cover_image(tmp_path):
    """Create a sample cover image file."""
    # Create a minimal PNG file (1x1 pixel)
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixel
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    image_path = tmp_path / "test_cover.png"
    image_path.write_bytes(png_data)
    return image_path


# ===== TESTS: SERVICE INITIALIZATION =====

class TestServiceInitialization:
    """Tests for BookService initialization."""

    def test_service_creates_directories(self, tmp_path, monkeypatch, mock_db_manager):
        """Test that service ensures directories exist."""
        monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path / "resources")
        monkeypatch.setattr(settings, 'TEMP_PATH', tmp_path / "temp")
        
        service = BookService(db_manager=mock_db_manager)
        assert service is not None

    def test_service_initializes_repository(self, book_service):
        """Test that service initializes repository."""
        assert book_service is not None
        assert hasattr(book_service, '_repository')


# ===== TESTS: ADD BOOK =====

class TestAddBook:
    """Tests for add_book method."""

    def test_add_book_success(self, book_service, sample_book):
        """Test successful book addition."""
        book_id = book_service.add_book(sample_book)
        
        assert book_id > 0
        assert isinstance(book_id, int)

    def test_add_book_copies_cover_image(self, book_service, sample_book, sample_cover_image):
        """Test that cover image is copied to resources."""
        sample_book.cover_image_path = str(sample_cover_image)
        
        book_id = book_service.add_book(sample_book)
        
        retrieved = book_service.get_book(book_id)
        assert retrieved.cover_image_path != str(sample_cover_image)
        assert Path(retrieved.cover_image_path).exists()
        assert 'covers' in retrieved.cover_image_path

    def test_add_book_with_empty_optional_fields(self, book_service, sample_book):
        """Test adding book with empty optional fields."""
        sample_book.subtitle = ""
        sample_book.responsibility = ""
        sample_book.edition = ""
        sample_book.annotation = ""
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_add_book_validation_error_empty_author(self, book_service, sample_book):
        """Test validation error for empty author."""
        sample_book.author = ""
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Автор обязателен" in str(exc_info.value)

    def test_add_book_validation_error_empty_title(self, book_service, sample_book):
        """Test validation error for empty title."""
        sample_book.title = ""
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Название обязательно" in str(exc_info.value)

    def test_add_book_validation_error_invalid_year(self, book_service, sample_book):
        """Test validation error for invalid year."""
        sample_book.year = 1800  # Before 1900
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Год должен быть в диапазоне 1900-2100" in str(exc_info.value)

    def test_add_book_validation_error_invalid_pages(self, book_service, sample_book):
        """Test validation error for invalid pages."""
        sample_book.pages = 0
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Количество страниц должно быть больше 0" in str(exc_info.value)

    def test_add_book_validation_error_invalid_isbn(self, book_service, sample_book):
        """Test validation error for invalid ISBN."""
        sample_book.isbn = "invalid-isbn"
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Недопустимый ISBN" in str(exc_info.value)

    def test_add_book_validation_error_empty_isbn(self, book_service, sample_book):
        """Test validation error for empty ISBN."""
        sample_book.isbn = ""
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "ISBN обязателен" in str(exc_info.value)

    def test_add_book_validation_error_empty_place(self, book_service, sample_book):
        """Test validation error for empty place."""
        sample_book.place = ""
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Место издания обязательно" in str(exc_info.value)

    def test_add_book_validation_error_empty_publisher(self, book_service, sample_book):
        """Test validation error for empty publisher."""
        sample_book.publisher = ""
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Издательство обязательно" in str(exc_info.value)

    def test_add_book_multiple_validation_errors(self, book_service, sample_book):
        """Test multiple validation errors at once."""
        sample_book.author = ""
        sample_book.title = ""
        sample_book.isbn = "invalid"
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        error_msg = str(exc_info.value)
        assert "Автор обязателен" in error_msg
        assert "Название обязательно" in error_msg
        assert "Недопустимый ISBN" in error_msg


# ===== TESTS: UPDATE BOOK =====

class TestUpdateBook:
    """Tests for update_book method."""

    def test_update_book_success(self, book_service, sample_book):
        """Test successful book update."""
        book_id = book_service.add_book(sample_book)
        
        # Modify book
        sample_book.id = book_id
        sample_book.title = "Обновлённое название"
        sample_book.year = 2025
        
        success = book_service.update_book(sample_book)
        assert success is True
        
        # Verify update
        updated = book_service.get_book(book_id)
        assert updated.title == "Обновлённое название"
        assert updated.year == 2025

    def test_update_book_validation_error(self, book_service, sample_book):
        """Test update with validation error."""
        book_id = book_service.add_book(sample_book)
        
        sample_book.id = book_id
        sample_book.author = ""
        
        with pytest.raises(ValidationError):
            book_service.update_book(sample_book)

    def test_update_nonexistent_book(self, book_service, sample_book):
        """Test updating non-existent book."""
        sample_book.id = 99999
        
        success = book_service.update_book(sample_book)
        assert success is False


# ===== TESTS: DELETE BOOK =====

class TestDeleteBook:
    """Tests for delete_book method."""

    def test_delete_book_success(self, book_service, sample_book):
        """Test successful book deletion."""
        book_id = book_service.add_book(sample_book)
        
        success = book_service.delete_book(book_id)
        assert success is True
        
        # Verify deletion
        retrieved = book_service.get_book(book_id)
        assert retrieved is None

    def test_delete_nonexistent_book(self, book_service):
        """Test deleting non-existent book."""
        success = book_service.delete_book(99999)
        assert success is False


# ===== TESTS: GET BOOK =====

class TestGetBook:
    """Tests for get_book method."""

    def test_get_existing_book(self, book_service, sample_book):
        """Test retrieving existing book."""
        book_id = book_service.add_book(sample_book)
        
        retrieved = book_service.get_book(book_id)
        
        assert retrieved is not None
        assert retrieved.id == book_id
        assert retrieved.author == sample_book.author

    def test_get_nonexistent_book(self, book_service):
        """Test retrieving non-existent book."""
        result = book_service.get_book(99999)
        assert result is None


# ===== TESTS: GET ALL BOOKS =====

class TestGetAllBooks:
    """Tests for get_all_books method."""

    def test_get_all_books_empty(self, book_service):
        """Test get all books with empty repository."""
        books = book_service.get_all_books()
        assert books == []

    def test_get_all_books_returns_all(self, book_service, sample_book):
        """Test that get all returns all books."""
        book_service.add_book(sample_book)
        book_service.add_book(sample_book)
        
        books = book_service.get_all_books()
        assert len(books) == 2


# ===== TESTS: SEARCH BOOKS =====

class TestSearchBooks:
    """Tests for search_books method."""

    def test_search_books_found(self, book_service, sample_book):
        """Test search returns matching books."""
        book_service.add_book(sample_book)
        
        results = book_service.search_books("Иванов")
        assert len(results) > 0

    def test_search_books_not_found(self, book_service, sample_book):
        """Test search with no results."""
        book_service.add_book(sample_book)
        
        results = book_service.search_books("несуществующий_автор")
        assert len(results) == 0


# ===== TESTS: COUNT BOOKS =====

class TestCountBooks:
    """Tests for count_books method."""

    def test_count_books_empty(self, book_service):
        """Test count with empty repository."""
        count = book_service.count_books()
        assert count == 0

    def test_count_books_after_adding(self, book_service, sample_book):
        """Test count after adding books."""
        book_service.add_book(sample_book)
        book_service.add_book(sample_book)
        
        count = book_service.count_books()
        assert count == 2

    def test_count_books_after_deletion(self, book_service, sample_book):
        """Test count after deletion."""
        book_id = book_service.add_book(sample_book)
        book_service.delete_book(book_id)
        
        count = book_service.count_books()
        assert count == 0


# ===== TESTS: ISBN VALIDATOR =====

class TestISBNValidatorInService:
    """Tests for ISBN validation within service context."""

    def test_service_rejects_invalid_isbn10(self, book_service, sample_book):
        """Test that service rejects invalid ISBN-10."""
        sample_book.isbn = "2-266-11156-5"  # Wrong check digit
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Недопустимый ISBN" in str(exc_info.value)

    def test_service_rejects_invalid_isbn13(self, book_service, sample_book):
        """Test that service rejects invalid ISBN-13."""
        sample_book.isbn = "978-5-02-040500-1"  # Wrong check digit
        
        with pytest.raises(ValidationError) as exc_info:
            book_service.add_book(sample_book)
        
        assert "Недопустимый ISBN" in str(exc_info.value)

    def test_service_accepts_valid_isbn10(self, book_service, sample_book):
        """Test that service accepts valid ISBN-10."""
        sample_book.isbn = "5-02-040500-0"
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_service_accepts_valid_isbn13(self, book_service, sample_book):
        """Test that service accepts valid ISBN-13."""
        sample_book.isbn = "978-5-699-12345-2"
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_service_accepts_isbn_with_x(self, book_service, sample_book):
        """Test that service accepts ISBN with X check digit."""
        sample_book.isbn = "0-8044-2957-X"
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0


# ===== TESTS: FILE OPERATIONS =====

class TestFileOperations:
    """Tests for file operations in service."""

    def test_copy_file_to_resources_success(self, book_service, sample_cover_image, test_resources_path):
        """Test successful file copy to resources."""
        covers_dir = test_resources_path / "covers"
        
        dest_path = book_service._copy_file_to_resources(
            str(sample_cover_image), "covers"
        )
        
        assert dest_path
        assert Path(dest_path).exists()
        assert 'covers' in dest_path

    def test_copy_file_to_resources_empty_path(self, book_service):
        """Test copy file with empty path."""
        result = book_service._copy_file_to_resources("", "covers")
        assert result == ""

    def test_copy_file_to_resources_nonexistent_file(self, book_service):
        """Test copy file that doesn't exist."""
        result = book_service._copy_file_to_resources(
            "/nonexistent/path/file.png", "covers"
        )
        assert result == ""

    def test_add_book_without_cover_image(self, book_service, sample_book):
        """Test adding book without cover image."""
        sample_book.cover_image_path = ""
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0
        
        retrieved = book_service.get_book(book_id)
        assert retrieved.cover_image_path == ""


# ===== TESTS: EDGE CASES =====

class TestServiceEdgeCases:
    """Tests for edge cases in service layer."""

    def test_add_book_whitespace_author(self, book_service, sample_book):
        """Test adding book with whitespace-only author."""
        sample_book.author = "   "
        
        with pytest.raises(ValidationError):
            book_service.add_book(sample_book)

    def test_add_book_whitespace_title(self, book_service, sample_book):
        """Test adding book with whitespace-only title."""
        sample_book.title = "   "
        
        with pytest.raises(ValidationError):
            book_service.add_book(sample_book)

    def test_add_book_year_boundary_1900(self, book_service, sample_book):
        """Test adding book with year 1900 (minimum valid)."""
        sample_book.year = 1900
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_add_book_year_boundary_2100(self, book_service, sample_book):
        """Test adding book with year 2100 (maximum valid)."""
        sample_book.year = 2100
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_add_book_year_below_boundary(self, book_service, sample_book):
        """Test adding book with year below minimum."""
        sample_book.year = 1899
        
        with pytest.raises(ValidationError):
            book_service.add_book(sample_book)

    def test_add_book_year_above_boundary(self, book_service, sample_book):
        """Test adding book with year above maximum."""
        sample_book.year = 2101
        
        with pytest.raises(ValidationError):
            book_service.add_book(sample_book)

    def test_add_book_pages_boundary(self, book_service, sample_book):
        """Test adding book with minimum pages (1)."""
        sample_book.pages = 1
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_add_book_isbn_with_spaces(self, book_service, sample_book):
        """Test adding book with ISBN containing spaces."""
        sample_book.isbn = "978 5 699 12345 2"
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0

    def test_add_book_special_characters_in_fields(self, book_service, sample_book):
        """Test adding book with special characters."""
        sample_book.title = "Программирование: C++ & Python / 100%"
        sample_book.annotation = "Текст с «кавычками» и — тире"
        
        book_id = book_service.add_book(sample_book)
        assert book_id > 0
        
        retrieved = book_service.get_book(book_id)
        assert retrieved.title == sample_book.title
        assert retrieved.annotation == sample_book.annotation

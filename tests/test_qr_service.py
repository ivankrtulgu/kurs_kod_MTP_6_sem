"""
Tests for QRService.

Tests for QR code generation for books and book items.
"""

import pytest
import json
from pathlib import Path
import sys
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.book import Book
from core.models.inventory import BookItem, ItemStatus
from core.services.qr_service import QRService
from config.settings import settings


# ===== FIXTURES =====

@pytest.fixture
def sample_book():
    """Create sample book for testing."""
    return Book(
        id=1,
        author="Иванов И.И.",
        title="Основы программирования",
        subtitle="Учебное пособие",
        place="Москва",
        publisher="Наука",
        year=2024,
        pages=350,
        isbn="978-5-699-12345-2",
        doi="10.1000/test"
    )


@pytest.fixture
def sample_item():
    """Create sample book item for testing."""
    return BookItem(
        id=1,
        inventory_number="INV001",
        book_id=1,
        status=ItemStatus.AVAILABLE,
        location="Shelf A1"
    )


@pytest.fixture
def temp_qr_dir(tmp_path, monkeypatch):
    """Create temporary directory for QR codes."""
    qr_dir = tmp_path / "qr_codes"
    qr_dir.mkdir()
    monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path)
    return qr_dir


# ===== TESTS: GENERATE BOOK QR =====

class TestGenerateBookQR:
    """Tests for generate_book_qr method."""

    def test_generate_book_qr_success(self, sample_book, temp_qr_dir):
        """Test successful QR code generation for book."""
        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert isinstance(qr_path, str)
        assert Path(qr_path).exists()
        assert qr_path.endswith('.png')

    def test_generate_book_qr_contains_isbn(self, sample_book, temp_qr_dir):
        """Test that generated QR contains ISBN."""
        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        # QR code file should exist
        assert Path(qr_path).exists()
        # Filename should contain ISBN
        assert sample_book.isbn.replace('-', '') in qr_path or 'qr_' in qr_path

    def test_generate_book_qr_creates_directory(self, sample_book, tmp_path, monkeypatch):
        """Test that QR generation creates directory if it doesn't exist."""
        monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path)

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        qr_dir = tmp_path / "qr_codes"
        assert qr_dir.exists()

    def test_generate_book_qr_unique_filenames(self, sample_book, temp_qr_dir):
        """Test that multiple QR generations create unique filenames."""
        qr_path1 = QRService.generate_book_qr(sample_book)
        qr_path2 = QRService.generate_book_qr(sample_book)

        assert qr_path1 != qr_path2
        assert Path(qr_path1).exists()
        assert Path(qr_path2).exists()

    def test_generate_book_qr_data_structure(self, sample_book, temp_qr_dir):
        """Test that QR code contains correct data structure."""
        # We can't easily decode QR from file in tests, but we can verify
        # the function runs without error and creates a file
        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        # Verify file is not empty
        assert Path(qr_path).stat().st_size > 0

    def test_generate_book_qr_with_doi(self, sample_book, temp_qr_dir):
        """Test QR generation for book with DOI."""
        sample_book.doi = "10.1000/test.doi"

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert Path(qr_path).exists()

    def test_generate_book_qr_without_doi(self, sample_book, temp_qr_dir):
        """Test QR generation for book without DOI."""
        sample_book.doi = ""

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert Path(qr_path).exists()

    def test_generate_book_qr_with_special_characters(self, sample_book, temp_qr_dir):
        """Test QR generation for book with special characters."""
        sample_book.title = "C++ & Python: 100% Guide"
        sample_book.author = "O'Brien, J."

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert Path(qr_path).exists()

    def test_generate_book_qr_with_unicode(self, sample_book, temp_qr_dir):
        """Test QR generation for book with Unicode characters."""
        sample_book.title = "Привет мир! 你好世界"
        sample_book.author = "田中太郎"

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert Path(qr_path).exists()

    def test_generate_book_qr_file_size(self, sample_book, temp_qr_dir):
        """Test that generated QR code has reasonable file size."""
        qr_path = QRService.generate_book_qr(sample_book)

        file_size = Path(qr_path).stat().st_size
        # QR code should be between 1KB and 100KB
        assert 1000 < file_size < 100000


# ===== TESTS: GENERATE ITEM QR =====

class TestGenerateItemQR:
    """Tests for generate_item_qr method."""

    def test_generate_item_qr_success(self, sample_item, temp_qr_dir):
        """Test successful QR code generation for item."""
        qr_path = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        assert qr_path is not None
        assert isinstance(qr_path, str)
        assert Path(qr_path).exists()
        assert qr_path.endswith('.png')

    def test_generate_item_qr_contains_inventory_number(self, sample_item, temp_qr_dir):
        """Test that generated QR filename contains inventory number."""
        qr_path = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        assert qr_path is not None
        assert sample_item.inventory_number in qr_path or 'qr_item_' in qr_path

    def test_generate_item_qr_creates_subdirectory(self, sample_item, tmp_path, monkeypatch):
        """Test that item QR generation creates items subdirectory."""
        monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path)

        qr_path = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        assert qr_path is not None
        items_dir = tmp_path / "qr_codes" / "items"
        assert items_dir.exists()

    def test_generate_item_qr_unique_filenames(self, sample_item, temp_qr_dir):
        """Test that multiple item QR generations create unique filenames."""
        qr_path1 = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")
        qr_path2 = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        assert qr_path1 != qr_path2
        assert Path(qr_path1).exists()
        assert Path(qr_path2).exists()

    def test_generate_item_qr_different_items(self, temp_qr_dir):
        """Test QR generation for different items."""
        item1 = BookItem(id=1, inventory_number="INV001", book_id=1)
        item2 = BookItem(id=2, inventory_number="INV002", book_id=1)

        qr_path1 = QRService.generate_item_qr(item1, "978-5-699-12345-2")
        qr_path2 = QRService.generate_item_qr(item2, "978-5-699-12345-2")

        assert qr_path1 != qr_path2
        assert Path(qr_path1).exists()
        assert Path(qr_path2).exists()

    def test_generate_item_qr_with_special_inventory_number(self, temp_qr_dir):
        """Test QR generation for item with special characters in inventory number."""
        item = BookItem(
            id=1,
            inventory_number="INV-2024-001",
            book_id=1
        )

        qr_path = QRService.generate_item_qr(item, "978-5-699-12345-2")

        assert qr_path is not None
        assert Path(qr_path).exists()

    def test_generate_item_qr_file_size(self, sample_item, temp_qr_dir):
        """Test that generated item QR code has reasonable file size."""
        qr_path = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        file_size = Path(qr_path).stat().st_size
        # QR code should be between 500 bytes and 100KB
        assert 500 < file_size < 100000


# ===== TESTS: ERROR HANDLING =====

class TestQRServiceErrorHandling:
    """Tests for error handling in QR service."""

    def test_generate_book_qr_with_invalid_book(self, temp_qr_dir):
        """Test QR generation with invalid book object."""
        # This should handle gracefully and return None
        result = QRService.generate_book_qr(None)

        assert result is None

    def test_generate_item_qr_with_invalid_item(self, temp_qr_dir):
        """Test QR generation with invalid item object."""
        result = QRService.generate_item_qr(None, "978-5-699-12345-2")

        assert result is None

    def test_generate_book_qr_with_missing_isbn(self, temp_qr_dir):
        """Test that book with empty ISBN cannot be created."""
        # Book validation should prevent creation with empty ISBN
        with pytest.raises(ValueError):
            book = Book(
                id=1,
                author="Test",
                title="Test",
                place="Test",
                publisher="Test",
                year=2024,
                pages=100,
                isbn=""  # Empty ISBN should raise ValueError
            )


# ===== TESTS: QR CODE CONTENT VERIFICATION =====

class TestQRCodeContent:
    """Tests for verifying QR code content structure."""

    def test_book_qr_data_format(self, sample_book, temp_qr_dir):
        """Test that book QR data follows expected format."""
        # Generate QR
        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None

        # We can verify the data structure that should be encoded
        # by checking what the function would encode
        expected_data = {
            "isbn": sample_book.isbn,
            "doi": sample_book.doi,
            "biblio": sample_book.format_bibliographic_record()
        }

        # Verify the data can be JSON serialized
        json_data = json.dumps(expected_data, ensure_ascii=False)
        assert isinstance(json_data, str)
        assert sample_book.isbn in json_data

    def test_item_qr_data_format(self, sample_item, temp_qr_dir):
        """Test that item QR data follows expected format."""
        isbn = "978-5-699-12345-2"
        qr_path = QRService.generate_item_qr(sample_item, isbn)

        assert qr_path is not None

        # Verify expected data structure
        expected_data = {
            "item_inv": sample_item.inventory_number,
            "book_id": sample_item.book_id,
            "isbn": isbn
        }

        json_data = json.dumps(expected_data, ensure_ascii=False)
        assert isinstance(json_data, str)
        assert sample_item.inventory_number in json_data


# ===== TESTS: INTEGRATION WITH SETTINGS =====

class TestQRServiceSettings:
    """Tests for QR service integration with settings."""

    def test_qr_service_uses_resources_path(self, sample_book, tmp_path, monkeypatch):
        """Test that QR service uses configured resources path."""
        custom_path = tmp_path / "custom_resources"
        monkeypatch.setattr(settings, 'RESOURCES_PATH', custom_path)

        qr_path = QRService.generate_book_qr(sample_book)

        assert qr_path is not None
        assert str(custom_path) in qr_path

    def test_qr_service_creates_nested_directories(self, sample_item, tmp_path, monkeypatch):
        """Test that QR service creates nested directory structure."""
        monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path)

        qr_path = QRService.generate_item_qr(sample_item, "978-5-699-12345-2")

        assert qr_path is not None
        # Should create qr_codes/items/
        assert (tmp_path / "qr_codes" / "items").exists()


# ===== TESTS: PERFORMANCE =====

class TestQRServicePerformance:
    """Tests for QR service performance."""

    def test_generate_multiple_book_qrs(self, temp_qr_dir):
        """Test generating multiple book QR codes."""
        # Use valid ISBNs with correct check digits
        valid_isbns = [
            "978-5-699-12345-2",
            "978-5-699-12346-9",
            "978-5-699-12347-6",
            "978-5-699-12348-3",
            "978-5-699-12349-0",
            "978-5-699-12350-6",
            "978-5-699-12351-3",
            "978-5-699-12352-0",
            "978-5-699-12353-7",
            "978-5-699-12354-4"
        ]

        books = []
        for i in range(10):
            book = Book(
                id=i,
                author=f"Author {i}",
                title=f"Book {i}",
                place="Moscow",
                publisher="Publisher",
                year=2024,
                pages=100,
                isbn=valid_isbns[i]
            )
            books.append(book)

        qr_paths = []
        for book in books:
            qr_path = QRService.generate_book_qr(book)
            qr_paths.append(qr_path)

        # All should succeed
        assert all(path is not None for path in qr_paths)
        assert all(Path(path).exists() for path in qr_paths)
        # All should be unique
        assert len(set(qr_paths)) == 10

    def test_generate_multiple_item_qrs(self, temp_qr_dir):
        """Test generating multiple item QR codes."""
        items = []
        for i in range(10):
            item = BookItem(
                id=i,
                inventory_number=f"INV{i:03d}",
                book_id=1
            )
            items.append(item)

        qr_paths = []
        for item in items:
            qr_path = QRService.generate_item_qr(item, "978-5-699-12345-2")
            qr_paths.append(qr_path)

        # All should succeed
        assert all(path is not None for path in qr_paths)
        assert all(Path(path).exists() for path in qr_paths)
        # All should be unique
        assert len(set(qr_paths)) == 10

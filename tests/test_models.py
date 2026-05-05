"""
Tests for core models.

Tests for Book, Reader, LoanRecord, BookItem models including
validation, methods, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.book import Book
from core.models.inventory import BookItem, Reader, LoanRecord, ItemStatus


# ===== BOOK MODEL TESTS =====

class TestBookModel:
    """Tests for Book model."""

    def test_book_creation_with_required_fields(self):
        """Test creating book with only required fields."""
        book = Book(
            author="Иванов И.И.",
            title="Тестовая книга",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        assert book.author == "Иванов И.И."
        assert book.title == "Тестовая книга"
        assert book.year == 2024
        assert book.pages == 100

    def test_book_creation_with_all_fields(self):
        """Test creating book with all fields."""
        book = Book(
            author="Иванов И.И.",
            title="Тестовая книга",
            subtitle="Учебное пособие",
            responsibility="Под ред. Петрова",
            edition="2-е изд.",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2",
            copyright="© 2024",
            udc="004.43",
            bbk="32.973",
            author_mark="И12",
            reviewers="Рецензент: Сидоров",
            annotation="Аннотация",
            abstract="Абстракт",
            doi="10.1000/test",
            content_type="Текст",
            access_method="непосредственный"
        )

        assert book.subtitle == "Учебное пособие"
        assert book.udc == "004.43"
        assert book.doi == "10.1000/test"

    def test_book_validation_empty_author(self):
        """Test validation fails for empty author."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="",
                title="Тестовая книга",
                place="Москва",
                publisher="Наука",
                year=2024,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "author" in str(exc_info.value).lower()

    def test_book_validation_empty_title(self):
        """Test validation fails for empty title."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="",
                place="Москва",
                publisher="Наука",
                year=2024,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "title" in str(exc_info.value).lower()

    def test_book_validation_invalid_year_too_low(self):
        """Test validation fails for year < 1900."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="Москва",
                publisher="Наука",
                year=1899,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "year" in str(exc_info.value).lower()
        assert "1900" in str(exc_info.value)

    def test_book_validation_invalid_year_too_high(self):
        """Test validation fails for year > 2100."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="Москва",
                publisher="Наука",
                year=2101,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "year" in str(exc_info.value).lower()
        assert "2100" in str(exc_info.value)

    def test_book_validation_invalid_pages(self):
        """Test validation fails for pages <= 0."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="Москва",
                publisher="Наука",
                year=2024,
                pages=0,
                isbn="978-5-699-12345-2"
            )

        assert "pages" in str(exc_info.value).lower()

    def test_book_validation_invalid_isbn(self):
        """Test validation fails for invalid ISBN."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="Москва",
                publisher="Наука",
                year=2024,
                pages=100,
                isbn="invalid-isbn"
            )

        assert "isbn" in str(exc_info.value).lower()

    def test_book_validation_empty_place(self):
        """Test validation fails for empty place."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="",
                publisher="Наука",
                year=2024,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "place" in str(exc_info.value).lower()

    def test_book_validation_empty_publisher(self):
        """Test validation fails for empty publisher."""
        with pytest.raises(ValueError) as exc_info:
            Book(
                author="Иванов И.И.",
                title="Тестовая книга",
                place="Москва",
                publisher="",
                year=2024,
                pages=100,
                isbn="978-5-699-12345-2"
            )

        assert "publisher" in str(exc_info.value).lower()

    def test_book_format_bibliographic_record_minimal(self):
        """Test formatting bibliographic record with minimal fields."""
        book = Book(
            author="Иванов И.И.",
            title="Основы программирования",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=350,
            isbn="978-5-699-12345-2"
        )

        record = book.format_bibliographic_record()

        assert "Иванов И.И." in record
        assert "Основы программирования" in record
        assert "Москва" in record
        assert "Наука" in record
        assert "2024" in record
        assert "350 с." in record
        assert "ISBN 978-5-699-12345-2" in record

    def test_book_format_bibliographic_record_full(self):
        """Test formatting bibliographic record with all fields."""
        book = Book(
            author="Иванов И.И.",
            title="Основы программирования",
            subtitle="Учебное пособие",
            responsibility="Под ред. Петрова П.П.",
            edition="2-е изд., перераб. и доп.",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=350,
            isbn="978-5-699-12345-2",
            udc="004.43",
            bbk="32.973",
            doi="10.1000/test"
        )

        record = book.format_bibliographic_record()

        assert "Учебное пособие" in record
        assert "Под ред. Петрова П.П." in record
        assert "2-е изд., перераб. и доп." in record
        assert "УДК 004.43" in record
        assert "ББК 32.973" in record
        assert "DOI 10.1000/test" in record

    def test_book_to_dict(self):
        """Test converting book to dictionary."""
        book = Book(
            author="Иванов И.И.",
            title="Тестовая книга",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        data = book.to_dict()

        assert isinstance(data, dict)
        assert data["author"] == "Иванов И.И."
        assert data["title"] == "Тестовая книга"
        assert data["year"] == 2024
        assert "created_at" in data

    def test_book_from_dict(self):
        """Test creating book from dictionary."""
        data = {
            "author": "Иванов И.И.",
            "title": "Тестовая книга",
            "place": "Москва",
            "publisher": "Наука",
            "year": 2024,
            "pages": 100,
            "isbn": "978-5-699-12345-2",
            "subtitle": "Подзаголовок"
        }

        book = Book.from_dict(data)

        assert book.author == "Иванов И.И."
        assert book.title == "Тестовая книга"
        assert book.subtitle == "Подзаголовок"

    def test_book_from_dict_with_datetime_string(self):
        """Test creating book from dict with datetime as string."""
        data = {
            "author": "Иванов И.И.",
            "title": "Тестовая книга",
            "place": "Москва",
            "publisher": "Наука",
            "year": 2024,
            "pages": 100,
            "isbn": "978-5-699-12345-2",
            "created_at": "2024-01-01T12:00:00"
        }

        book = Book.from_dict(data)

        assert isinstance(book.created_at, datetime)

    def test_book_str_representation(self):
        """Test string representation of book."""
        book = Book(
            author="Иванов И.И.",
            title="Тестовая книга",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        str_repr = str(book)

        assert "Иванов И.И." in str_repr
        assert "Тестовая книга" in str_repr
        assert "2024" in str_repr

    def test_book_default_values(self):
        """Test default values for optional fields."""
        book = Book(
            author="Иванов И.И.",
            title="Тестовая книга",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        assert book.subtitle == ""
        assert book.responsibility == ""
        assert book.edition == ""
        assert book.content_type == "Текст"
        assert book.access_method == "непосредственный"
        assert book.id == 0
        assert isinstance(book.created_at, datetime)


# ===== READER MODEL TESTS =====

class TestReaderModel:
    """Tests for Reader model."""

    def test_reader_creation_minimal(self):
        """Test creating reader with minimal fields."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван"
        )

        assert reader.last_name == "Иванов"
        assert reader.first_name == "Иван"
        assert reader.status == "active"

    def test_reader_creation_full(self):
        """Test creating reader with all fields."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
            birth_date="1990-01-01",
            phone="+7 (999) 123-45-67",
            email="ivan@example.com",
            home_address="ул. Тестовая, д. 1",
            registration_date="2024-01-01",
            status="active",
            notes="VIP читатель",
            passport_series="1234",
            passport_number="567890"
        )

        assert reader.middle_name == "Иванович"
        assert reader.phone == "+7 (999) 123-45-67"
        assert reader.email == "ivan@example.com"

    def test_reader_full_name_with_middle_name(self):
        """Test full_name property with middle name."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович"
        )

        assert reader.full_name == "Иванов Иван Иванович"

    def test_reader_full_name_without_middle_name(self):
        """Test full_name property without middle name."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван"
        )

        assert reader.full_name == "Иванов Иван"

    def test_reader_full_name_with_empty_middle_name(self):
        """Test full_name property with empty middle name."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            middle_name=""
        )

        assert reader.full_name == "Иванов Иван"

    def test_reader_is_active_true(self):
        """Test is_active property returns True for active reader."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            status="active"
        )

        assert reader.is_active is True

    def test_reader_is_active_false_blocked(self):
        """Test is_active property returns False for blocked reader."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            status="blocked"
        )

        assert reader.is_active is False

    def test_reader_is_active_false_expired(self):
        """Test is_active property returns False for expired reader."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван",
            status="expired"
        )

        assert reader.is_active is False

    def test_reader_default_values(self):
        """Test default values for optional fields."""
        reader = Reader(
            last_name="Иванов",
            first_name="Иван"
        )

        assert reader.middle_name == ""
        assert reader.birth_date == ""
        assert reader.phone == ""
        assert reader.email == ""
        assert reader.status == "active"
        assert reader.id == 0


# ===== BOOK ITEM MODEL TESTS =====

class TestBookItemModel:
    """Tests for BookItem model."""

    def test_book_item_creation(self):
        """Test creating book item."""
        item = BookItem(
            inventory_number="INV001",
            book_id=1,
            status=ItemStatus.AVAILABLE,
            location="Shelf A1"
        )

        assert item.inventory_number == "INV001"
        assert item.book_id == 1
        assert item.status == ItemStatus.AVAILABLE
        assert item.location == "Shelf A1"

    def test_book_item_default_status(self):
        """Test default status is AVAILABLE."""
        item = BookItem(
            inventory_number="INV001",
            book_id=1
        )

        assert item.status == ItemStatus.AVAILABLE

    def test_book_item_all_statuses(self):
        """Test all possible item statuses."""
        statuses = [
            ItemStatus.AVAILABLE,
            ItemStatus.LOANED,
            ItemStatus.LOST,
            ItemStatus.REPAIR,
            ItemStatus.WRITTEN_OFF
        ]

        for status in statuses:
            item = BookItem(
                inventory_number=f"INV{status.value}",
                book_id=1,
                status=status
            )
            assert item.status == status

    def test_book_item_default_location(self):
        """Test default location is empty string."""
        item = BookItem(
            inventory_number="INV001",
            book_id=1
        )

        assert item.location == ""

    def test_book_item_with_qr_code_path(self):
        """Test book item with QR code path."""
        item = BookItem(
            inventory_number="INV001",
            book_id=1,
            qr_code_path="/path/to/qr.png"
        )

        assert item.qr_code_path == "/path/to/qr.png"


# ===== LOAN RECORD MODEL TESTS =====

class TestLoanRecordModel:
    """Tests for LoanRecord model."""

    def test_loan_record_creation(self):
        """Test creating loan record."""
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)

        loan = LoanRecord(
            item_id=1,
            reader_id=1,
            issue_date=issue_date,
            due_date=due_date,
            condition_on_issue="Хорошее"
        )

        assert loan.item_id == 1
        assert loan.reader_id == 1
        assert loan.issue_date == issue_date
        assert loan.due_date == due_date
        assert loan.condition_on_issue == "Хорошее"
        assert loan.return_date is None

    def test_loan_record_with_return(self):
        """Test loan record with return date."""
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)
        return_date = issue_date + timedelta(days=10)

        loan = LoanRecord(
            item_id=1,
            reader_id=1,
            issue_date=issue_date,
            due_date=due_date,
            return_date=return_date,
            condition_on_issue="Хорошее",
            condition_on_return="Хорошее"
        )

        assert loan.return_date == return_date
        assert loan.condition_on_return == "Хорошее"

    def test_loan_record_default_dates(self):
        """Test loan record with default dates."""
        loan = LoanRecord(
            item_id=1,
            reader_id=1
        )

        assert isinstance(loan.issue_date, datetime)
        assert isinstance(loan.due_date, datetime)
        assert loan.return_date is None

    def test_loan_record_default_id(self):
        """Test loan record default ID is 0."""
        loan = LoanRecord(
            item_id=1,
            reader_id=1
        )

        assert loan.id == 0


# ===== ITEM STATUS ENUM TESTS =====

class TestItemStatusEnum:
    """Tests for ItemStatus enum."""

    def test_item_status_values(self):
        """Test all ItemStatus enum values."""
        assert ItemStatus.AVAILABLE.value == "AVAILABLE"
        assert ItemStatus.LOANED.value == "LOANED"
        assert ItemStatus.LOST.value == "LOST"
        assert ItemStatus.REPAIR.value == "REPAIR"
        assert ItemStatus.WRITTEN_OFF.value == "WRITTEN_OFF"

    def test_item_status_from_string(self):
        """Test creating ItemStatus from string."""
        status = ItemStatus("AVAILABLE")
        assert status == ItemStatus.AVAILABLE

    def test_item_status_comparison(self):
        """Test comparing ItemStatus values."""
        assert ItemStatus.AVAILABLE == ItemStatus.AVAILABLE
        assert ItemStatus.AVAILABLE != ItemStatus.LOANED


# ===== EDGE CASES AND SPECIAL SCENARIOS =====

class TestModelEdgeCases:
    """Tests for edge cases in models."""

    def test_book_with_very_long_fields(self):
        """Test book with very long field values."""
        long_text = "А" * 10000

        book = Book(
            author="Иванов И.И.",
            title=long_text,
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2",
            annotation=long_text
        )

        assert len(book.title) == 10000
        assert len(book.annotation) == 10000

    def test_book_with_special_characters(self):
        """Test book with special characters in fields."""
        book = Book(
            author="O'Brien, J.",
            title="C++ & Python: 100% Guide",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        assert "O'Brien" in book.author
        assert "&" in book.title

    def test_book_with_unicode_characters(self):
        """Test book with Unicode characters."""
        book = Book(
            author="田中太郎",
            title="Привет мир! 你好世界",
            place="東京",
            publisher="出版社",
            year=2024,
            pages=100,
            isbn="978-5-699-12345-2"
        )

        assert book.author == "田中太郎"
        assert "你好世界" in book.title

    def test_reader_with_special_characters_in_name(self):
        """Test reader with special characters in name."""
        reader = Reader(
            last_name="O'Connor",
            first_name="Seán"
        )

        assert reader.last_name == "O'Connor"
        assert reader.first_name == "Seán"

    def test_book_item_with_alphanumeric_inventory_number(self):
        """Test book item with alphanumeric inventory number."""
        item = BookItem(
            inventory_number="ABC-123-XYZ",
            book_id=1
        )

        assert item.inventory_number == "ABC-123-XYZ"

    def test_loan_record_overdue(self):
        """Test loan record that is overdue."""
        issue_date = datetime.now() - timedelta(days=30)
        due_date = datetime.now() - timedelta(days=16)

        loan = LoanRecord(
            item_id=1,
            reader_id=1,
            issue_date=issue_date,
            due_date=due_date
        )

        # Check if overdue
        assert loan.return_date is None
        assert loan.due_date < datetime.now()

    def test_book_year_boundaries(self):
        """Test book with boundary year values."""
        # Minimum year
        book1 = Book(
            author="Иванов И.И.",
            title="Старая книга",
            place="Москва",
            publisher="Наука",
            year=1900,
            pages=100,
            isbn="978-5-699-12345-2"
        )
        assert book1.year == 1900

        # Maximum year
        book2 = Book(
            author="Иванов И.И.",
            title="Будущая книга",
            place="Москва",
            publisher="Наука",
            year=2100,
            pages=100,
            isbn="978-5-699-12345-2"
        )
        assert book2.year == 2100

    def test_book_minimum_pages(self):
        """Test book with minimum pages (1)."""
        book = Book(
            author="Иванов И.И.",
            title="Короткая книга",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=1,
            isbn="978-5-699-12345-2"
        )

        assert book.pages == 1

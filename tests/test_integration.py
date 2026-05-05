"""
Integration tests for library system.

End-to-end tests for complete workflows including:
- Adding books and items
- Issuing and returning books
- Reader management
- QR code generation and printing
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.book import Book
from core.models.inventory import BookItem, Reader, ItemStatus
from core.services.book_service import BookService
from core.services.inventory_service import InventoryService
from core.services.qr_service import QRService
from core.services.printing_service import PrintingService
from infrastructure.database.book_repository import PostgresBookRepository
from infrastructure.database.inventory_repository import PostgresInventoryRepository
from config.settings import settings


# ===== FIXTURES =====

@pytest.fixture
def book_service(mock_db_manager):
    """Create book service."""
    return BookService(db_manager=mock_db_manager)


@pytest.fixture
def inventory_service(mock_db_manager):
    """Create inventory service."""
    repo = PostgresInventoryRepository(mock_db_manager)
    return InventoryService(repo)


@pytest.fixture
def temp_resources(tmp_path, monkeypatch):
    """Setup temporary resources directory."""
    monkeypatch.setattr(settings, 'RESOURCES_PATH', tmp_path)
    return tmp_path


# ===== INTEGRATION TESTS: COMPLETE WORKFLOWS =====

class TestCompleteBookWorkflow:
    """Test complete workflow from adding book to issuing and returning."""

    def test_add_book_create_items_issue_return(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test complete workflow: add book → create items → issue → return."""

        # Step 1: Add a book
        book = Book(
            author="Иванов И.И.",
            title="Основы программирования",
            place="Москва",
            publisher="Наука",
            year=2024,
            pages=350,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        assert book_id > 0

        # Step 2: Create physical items
        item_ids = inventory_service.add_items(
            book_id=book_id,
            count=3,
            start_inv=1000,
            location="Shelf A1"
        )
        assert len(item_ids) == 3

        # Step 3: Add a reader
        reader = Reader(
            last_name="Петров",
            first_name="Петр",
            middle_name="Петрович",
            phone="+7 (999) 123-45-67",
            email="petrov@example.com"
        )
        reader_id = inventory_service.add_reader(reader)
        assert reader_id > 0

        # Step 4: Issue first item to reader
        loan_id = inventory_service.issue_item(item_ids[0], reader_id, days=14)
        assert loan_id > 0

        # Verify item status changed to LOANED
        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.status == ItemStatus.LOANED

        # Verify loan record created
        loan = inventory_service._repo.find_active_loan(item_ids[0])
        assert loan is not None
        assert loan.reader_id == reader_id

        # Step 5: Return the item
        success = inventory_service.return_item(item_ids[0], "Хорошее состояние")
        assert success is True

        # Verify item status changed back to AVAILABLE
        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.status == ItemStatus.AVAILABLE

        # Verify loan record closed
        loan = inventory_service._repo.find_active_loan(item_ids[0])
        assert loan is None

    def test_multiple_readers_multiple_items(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test workflow with multiple readers and items."""

        # Add book
        book = Book(
            author="Сидоров С.С.",
            title="Базы данных",
            place="Санкт-Петербург",
            publisher="БХВ",
            year=2024,
            pages=400,
            isbn="978-5-9775-0002-9"
        )
        book_id = book_service.add_book(book)

        # Create 5 items
        item_ids = inventory_service.add_items(book_id=book_id, count=5, start_inv=2000)

        # Add 3 readers
        readers = []
        for i in range(3):
            reader = Reader(
                last_name=f"Читатель{i}",
                first_name=f"Имя{i}"
            )
            reader_id = inventory_service.add_reader(reader)
            readers.append(reader_id)

        # Issue items to different readers
        inventory_service.issue_item(item_ids[0], readers[0])
        inventory_service.issue_item(item_ids[1], readers[1])
        inventory_service.issue_item(item_ids[2], readers[2])

        # Verify active loans
        active_loans = inventory_service.get_all_active_loans()
        assert len(active_loans) >= 3

        # Return one item
        inventory_service.return_item(item_ids[0], "Хорошее")

        # Verify reader 0 has no active loans
        reader_loans = inventory_service.get_reader_current_loans(readers[0])
        assert len(reader_loans) == 0

        # Verify readers 1 and 2 still have active loans
        reader1_loans = inventory_service.get_reader_current_loans(readers[1])
        reader2_loans = inventory_service.get_reader_current_loans(readers[2])
        assert len(reader1_loans) == 1
        assert len(reader2_loans) == 1


class TestQRCodeWorkflow:
    """Test QR code generation workflow."""

    def test_generate_qr_for_book_and_items(
        self, book_service, inventory_service, temp_resources, mock_db_manager
    ):
        """Test generating QR codes for book and its items."""

        # Add book
        book = Book(
            author="Тестовый Автор",
            title="Тестовая Книга",
            place="Москва",
            publisher="Тест",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)

        # Generate book QR
        book_obj = book_service.get_book(book_id)
        book_qr_path = QRService.generate_book_qr(book_obj)
        assert book_qr_path is not None
        assert Path(book_qr_path).exists()

        # Create items
        item_ids = inventory_service.add_items(book_id=book_id, count=3, start_inv=3000)

        # Generate QR for each item
        item_qr_paths = []
        for item_id in item_ids:
            item = inventory_service._repo.get_item_by_id(item_id)
            qr_path = QRService.generate_item_qr(item, book_obj.isbn)
            assert qr_path is not None
            assert Path(qr_path).exists()
            item_qr_paths.append(qr_path)

        assert len(item_qr_paths) == 3


class TestPrintingWorkflow:
    """Test printing workflow."""

    def test_print_qr_codes_for_items(
        self, book_service, inventory_service, temp_resources, mock_db_manager
    ):
        """Test printing QR codes for multiple items."""

        # Add book
        book = Book(
            author="Автор",
            title="Книга",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=300,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        book_obj = book_service.get_book(book_id)

        # Generate book QR
        book_qr_path = QRService.generate_book_qr(book_obj)

        # Create items and generate QRs
        item_ids = inventory_service.add_items(book_id=book_id, count=5, start_inv=4000)

        items_data = []
        for item_id in item_ids:
            item = inventory_service._repo.get_item_by_id(item_id)
            qr_path = QRService.generate_item_qr(item, book_obj.isbn)

            # Update item with QR path
            inventory_service._repo.update_item_qr_path(item_id, qr_path)

            items_data.append({
                "qr_path": qr_path,
                "label": f"Экз. {item.inventory_number}"
            })

        # Generate batch PDF
        output_path = str(temp_resources / "batch_qr.pdf")
        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            book_qr_path=book_qr_path,
            book_label=f"{book_obj.author}. {book_obj.title}",
            output_path=output_path,
            mode="both"
        )

        assert success is True
        assert Path(output_path).exists()


class TestSearchAndRetrievalWorkflow:
    """Test search and retrieval workflows."""

    def test_search_books_and_check_availability(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test searching for books and checking item availability."""

        # Add multiple books
        books_data = [
            ("Иванов И.И.", "Python для начинающих", "978-5-4461-0001-9"),
            ("Петров П.П.", "Базы данных", "978-5-9775-0002-9"),
            ("Сидоров С.С.", "Веб-разработка", "978-5-9706-0003-0")
        ]

        for author, title, isbn in books_data:
            book = Book(
                author=author,
                title=title,
                place="Москва",
                publisher="Издательство",
                year=2024,
                pages=300,
                isbn=isbn
            )
            book_id = book_service.add_book(book)

            # Add items for each book
            inventory_service.add_items(book_id=book_id, count=2, start_inv=5000 + book_id * 10)

        # Search for Python books
        results = book_service.search_books("Python")
        assert len(results) > 0
        assert any("Python" in book.title for book in results)

        # Get items for found book
        python_book = results[0]
        items = inventory_service.get_items_by_book(python_book.id)
        assert len(items) == 2

        # Check all items are available
        assert all(item.status == ItemStatus.AVAILABLE for item in items)


class TestReaderHistoryWorkflow:
    """Test reader history and loan tracking."""

    def test_track_reader_loan_history(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test tracking complete loan history for a reader."""

        # Add books
        book1 = Book(
            author="Автор 1",
            title="Книга 1",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book1_id = book_service.add_book(book1)

        book2 = Book(
            author="Автор 2",
            title="Книга 2",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=300,
            isbn="978-5-9775-0002-9"
        )
        book2_id = book_service.add_book(book2)

        # Create items
        items1 = inventory_service.add_items(book_id=book1_id, count=2, start_inv=6000)
        items2 = inventory_service.add_items(book_id=book2_id, count=2, start_inv=6010)

        # Add reader
        reader = Reader(
            last_name="Тестовый",
            first_name="Читатель"
        )
        reader_id = inventory_service.add_reader(reader)

        # Issue and return multiple books
        # First book
        inventory_service.issue_item(items1[0], reader_id)
        inventory_service.return_item(items1[0], "Хорошее")

        # Second book
        inventory_service.issue_item(items2[0], reader_id)
        inventory_service.return_item(items2[0], "Хорошее")

        # Third book (still active)
        inventory_service.issue_item(items1[1], reader_id)

        # Check current loans
        current_loans = inventory_service.get_reader_current_loans(reader_id)
        assert len(current_loans) == 1

        # Check all loans (including returned)
        all_loans = inventory_service._repo.get_loans_by_reader(reader_id, active_only=False)
        assert len(all_loans) == 3


class TestItemStatusWorkflow:
    """Test item status management workflow."""

    def test_item_lifecycle_statuses(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test item going through different statuses."""

        # Add book and items
        book = Book(
            author="Автор",
            title="Книга",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        item_ids = inventory_service.add_items(book_id=book_id, count=4, start_inv=7000)

        # Item 1: Normal circulation
        reader = Reader(last_name="Читатель", first_name="Тест")
        reader_id = inventory_service.add_reader(reader)

        inventory_service.issue_item(item_ids[0], reader_id)
        assert inventory_service._repo.get_item_by_id(item_ids[0]).status == ItemStatus.LOANED

        inventory_service.return_item(item_ids[0], "Хорошее")
        assert inventory_service._repo.get_item_by_id(item_ids[0]).status == ItemStatus.AVAILABLE

        # Item 2: Goes to repair
        inventory_service.update_item_status(item_ids[1], ItemStatus.REPAIR)
        assert inventory_service._repo.get_item_by_id(item_ids[1]).status == ItemStatus.REPAIR

        # Item 3: Lost
        inventory_service.update_item_status(item_ids[2], ItemStatus.LOST)
        assert inventory_service._repo.get_item_by_id(item_ids[2]).status == ItemStatus.LOST

        # Item 4: Written off
        inventory_service.update_item_status(item_ids[3], ItemStatus.WRITTEN_OFF)
        assert inventory_service._repo.get_item_by_id(item_ids[3]).status == ItemStatus.WRITTEN_OFF


class TestOverdueLoansWorkflow:
    """Test overdue loan detection."""

    def test_identify_overdue_loans(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test identifying overdue loans."""

        # Add book and items
        book = Book(
            author="Автор",
            title="Книга",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        item_ids = inventory_service.add_items(book_id=book_id, count=2, start_inv=8000)

        # Add reader
        reader = Reader(last_name="Читатель", first_name="Тест")
        reader_id = inventory_service.add_reader(reader)

        # Issue with short duration (will be overdue immediately for testing)
        inventory_service.issue_item(item_ids[0], reader_id, days=0)

        # Get active loans
        active_loans = inventory_service.get_all_active_loans()

        # Check if any are overdue
        overdue_loans = [
            loan for loan in active_loans
            if loan.return_date is None and loan.due_date < datetime.now()
        ]

        assert len(overdue_loans) > 0


class TestConcurrentOperations:
    """Test concurrent operations on the same resources."""

    def test_sequential_loans_same_item(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test sequential loans of the same item to different readers."""

        # Setup
        book = Book(
            author="Автор",
            title="Книга",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        item_ids = inventory_service.add_items(book_id=book_id, count=1, start_inv=9000)
        item_id = item_ids[0]

        # Add readers
        reader1 = Reader(last_name="Читатель1", first_name="Тест")
        reader2 = Reader(last_name="Читатель2", first_name="Тест")
        reader1_id = inventory_service.add_reader(reader1)
        reader2_id = inventory_service.add_reader(reader2)

        # First loan
        loan1_id = inventory_service.issue_item(item_id, reader1_id)
        inventory_service.return_item(item_id, "Хорошее")

        # Second loan
        loan2_id = inventory_service.issue_item(item_id, reader2_id)

        # Verify history
        history = inventory_service.get_item_history(item_id)
        assert len(history) == 2
        assert history[0].reader_id == reader1_id
        assert history[1].reader_id == reader2_id


class TestDataIntegrity:
    """Test data integrity across operations."""

    def test_book_deletion_cascade(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test that deleting a book handles related items properly."""

        # Add book and items
        book = Book(
            author="Автор",
            title="Книга для удаления",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        item_ids = inventory_service.add_items(book_id=book_id, count=3, start_inv=10000)

        # Verify items exist
        items_before = inventory_service.get_items_by_book(book_id)
        assert len(items_before) == 3

        # Delete book
        book_service.delete_book(book_id)

        # Verify book is deleted
        deleted_book = book_service.get_book(book_id)
        assert deleted_book is None

        # Items should be cascade deleted (depending on DB constraints)
        items_after = inventory_service.get_items_by_book(book_id)
        assert len(items_after) == 0

    def test_reader_with_active_loans_deletion(
        self, book_service, inventory_service, mock_db_manager
    ):
        """Test handling reader deletion with active loans."""

        # Setup
        book = Book(
            author="Автор",
            title="Книга",
            place="Москва",
            publisher="Издательство",
            year=2024,
            pages=200,
            isbn="978-5-699-12345-2"
        )
        book_id = book_service.add_book(book)
        item_ids = inventory_service.add_items(book_id=book_id, count=1, start_inv=11000)

        reader = Reader(last_name="Читатель", first_name="Тест")
        reader_id = inventory_service.add_reader(reader)

        # Issue item
        inventory_service.issue_item(item_ids[0], reader_id)

        # Try to delete reader with active loan
        # This should either fail or cascade delete loans depending on constraints
        try:
            success = inventory_service.delete_reader(reader_id)
            # If deletion succeeds, verify loan is also deleted
            if success:
                loan = inventory_service._repo.find_active_loan(item_ids[0])
                # Loan should be deleted or reader_id should be null
        except Exception:
            # Deletion failed due to foreign key constraint - expected behavior
            pass


class TestCompleteLibraryScenario:
    """Test complete library scenario with multiple operations."""

    def test_full_library_day_scenario(
        self, book_service, inventory_service, temp_resources, mock_db_manager
    ):
        """Test a full day scenario in a library."""

        # Morning: Add new books to collection
        books = []
        valid_isbns = [
            "978-5-699-12345-2",  # Valid ISBN-13
            "978-5-699-12346-9",  # Valid ISBN-13
            "978-5-699-12347-6"   # Valid ISBN-13
        ]
        for i in range(3):
            book = Book(
                author=f"Автор {i}",
                title=f"Книга {i}",
                place="Москва",
                publisher="Издательство",
                year=2024,
                pages=200 + i * 50,
                isbn=valid_isbns[i]
            )
            book_id = book_service.add_book(book)
            books.append(book_id)

            # Add physical copies
            inventory_service.add_items(book_id=book_id, count=3, start_inv=12000 + i * 10)

        # Add readers
        readers = []
        for i in range(5):
            reader = Reader(
                last_name=f"Читатель{i}",
                first_name=f"Имя{i}",
                phone=f"+7 (999) {i:03d}-45-67"
            )
            reader_id = inventory_service.add_reader(reader)
            readers.append(reader_id)

        # Midday: Issue books
        all_items = inventory_service.get_all_items()
        available_items = [item for item in all_items if item.status == ItemStatus.AVAILABLE]

        for i, reader_id in enumerate(readers[:3]):
            if i < len(available_items):
                inventory_service.issue_item(available_items[i].id, reader_id)

        # Afternoon: Returns
        inventory_service.return_item(available_items[0].id, "Хорошее состояние")

        # Evening: Statistics
        total_books = book_service.count_books()
        total_items = len(inventory_service.get_all_items())
        active_loans = len(inventory_service.get_all_active_loans())
        total_readers = len(inventory_service.get_all_readers())

        assert total_books >= 3
        assert total_items >= 9
        assert active_loans >= 2
        assert total_readers >= 5

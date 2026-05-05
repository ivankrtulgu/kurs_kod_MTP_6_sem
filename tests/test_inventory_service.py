"""
Tests for InventoryService.

Tests for business logic of inventory management including
item management, circulation (issue/return), and reader management.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.inventory import BookItem, Reader, LoanRecord, ItemStatus
from core.services.inventory_service import InventoryService
from infrastructure.database.inventory_repository import PostgresInventoryRepository


# ===== FIXTURES =====

@pytest.fixture
def inventory_service(mock_db_manager):
    """Create inventory service with mock database."""
    repo = PostgresInventoryRepository(mock_db_manager)
    return InventoryService(repo)


@pytest.fixture
def sample_reader():
    """Create sample reader."""
    return Reader(
        last_name="Иванов",
        first_name="Иван",
        middle_name="Иванович",
        birth_date="1990-01-01",
        phone="+7 (999) 123-45-67",
        email="ivan@example.com",
        home_address="ул. Тестовая, д. 1",
        registration_date="2024-01-01",
        status="active",
        passport_series="1234",
        passport_number="567890"
    )


@pytest.fixture
def sample_book_id(mock_db_manager):
    """Create a sample book and return its ID."""
    from infrastructure.database.book_repository import PostgresBookRepository
    from core.models.book import Book

    repo = PostgresBookRepository(mock_db_manager)
    book = Book(
        author="Тестовый Автор",
        title="Тестовая Книга",
        place="Москва",
        publisher="Наука",
        year=2024,
        pages=200,
        isbn="978-5-699-12345-2"
    )
    return repo.add(book)


# ===== TESTS: ADD ITEMS =====

class TestAddItems:
    """Tests for add_items method."""

    def test_add_single_item(self, inventory_service, sample_book_id):
        """Test adding a single item."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=1,
            start_inv=1000,
            location="Shelf A1"
        )

        assert len(item_ids) == 1
        assert all(isinstance(id, int) for id in item_ids)

    def test_add_multiple_items(self, inventory_service, sample_book_id):
        """Test adding multiple items."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=5,
            start_inv=1000,
            location="Shelf A1"
        )

        assert len(item_ids) == 5
        assert len(set(item_ids)) == 5  # All unique

    def test_add_items_sequential_inventory_numbers(self, inventory_service, sample_book_id):
        """Test that inventory numbers are sequential."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=3,
            start_inv=1000
        )

        items = [inventory_service._repo.get_item_by_id(id) for id in item_ids]
        inv_numbers = [int(item.inventory_number) for item in items]

        assert inv_numbers == [1000, 1001, 1002]

    def test_add_items_auto_start_inventory(self, inventory_service, sample_book_id):
        """Test adding items with auto-generated start inventory number."""
        # Add first batch
        inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=100)

        # Add second batch without specifying start_inv
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=2)

        items = [inventory_service._repo.get_item_by_id(id) for id in item_ids]
        inv_numbers = [int(item.inventory_number) for item in items]

        # Should start from 102 (after 100, 101)
        assert inv_numbers[0] >= 102

    def test_add_items_with_location(self, inventory_service, sample_book_id):
        """Test adding items with specific location."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=2,
            start_inv=1000,
            location="Shelf B2"
        )

        items = [inventory_service._repo.get_item_by_id(id) for id in item_ids]

        assert all(item.location == "Shelf B2" for item in items)

    def test_add_items_default_status_available(self, inventory_service, sample_book_id):
        """Test that new items have AVAILABLE status."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=2,
            start_inv=1000
        )

        items = [inventory_service._repo.get_item_by_id(id) for id in item_ids]

        assert all(item.status == ItemStatus.AVAILABLE for item in items)


# ===== TESTS: GET ITEMS =====

class TestGetItems:
    """Tests for getting items."""

    def test_get_items_by_book(self, inventory_service, sample_book_id):
        """Test getting all items for a specific book."""
        inventory_service.add_items(book_id=sample_book_id, count=3, start_inv=1000)

        items = inventory_service.get_items_by_book(sample_book_id)

        assert len(items) == 3
        assert all(item.book_id == sample_book_id for item in items)

    def test_get_items_by_book_empty(self, inventory_service, sample_book_id):
        """Test getting items for book with no items."""
        items = inventory_service.get_items_by_book(sample_book_id)

        assert items == []

    def test_get_all_items(self, inventory_service, sample_book_id):
        """Test getting all items in library."""
        inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=1000)

        items = inventory_service.get_all_items()

        assert len(items) >= 2


# ===== TESTS: UPDATE ITEM LOCATION =====

class TestUpdateItemLocation:
    """Tests for update_item_location method."""

    def test_update_item_location_success(self, inventory_service, sample_book_id):
        """Test successfully updating item location."""
        item_ids = inventory_service.add_items(
            book_id=sample_book_id,
            count=1,
            start_inv=1000,
            location="Shelf A1"
        )

        success = inventory_service.update_item_location(item_ids[0], "Shelf B2")

        assert success is True

        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.location == "Shelf B2"


# ===== TESTS: ISSUE ITEM =====

class TestIssueItem:
    """Tests for issue_item method."""

    def test_issue_item_success(self, inventory_service, sample_book_id, sample_reader):
        """Test successfully issuing an item."""
        # Add reader
        reader_id = inventory_service.add_reader(sample_reader)

        # Add item
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        # Issue item
        loan_id = inventory_service.issue_item(item_id, reader_id, days=14)

        assert loan_id > 0
        assert isinstance(loan_id, int)

    def test_issue_item_updates_status_to_loaned(self, inventory_service, sample_book_id, sample_reader):
        """Test that issuing item updates status to LOANED."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        inventory_service.issue_item(item_id, reader_id)

        item = inventory_service._repo.get_item_by_id(item_id)
        assert item.status == ItemStatus.LOANED

    def test_issue_item_creates_loan_record(self, inventory_service, sample_book_id, sample_reader):
        """Test that issuing item creates loan record."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        loan_id = inventory_service.issue_item(item_id, reader_id, days=14)

        loan = inventory_service._repo.find_active_loan(item_id)
        assert loan is not None
        assert loan.id == loan_id
        assert loan.item_id == item_id
        assert loan.reader_id == reader_id

    def test_issue_item_sets_due_date(self, inventory_service, sample_book_id, sample_reader):
        """Test that issuing item sets correct due date."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        issue_time = datetime.now()
        inventory_service.issue_item(item_id, reader_id, days=14)

        loan = inventory_service._repo.find_active_loan(item_id)
        expected_due = issue_time + timedelta(days=14)

        # Allow 1 second tolerance
        assert abs((loan.due_date - expected_due).total_seconds()) < 1

    def test_issue_item_nonexistent_item(self, inventory_service, sample_reader):
        """Test issuing non-existent item raises error."""
        reader_id = inventory_service.add_reader(sample_reader)

        with pytest.raises(ValueError) as exc_info:
            inventory_service.issue_item(99999, reader_id)

        assert "не найден" in str(exc_info.value).lower()

    def test_issue_item_nonexistent_reader(self, inventory_service, sample_book_id):
        """Test issuing to non-existent reader raises error."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        with pytest.raises(ValueError) as exc_info:
            inventory_service.issue_item(item_ids[0], 99999)

        assert "не найден" in str(exc_info.value).lower()

    def test_issue_item_already_loaned(self, inventory_service, sample_book_id, sample_reader):
        """Test issuing already loaned item raises error."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        # Issue first time
        inventory_service.issue_item(item_id, reader_id)

        # Try to issue again
        with pytest.raises(ValueError) as exc_info:
            inventory_service.issue_item(item_id, reader_id)

        assert "недоступен" in str(exc_info.value).lower()

    def test_issue_item_inactive_reader(self, inventory_service, sample_book_id, sample_reader):
        """Test issuing to inactive reader raises error."""
        sample_reader.status = "blocked"
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        with pytest.raises(ValueError) as exc_info:
            inventory_service.issue_item(item_ids[0], reader_id)

        assert "не активен" in str(exc_info.value).lower()

    def test_issue_item_by_inventory_number(self, inventory_service, sample_book_id, sample_reader):
        """Test issuing item by inventory number."""
        reader_id = inventory_service.add_reader(sample_reader)
        inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        loan_id = inventory_service.issue_item_by_inv("1000", reader_id, days=14)

        assert loan_id > 0


# ===== TESTS: RETURN ITEM =====

class TestReturnItem:
    """Tests for return_item method."""

    def test_return_item_success(self, inventory_service, sample_book_id, sample_reader):
        """Test successfully returning an item."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        # Issue item
        inventory_service.issue_item(item_id, reader_id)

        # Return item
        success = inventory_service.return_item(item_id, "Хорошее состояние")

        assert success is True

    def test_return_item_updates_status_to_available(self, inventory_service, sample_book_id, sample_reader):
        """Test that returning item updates status to AVAILABLE."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        inventory_service.issue_item(item_id, reader_id)
        inventory_service.return_item(item_id, "Хорошее")

        item = inventory_service._repo.get_item_by_id(item_id)
        assert item.status == ItemStatus.AVAILABLE

    def test_return_item_closes_loan_record(self, inventory_service, sample_book_id, sample_reader):
        """Test that returning item closes loan record."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        inventory_service.issue_item(item_id, reader_id)
        inventory_service.return_item(item_id, "Хорошее")

        active_loan = inventory_service._repo.find_active_loan(item_id)
        assert active_loan is None

    def test_return_item_not_loaned(self, inventory_service, sample_book_id):
        """Test returning item that is not loaned raises error."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        with pytest.raises(ValueError) as exc_info:
            inventory_service.return_item(item_ids[0], "Хорошее")

        assert "не найдена" in str(exc_info.value).lower()

    def test_return_item_by_inventory_number(self, inventory_service, sample_book_id, sample_reader):
        """Test returning item by inventory number."""
        reader_id = inventory_service.add_reader(sample_reader)
        inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        inventory_service.issue_item_by_inv("1000", reader_id)
        success = inventory_service.return_item_by_inv("1000", "Хорошее")

        assert success is True


# ===== TESTS: UPDATE ITEM STATUS =====

class TestUpdateItemStatus:
    """Tests for update_item_status method."""

    def test_update_status_to_repair(self, inventory_service, sample_book_id):
        """Test updating item status to REPAIR."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        success = inventory_service.update_item_status(item_ids[0], ItemStatus.REPAIR)

        assert success is True

        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.status == ItemStatus.REPAIR

    def test_update_status_to_lost(self, inventory_service, sample_book_id):
        """Test updating item status to LOST."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        success = inventory_service.update_item_status(item_ids[0], ItemStatus.LOST)

        assert success is True

        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.status == ItemStatus.LOST

    def test_update_status_to_written_off(self, inventory_service, sample_book_id):
        """Test updating item status to WRITTEN_OFF."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        success = inventory_service.update_item_status(item_ids[0], ItemStatus.WRITTEN_OFF)

        assert success is True

        item = inventory_service._repo.get_item_by_id(item_ids[0])
        assert item.status == ItemStatus.WRITTEN_OFF

    def test_update_status_loaned_item_fails(self, inventory_service, sample_book_id, sample_reader):
        """Test that updating status of loaned item raises error."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        inventory_service.issue_item(item_id, reader_id)

        with pytest.raises(ValueError) as exc_info:
            inventory_service.update_item_status(item_id, ItemStatus.LOST)

        assert "выдан" in str(exc_info.value).lower()

    def test_update_status_nonexistent_item(self, inventory_service):
        """Test updating status of non-existent item raises error."""
        with pytest.raises(ValueError) as exc_info:
            inventory_service.update_item_status(99999, ItemStatus.LOST)

        assert "не найден" in str(exc_info.value).lower()


# ===== TESTS: ITEM HISTORY =====

class TestItemHistory:
    """Tests for get_item_history method."""

    def test_get_item_history_empty(self, inventory_service, sample_book_id):
        """Test getting history for item with no loans."""
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        history = inventory_service.get_item_history(item_ids[0])

        assert history == []

    def test_get_item_history_single_loan(self, inventory_service, sample_book_id, sample_reader):
        """Test getting history for item with one loan."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        inventory_service.issue_item(item_id, reader_id)
        inventory_service.return_item(item_id, "Хорошее")

        history = inventory_service.get_item_history(item_id)

        assert len(history) == 1
        assert history[0].item_id == item_id

    def test_get_item_history_multiple_loans(self, inventory_service, sample_book_id, sample_reader):
        """Test getting history for item with multiple loans."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        # First loan
        inventory_service.issue_item(item_id, reader_id)
        inventory_service.return_item(item_id, "Хорошее")

        # Second loan
        inventory_service.issue_item(item_id, reader_id)
        inventory_service.return_item(item_id, "Хорошее")

        history = inventory_service.get_item_history(item_id)

        assert len(history) == 2


# ===== TESTS: READER MANAGEMENT =====

class TestReaderManagement:
    """Tests for reader management methods."""

    def test_add_reader(self, inventory_service, sample_reader):
        """Test adding a reader."""
        reader_id = inventory_service.add_reader(sample_reader)

        assert reader_id > 0
        assert isinstance(reader_id, int)

    def test_update_reader(self, inventory_service, sample_reader):
        """Test updating a reader."""
        reader_id = inventory_service.add_reader(sample_reader)

        sample_reader.id = reader_id
        sample_reader.phone = "+7 (999) 999-99-99"

        success = inventory_service.update_reader(sample_reader)

        assert success is True

        updated = inventory_service._repo.get_reader_by_id(reader_id)
        assert updated.phone == "+7 (999) 999-99-99"

    def test_delete_reader(self, inventory_service, sample_reader):
        """Test deleting a reader."""
        reader_id = inventory_service.add_reader(sample_reader)

        success = inventory_service.delete_reader(reader_id)

        assert success is True

        deleted = inventory_service._repo.get_reader_by_id(reader_id)
        assert deleted is None

    def test_get_all_readers(self, inventory_service, sample_reader):
        """Test getting all readers."""
        inventory_service.add_reader(sample_reader)

        readers = inventory_service.get_all_readers()

        assert len(readers) >= 1


# ===== TESTS: LOAN QUERIES =====

class TestLoanQueries:
    """Tests for loan query methods."""

    def test_get_reader_current_loans(self, inventory_service, sample_book_id, sample_reader):
        """Test getting current loans for a reader."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=1000)

        # Issue two items
        inventory_service.issue_item(item_ids[0], reader_id)
        inventory_service.issue_item(item_ids[1], reader_id)

        loans = inventory_service.get_reader_current_loans(reader_id)

        assert len(loans) == 2

    def test_get_reader_current_loans_after_return(self, inventory_service, sample_book_id, sample_reader):
        """Test that returned items don't appear in current loans."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=1000)

        inventory_service.issue_item(item_ids[0], reader_id)
        inventory_service.issue_item(item_ids[1], reader_id)

        # Return one item
        inventory_service.return_item(item_ids[0], "Хорошее")

        loans = inventory_service.get_reader_current_loans(reader_id)

        assert len(loans) == 1
        assert loans[0].item_id == item_ids[1]

    def test_get_all_active_loans(self, inventory_service, sample_book_id, sample_reader):
        """Test getting all active loans in library."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=1000)

        inventory_service.issue_item(item_ids[0], reader_id)
        inventory_service.issue_item(item_ids[1], reader_id)

        loans = inventory_service.get_all_active_loans()

        assert len(loans) >= 2

    def test_get_all_loans(self, inventory_service, sample_book_id, sample_reader):
        """Test getting all loans including closed ones."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=2, start_inv=1000)

        inventory_service.issue_item(item_ids[0], reader_id)
        inventory_service.return_item(item_ids[0], "Хорошее")

        inventory_service.issue_item(item_ids[1], reader_id)

        loans = inventory_service.get_all_loans()

        assert len(loans) >= 2


# ===== TESTS: EDGE CASES =====

class TestInventoryServiceEdgeCases:
    """Tests for edge cases in inventory service."""

    def test_issue_multiple_items_to_same_reader(self, inventory_service, sample_book_id, sample_reader):
        """Test issuing multiple items to the same reader."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=5, start_inv=1000)

        for item_id in item_ids:
            loan_id = inventory_service.issue_item(item_id, reader_id)
            assert loan_id > 0

        loans = inventory_service.get_reader_current_loans(reader_id)
        assert len(loans) == 5

    def test_issue_same_item_to_different_readers_sequentially(self, inventory_service, sample_book_id):
        """Test issuing same item to different readers over time."""
        reader1 = Reader(last_name="Иванов", first_name="Иван")
        reader2 = Reader(last_name="Петров", first_name="Петр")

        reader1_id = inventory_service.add_reader(reader1)
        reader2_id = inventory_service.add_reader(reader2)

        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)
        item_id = item_ids[0]

        # Issue to reader 1
        inventory_service.issue_item(item_id, reader1_id)
        inventory_service.return_item(item_id, "Хорошее")

        # Issue to reader 2
        inventory_service.issue_item(item_id, reader2_id)

        active_loan = inventory_service._repo.find_active_loan(item_id)
        assert active_loan.reader_id == reader2_id

    def test_custom_loan_duration(self, inventory_service, sample_book_id, sample_reader):
        """Test issuing item with custom loan duration."""
        reader_id = inventory_service.add_reader(sample_reader)
        item_ids = inventory_service.add_items(book_id=sample_book_id, count=1, start_inv=1000)

        issue_time = datetime.now()
        inventory_service.issue_item(item_ids[0], reader_id, days=30)

        loan = inventory_service._repo.find_active_loan(item_ids[0])
        expected_due = issue_time + timedelta(days=30)

        assert abs((loan.due_date - expected_due).total_seconds()) < 1

    def test_find_item_by_invalid_inventory_number(self, inventory_service):
        """Test finding item by non-existent inventory number."""
        with pytest.raises(ValueError) as exc_info:
            inventory_service.issue_item_by_inv("NONEXISTENT", 1)

        assert "не найден" in str(exc_info.value).lower()

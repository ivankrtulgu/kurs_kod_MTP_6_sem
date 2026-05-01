import pytest
from datetime import datetime
from core.models.inventory import BookItem, Reader, LoanRecord, ItemStatus
from infrastructure.database.inventory_repository import PostgresInventoryRepository
from tests.conftest import mock_db_manager

def create_sample_reader(id=0):
    return Reader(
        id=id,
        last_name="Тестовый",
        first_name="Иван",
        middle_name="Иванович",
        birth_date="1990-01-01",
        phone="1234567890",
        email="test@example.com",
        home_address="ул. Тестовая, 1",
        registration_date="2023-01-01",
        status="active",
        notes="Тестовый читатель",
        passport_series="1234",
        passport_number="567890"
    )

def test_book_item_crud(mock_db_manager):
    repo = PostgresInventoryRepository(mock_db_manager)
    # Need a book first
    from infrastructure.database.book_repository import PostgresBookRepository
    book_repo = PostgresBookRepository(mock_db_manager)
    from core.models.book import Book
    book = Book(author="A", title="T", place="P", publisher="Pub", year=2020, pages=100, isbn="978-0-13-235088-4")
    book_id = book_repo.add(book)
    
    item = BookItem(inventory_number="INV001", book_id=book_id, status=ItemStatus.AVAILABLE, location="Shelf A1")
    item_id = repo.add_item(item)
    assert item_id > 0
    
    retrieved = repo.get_item_by_id(item_id)
    assert retrieved.inventory_number == "INV001"
    
    repo.update_item_location(item_id, "Shelf B2")
    assert repo.get_item_by_id(item_id).location == "Shelf B2"
    
    repo.update_item_status(item_id, ItemStatus.LOST)
    assert repo.get_item_by_id(item_id).status == ItemStatus.LOST
    
    # Delete not implemented in repo as a direct method but usually done via items
    # Let's check if it exists. (It doesn't in the provided code)

def test_reader_crud(mock_db_manager):
    repo = PostgresInventoryRepository(mock_db_manager)
    reader = create_sample_reader()
    reader_id = repo.add_reader(reader)
    assert reader_id > 0
    
    retrieved = repo.get_reader_by_id(reader_id)
    assert retrieved.last_name == "Тестовый"
    
    reader.first_name = "Обновленный"
    reader.id = reader_id
    repo.update_reader(reader)
    assert repo.get_reader_by_id(reader_id).first_name == "Обновленный"
    
    repo.delete_reader(reader_id)
    assert repo.get_reader_by_id(reader_id) is None

def test_loan_lifecycle(mock_db_manager):
    repo = PostgresInventoryRepository(mock_db_manager)
    # Setup
    from infrastructure.database.book_repository import PostgresBookRepository
    from core.models.book import Book
    book_repo = PostgresBookRepository(mock_db_manager)
    book = Book(author="A", title="T", place="P", publisher="Pub", year=2020, pages=100, isbn="978-0-13-235088-4")
    book_id = book_repo.add(book)
    
    item = BookItem(inventory_number="INV002", book_id=book_id, status=ItemStatus.AVAILABLE, location="S1")
    item_id = repo.add_item(item)
    
    reader = create_sample_reader()
    reader_id = repo.add_reader(reader)
    
    loan = LoanRecord(
        item_id=item_id,
        reader_id=reader_id,
        issue_date=datetime.now(),
        due_date=datetime.now(),
        condition_on_issue="Good"
    )
    loan_id = repo.create_loan(loan)
    assert loan_id > 0
    
    active_loan = repo.find_active_loan(item_id)
    assert active_loan is not None
    assert active_loan.id == loan_id
    
    repo.close_loan(loan_id, datetime.now(), "Slightly worn")
    assert repo.find_active_loan(item_id) is None

def test_inventory_numbering(mock_db_manager):
    repo = PostgresInventoryRepository(mock_db_manager)
    # Add some items
    from infrastructure.database.book_repository import PostgresBookRepository
    from core.models.book import Book
    book_repo = PostgresBookRepository(mock_db_manager)
    book = Book(author="A", title="T", place="P", publisher="Pub", year=2020, pages=100, isbn="978-0-13-235088-4")
    book_id = book_repo.add(book)
    
    repo.add_item(BookItem(inventory_number="100", book_id=book_id, status=ItemStatus.AVAILABLE))
    repo.add_item(BookItem(inventory_number="105", book_id=book_id, status=ItemStatus.AVAILABLE))
    
    assert repo.get_max_inventory_number() == 105

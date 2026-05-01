import pytest
from datetime import datetime
from core.models.book import Book
from infrastructure.database.book_repository import PostgresBookRepository
from tests.conftest import mock_db_manager

def create_sample_book(id=0):
    return Book(
        id=id,
        author="Тестовый Автор",
        title="Тестовая Книга",
        subtitle="Тестовый подзаголовок",
        responsibility="Отв. ред. Тест",
        edition="1-е изд.",
        place="Москва",
        publisher="Тест-Издательство",
        year=2024,
        pages=200,
        isbn="978-0-13-235088-4", #-’ Modified to be a more likely valid format for simple tests or handle check digit
        copyright="© 2024",
        udc="123.45",
        bbk="А12",
        author_mark="Т100",
        reviewers="Рецензент 1",
        annotation="Тестовая аннотация",
        abstract="Тестовый абстракт",
        doi="10.1000/test",
        content_type="Текст",
        access_method="непосредственный",
        created_at=datetime.now(),
        qr_code_path="test_qr.png",
        cover_image_path="test_cover.jpg"
    )

def test_add_and_get_book(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    book = create_sample_book()
    
    book_id = repo.add(book)
    assert book_id > 0
    
    retrieved = repo.get_by_id(book_id)
    assert retrieved is not None
    assert retrieved.title == book.title
    assert retrieved.author == book.author
    assert retrieved.isbn == book.isbn

def test_get_by_isbn(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    book = create_sample_book()
    book_id = repo.add(book)
    
    retrieved = repo.get_by_isbn(book.isbn)
    assert retrieved is not None
    assert retrieved.id == book_id

def test_get_nonexistent_book(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    assert repo.get_by_id(999999) is None
    assert repo.get_by_isbn("000-0000000000") is None

def test_update_book(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    book = create_sample_book()
    book_id = repo.add(book)
    
    book.title = "Обновленный заголовок"
    book.id = book_id
    updated = repo.update(book)
    
    assert updated is True
    retrieved = repo.get_by_id(book_id)
    assert retrieved.title == "Обновленный заголовок"

def test_delete_book(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    book = create_sample_book()
    book_id = repo.add(book)
    
    deleted = repo.delete(book_id)
    assert deleted is True
    assert repo.get_by_id(book_id) is None

def test_search_books(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    
    book1 = create_sample_book()
    book1.title = "Книга про Python"
    repo.add(book1)
    
    book2 = create_sample_book()
    book2.title = "Книга про Java"
    repo.add(book2)
    
    results = repo.search("Python")
    assert len(results) == 1
    assert results[0].title == "Книга про Python"

def test_count_books(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    repo.add(create_sample_book())
    repo.add(create_sample_book())
    
    assert repo.count() == 2

def test_add_with_custom_id(mock_db_manager):
    repo = PostgresBookRepository(mock_db_manager)
    import random
    custom_id = random.randint(10000, 99999)
    book = create_sample_book(id=custom_id)
    
    book_id = repo.add(book)
    assert book_id == custom_id
    assert repo.get_by_id(custom_id) is not None

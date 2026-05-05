# API Documentation

Документация по программному интерфейсу системы управления библиотекой.

## Обзор

API системы организовано в виде сервисов, каждый из которых отвечает за определенную область функциональности:

- **BookService** — управление каталогом книг
- **InventoryService** — управление инвентарем, читателями и выдачей
- **QRService** — генерация QR-кодов
- **PrintingService** — печать QR-кодов в PDF

## Общие принципы

### Обработка ошибок

Все сервисы используют исключения для сообщения об ошибках:

```python
class ValidationError(Exception):
    """Ошибка валидации данных."""
    pass

class RepositoryError(Exception):
    """Ошибка работы с репозиторием."""
    pass
```

### Типизация

Все публичные методы имеют type hints:

```python
def add_book(self, book: Book) -> int:
    """Добавить книгу."""
    pass
```

### Возвращаемые значения

- Методы создания возвращают ID созданного объекта
- Методы получения возвращают объект или `None`
- Методы поиска возвращают список объектов
- Методы удаления возвращают `bool` (успех/неудача)

## Сервисы

### BookService

Подробная документация: [Book Service API](book-service.md)

Основные методы:
- `add_book(book: Book) -> int`
- `get_book(book_id: int) -> Book | None`
- `update_book(book: Book) -> bool`
- `delete_book(book_id: int) -> bool`
- `search_books(query: str) -> list[Book]`
- `get_all_books() -> list[Book]`

### InventoryService

Подробная документация: [Inventory Service API](inventory-service.md)

Основные методы:
- `add_items(book_id: int, count: int) -> list[BookItem]`
- `issue_item(item_id: int, reader_id: int) -> LoanRecord`
- `return_item(item_id: int) -> bool`
- `add_reader(reader: Reader) -> int`
- `get_active_loans() -> list[LoanRecord]`

### QRService

Подробная документация: [QR Service API](qr-service.md)

Основные методы:
- `generate_book_qr(book: Book) -> str`
- `generate_item_qr(item: BookItem) -> str`

### PrintingService

Подробная документация: [Printing Service API](printing-service.md)

Основные методы:
- `generate_qr_pdf(items: list[BookItem], output_path: str) -> str`
- `generate_batch_qr_pdf(book: Book, items: list[BookItem]) -> str`

## Модели данных

### Book

```python
@dataclass
class Book:
    author: str
    title: str
    isbn: str
    publisher: str = ""
    year: int = 0
    pages: int = 0
    place: str = ""
    doi: str = ""
    cover_image_path: str = ""
    id: int = 0
    created_at: datetime = None
```

### BookItem

```python
@dataclass
class BookItem:
    book_id: int
    inventory_number: str
    status: ItemStatus = ItemStatus.AVAILABLE
    location: str = ""
    qr_code_path: str = ""
    id: int = 0
```

### Reader

```python
@dataclass
class Reader:
    first_name: str
    last_name: str
    card_number: str
    middle_name: str = ""
    phone: str = ""
    email: str = ""
    registration_date: datetime = None
    expiry_date: datetime = None
    is_blocked: bool = False
    id: int = 0
```

### LoanRecord

```python
@dataclass
class LoanRecord:
    item_id: int
    reader_id: int
    loan_date: datetime
    due_date: datetime
    return_date: datetime = None
    id: int = 0
```

## Примеры использования

### Добавление книги

```python
from core.services.book_service import BookService
from core.models.book import Book

service = BookService()

book = Book(
    author="Иванов И.И.",
    title="Основы программирования",
    isbn="978-5-9775-3946-9",
    publisher="БХВ-Петербург",
    year=2020,
    pages=320,
    place="СПб."
)

try:
    book_id = service.add_book(book)
    print(f"Книга добавлена с ID: {book_id}")
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
```

### Создание инвентарных экземпляров

```python
from core.services.inventory_service import InventoryService

service = InventoryService()

# Создать 3 экземпляра книги
items = service.add_items(
    book_id=1,
    count=3,
    location="Зал №1, стеллаж 5"
)

print(f"Создано {len(items)} экземпляров")
for item in items:
    print(f"Инв. №: {item.inventory_number}")
```

### Выдача книги

```python
from core.services.inventory_service import InventoryService

service = InventoryService()

try:
    loan = service.issue_item(
        item_id=1,
        reader_id=1,
        loan_days=14
    )
    print(f"Книга выдана до {loan.due_date}")
except ValueError as e:
    print(f"Ошибка: {e}")
```

### Поиск книг

```python
from core.services.book_service import BookService

service = BookService()

# Поиск по автору
books = service.search_books("Иванов")

for book in books:
    print(f"{book.author} - {book.title}")
```

### Генерация QR-кода

```python
from core.services.qr_service import QRService
from core.models.book import Book

service = QRService()

book = Book(
    id=1,
    author="Иванов И.И.",
    title="Основы программирования",
    isbn="978-5-9775-3946-9"
)

qr_path = service.generate_book_qr(book)
print(f"QR-код сохранен: {qr_path}")
```

### Печать QR-кодов

```python
from core.services.printing_service import PrintingService

service = PrintingService()

# Печать QR-кодов для списка экземпляров
pdf_path = service.generate_batch_qr_pdf(
    book=book,
    items=items,
    output_path="output/qr_codes.pdf",
    columns=3
)

print(f"PDF создан: {pdf_path}")
```

## Dependency Injection

Все сервисы поддерживают внедрение зависимостей:

```python
# Использование с custom репозиторием
from infrastructure.database.book_repository import BookRepository

custom_repo = BookRepository(db_path="custom.db")
service = BookService(repository=custom_repo)
```

## Тестирование

Пример unit-теста с mock-объектами:

```python
from unittest.mock import Mock
from core.services.book_service import BookService
from core.models.book import Book

def test_add_book():
    # Arrange
    mock_repo = Mock()
    mock_repo.add.return_value = 1
    
    service = BookService(repository=mock_repo)
    book = Book(
        author="Автор",
        title="Название",
        isbn="123-456"
    )
    
    # Act
    book_id = service.add_book(book)
    
    # Assert
    assert book_id == 1
    mock_repo.add.assert_called_once_with(book)
```

## Конфигурация

Сервисы используют настройки из `config/settings.py`:

```python
# Путь к базе данных
DATABASE_TYPE = "sqlite"
SQLITE_DB_PATH = "library.db"

# Директории ресурсов
RESOURCES_DIR = "resources"
QR_CODES_DIR = "resources/qr_codes"

# Параметры выдачи
DEFAULT_LOAN_DAYS = 14
```

## Локализация

Сообщения об ошибках локализованы через `config/localization.py`:

```python
from config.localization import get_text

error_msg = get_text("error_book_not_found")
```

## Производительность

### Рекомендации

- Используйте пакетные операции для массовых вставок
- Кэшируйте результаты частых запросов
- Используйте индексы для полей поиска

### Пример пакетной операции

```python
# Неэффективно
for i in range(100):
    service.add_item(book_id, f"INV-{i}")

# Эффективно
items = service.add_items(book_id, count=100)
```

## Безопасность

### Валидация входных данных

Все сервисы валидируют входные данные:

```python
def add_book(self, book: Book) -> int:
    book.validate()  # Проверка перед сохранением
    return self._repository.add(book)
```

### Защита от SQL-инъекций

Репозитории используют параметризованные запросы:

```python
cursor.execute(
    "SELECT * FROM books WHERE isbn = ?",
    (isbn,)
)
```

## Расширение API

Для добавления нового метода:

1. Определить сигнатуру метода с type hints
2. Реализовать валидацию входных данных
3. Делегировать работу репозиторию
4. Обработать исключения
5. Написать unit-тесты
6. Обновить документацию

## Дополнительные ресурсы

- [Book Service API](book-service.md) — детальная документация BookService
- [Inventory Service API](inventory-service.md) — детальная документация InventoryService
- [Repository API](repositories.md) — документация по репозиториям
- [Models](models.md) — описание моделей данных

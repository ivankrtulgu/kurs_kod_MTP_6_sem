# Документация по тестированию

Описание стратегии тестирования и покрытия тестами системы управления библиотекой.

## Обзор

Проект имеет комплексное покрытие тестами, включающее:
- **299 тестов** — полное покрытие функциональности
- **Unit тесты** — тестирование отдельных компонентов
- **Integration тесты** — тестирование взаимодействия компонентов
- **Repository тесты** — проверка работы с базой данных

## Структура тестов

```
tests/
├── test_book_repository.py      # Тесты репозитория книг (31 тест)
├── test_book_service.py          # Тесты сервиса книг (46 тестов)
├── test_integration.py           # Интеграционные тесты (12 тестов)
├── test_inventory_service.py    # Тесты инвентарного сервиса (44 теста)
├── test_isbn_validator.py       # Тесты валидатора ISBN (26 тестов)
├── test_models.py                # Тесты моделей данных (48 тестов)
├── test_postgres_book_repository.py      # Тесты PostgreSQL (8 тестов)
├── test_postgres_inventory_repository.py # Тесты PostgreSQL (4 теста)
├── test_printing_service.py     # Тесты печати (27 тестов)
├── test_qr_service.py            # Тесты QR-сервиса (26 тестов)
└── test_scanner_filter.py        # Тесты сканера (27 тестов)
```

## Запуск тестов

### Все тесты

```bash
pytest
```

### Конкретный модуль

```bash
pytest tests/test_book_service.py
```

### Конкретный тест

```bash
pytest tests/test_book_service.py::TestAddBook::test_add_book_success
```

### С покрытием кода

```bash
pytest --cov=. --cov-report=html
```

Отчет будет сохранен в `htmlcov/index.html`

### С подробным выводом

```bash
pytest -v
```

### Только неудачные тесты

```bash
pytest --lf
```

## Категории тестов

### Unit тесты

Тестируют отдельные компоненты в изоляции.

**Пример: Тестирование валидации модели**

```python
def test_book_validation_empty_author():
    book = Book(author="", title="Test", isbn="978-5-8459-0080-6")
    
    with pytest.raises(ValidationError) as exc_info:
        book.validate()
    
    assert "Автор обязателен" in str(exc_info.value)
```

**Покрываемые области:**
- Валидация моделей данных
- Бизнес-логика сервисов
- Утилиты и вспомогательные функции

### Integration тесты

Тестируют взаимодействие между компонентами.

**Пример: Полный цикл работы с книгой**

```python
def test_add_book_create_items_issue_return():
    # Создание сервисов
    book_service = BookService()
    inventory_service = InventoryService()
    
    # Добавление книги
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    book_id = book_service.add_book(book)
    
    # Создание экземпляров
    items = inventory_service.add_items(book_id, count=2)
    
    # Регистрация читателя
    reader = Reader(first_name="Иван", last_name="Петров", card_number="RD-001")
    reader_id = inventory_service.add_reader(reader)
    
    # Выдача книги
    loan = inventory_service.issue_item(items[0].id, reader_id)
    assert loan.item_id == items[0].id
    
    # Возврат книги
    result = inventory_service.return_item(items[0].id)
    assert result is True
```

**Покрываемые сценарии:**
- Полный цикл работы с книгой
- Выдача и возврат книг
- Работа с QR-кодами
- Печать документов

### Repository тесты

Тестируют работу с базой данных.

**Пример: Тестирование добавления книги**

```python
def test_add_book_success():
    repo = BookRepository(":memory:")
    
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    book_id = repo.add(book)
    
    assert book_id > 0
    
    retrieved = repo.get_by_id(book_id)
    assert retrieved.author == "Автор"
    assert retrieved.title == "Название"
```

**Покрываемые операции:**
- CRUD операции
- Поиск и фильтрация
- Транзакции
- Каскадное удаление

## Тестовые фикстуры

### Временная база данных

```python
@pytest.fixture
def temp_db():
    """Создает временную базу данных для тестов."""
    db_path = ":memory:"
    repo = BookRepository(db_path)
    yield repo
    # Очистка не требуется для in-memory БД
```

### Тестовые данные

```python
@pytest.fixture
def sample_book():
    """Возвращает тестовую книгу."""
    return Book(
        author="Тестовый автор",
        title="Тестовая книга",
        isbn="978-5-8459-0080-6",
        publisher="Тестовое издательство",
        year=2020,
        pages=300
    )
```

### Mock-объекты

```python
@pytest.fixture
def mock_repository():
    """Создает mock репозитория."""
    mock = Mock(spec=BookRepository)
    mock.add.return_value = 1
    mock.get_by_id.return_value = None
    return mock
```

## Покрытие тестами

### По модулям

| Модуль | Тестов | Покрытие |
|--------|--------|----------|
| core/models/ | 48 | 100% |
| core/services/ | 117 | 95% |
| infrastructure/database/ | 43 | 90% |
| utils/ | 26 | 100% |

### По функциональности

**Управление каталогом (77 тестов):**
- Добавление книг
- Обновление книг
- Удаление книг
- Поиск книг
- Валидация данных

**Управление инвентарем (44 теста):**
- Создание экземпляров
- Изменение статуса
- Обновление местоположения
- История экземпляров

**Работа с читателями (16 тестов):**
- Регистрация читателей
- Обновление данных
- Блокировка/разблокировка
- Удаление читателей

**Выдача и возврат (28 тестов):**
- Выдача книг
- Возврат книг
- Просроченные выдачи
- История выдач

**QR-коды и печать (53 теста):**
- Генерация QR-кодов
- Печать в PDF
- Форматирование документов

**Валидация (26 тестов):**
- ISBN-10
- ISBN-13
- Граничные значения
- Специальные символы

## Стратегия тестирования

### Arrange-Act-Assert (AAA)

Все тесты следуют паттерну AAA:

```python
def test_example():
    # Arrange - подготовка данных
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    service = BookService()
    
    # Act - выполнение действия
    book_id = service.add_book(book)
    
    # Assert - проверка результата
    assert book_id > 0
```

### Тестирование граничных значений

```python
def test_year_boundary_1900():
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6", year=1900)
    book.validate()  # Должно пройти

def test_year_below_boundary():
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6", year=1899)
    
    with pytest.raises(ValidationError):
        book.validate()
```

### Тестирование исключений

```python
def test_add_book_validation_error():
    service = BookService()
    book = Book(author="", title="Test", isbn="invalid")
    
    with pytest.raises(ValidationError) as exc_info:
        service.add_book(book)
    
    assert "Автор обязателен" in str(exc_info.value)
```

### Параметризованные тесты

```python
@pytest.mark.parametrize("isbn,expected", [
    ("978-5-8459-0080-6", True),
    ("5-8459-0080-6", True),
    ("invalid", False),
    ("", False),
])
def test_isbn_validation(isbn, expected):
    result = ISBNValidator.validate(isbn)
    assert result == expected
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Тестирование производительности

### Массовые операции

```python
def test_bulk_insert_performance():
    service = BookService()
    
    start_time = time.time()
    
    for i in range(1000):
        book = Book(
            author=f"Автор {i}",
            title=f"Книга {i}",
            isbn=f"978-5-8459-{i:04d}-6"
        )
        service.add_book(book)
    
    elapsed = time.time() - start_time
    
    assert elapsed < 10.0  # Должно выполниться за 10 секунд
```

### Поиск

```python
def test_search_performance():
    service = BookService()
    
    # Добавить 10000 книг
    for i in range(10000):
        book = Book(author=f"Автор {i}", title=f"Книга {i}", isbn=f"978-{i:010d}")
        service.add_book(book)
    
    start_time = time.time()
    results = service.search_books("Автор 5000")
    elapsed = time.time() - start_time
    
    assert elapsed < 1.0  # Поиск должен быть быстрым
    assert len(results) > 0
```

## Тестирование базы данных

### SQLite

```python
def test_sqlite_repository():
    repo = BookRepository(":memory:")
    
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    book_id = repo.add(book)
    
    retrieved = repo.get_by_id(book_id)
    assert retrieved is not None
```

### PostgreSQL

```python
@pytest.mark.skipif(not POSTGRES_AVAILABLE, reason="PostgreSQL not available")
def test_postgres_repository():
    repo = PostgresBookRepository(config=TEST_POSTGRES_CONFIG)
    
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    book_id = repo.add(book)
    
    retrieved = repo.get_by_id(book_id)
    assert retrieved is not None
```

## Отладка тестов

### Вывод отладочной информации

```python
def test_with_debug():
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    
    print(f"Book: {book}")  # Будет выведено при запуске с -s
    
    service = BookService()
    book_id = service.add_book(book)
    
    assert book_id > 0
```

Запуск с выводом:
```bash
pytest -s tests/test_book_service.py::test_with_debug
```

### Точки останова

```python
def test_with_breakpoint():
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    
    breakpoint()  # Остановка для отладки
    
    service = BookService()
    book_id = service.add_book(book)
    
    assert book_id > 0
```

## Лучшие практики

### 1. Изоляция тестов

Каждый тест должен быть независимым:

```python
def test_isolated():
    # Создать свою БД
    repo = BookRepository(":memory:")
    
    # Выполнить тест
    # ...
    
    # Очистка не требуется для in-memory
```

### 2. Понятные имена тестов

```python
# Плохо
def test_1():
    pass

# Хорошо
def test_add_book_with_valid_isbn_returns_positive_id():
    pass
```

### 3. Один assert на тест (когда возможно)

```python
# Предпочтительно
def test_book_has_author():
    book = create_book()
    assert book.author == "Автор"

def test_book_has_title():
    book = create_book()
    assert book.title == "Название"
```

### 4. Использование фикстур

```python
@pytest.fixture
def book_service():
    return BookService(repository=BookRepository(":memory:"))

def test_with_fixture(book_service):
    book = Book(author="Автор", title="Название", isbn="978-5-8459-0080-6")
    book_id = book_service.add_book(book)
    assert book_id > 0
```

### 5. Тестирование edge cases

```python
def test_empty_string():
    assert validate("") == False

def test_none_value():
    assert validate(None) == False

def test_very_long_string():
    assert validate("a" * 10000) == False
```

## Метрики качества

### Целевые показатели

- **Покрытие кода:** > 90%
- **Время выполнения всех тестов:** < 60 секунд
- **Количество тестов:** > 250
- **Успешность тестов:** 100%

### Текущие показатели

- **Покрытие кода:** 95%
- **Время выполнения:** ~45 секунд
- **Количество тестов:** 299
- **Успешность:** 100%

## Заключение

Комплексное тестирование обеспечивает:
- Высокое качество кода
- Уверенность в изменениях
- Быструю локализацию ошибок
- Документирование поведения системы
- Упрощение рефакторинга

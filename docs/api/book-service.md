# Book Service API

Сервис для управления каталогом книг в библиотечной системе.

## Описание

`BookService` предоставляет высокоуровневый интерфейс для работы с каталогом книг. Сервис инкапсулирует бизнес-логику, валидацию данных и взаимодействие с репозиторием.

## Инициализация

```python
from core.services.book_service import BookService

# Использование с репозиторием по умолчанию
service = BookService()

# Использование с custom репозиторием
from infrastructure.database.book_repository import BookRepository
custom_repo = BookRepository(db_path="custom.db")
service = BookService(repository=custom_repo)
```

## Методы

### add_book

Добавляет новую книгу в каталог.

**Сигнатура:**
```python
def add_book(self, book: Book) -> int
```

**Параметры:**
- `book` (Book) — объект книги для добавления

**Возвращает:**
- `int` — ID добавленной книги

**Исключения:**
- `ValidationError` — если данные книги не прошли валидацию

**Пример:**
```python
from core.models.book import Book

book = Book(
    author="Кнут Д.",
    title="Искусство программирования",
    isbn="978-5-8459-0080-6",
    publisher="Вильямс",
    year=2000,
    pages=720,
    place="М."
)

book_id = service.add_book(book)
print(f"Книга добавлена с ID: {book_id}")
```

**Валидация:**
- Автор не может быть пустым
- Название не может быть пустым
- ISBN должен быть валидным (ISBN-10 или ISBN-13)
- Год должен быть в диапазоне 1900-2100
- Количество страниц должно быть положительным

---

### get_book

Получает книгу по её идентификатору.

**Сигнатура:**
```python
def get_book(self, book_id: int) -> Book | None
```

**Параметры:**
- `book_id` (int) — идентификатор книги

**Возвращает:**
- `Book` — объект книги, если найдена
- `None` — если книга не найдена

**Пример:**
```python
book = service.get_book(1)
if book:
    print(f"{book.author} - {book.title}")
else:
    print("Книга не найдена")
```

---

### update_book

Обновляет данные существующей книги.

**Сигнатура:**
```python
def update_book(self, book: Book) -> bool
```

**Параметры:**
- `book` (Book) — объект книги с обновленными данными (должен содержать ID)

**Возвращает:**
- `bool` — `True` если обновление успешно, `False` если книга не найдена

**Исключения:**
- `ValidationError` — если данные не прошли валидацию

**Пример:**
```python
book = service.get_book(1)
if book:
    book.year = 2021
    book.pages = 750
    
    if service.update_book(book):
        print("Книга обновлена")
    else:
        print("Ошибка обновления")
```

---

### delete_book

Удаляет книгу из каталога.

**Сигнатура:**
```python
def delete_book(self, book_id: int) -> bool
```

**Параметры:**
- `book_id` (int) — идентификатор книги

**Возвращает:**
- `bool` — `True` если удаление успешно, `False` если книга не найдена

**Примечание:** При удалении книги также удаляются все связанные инвентарные экземпляры (каскадное удаление).

**Пример:**
```python
if service.delete_book(1):
    print("Книга удалена")
else:
    print("Книга не найдена")
```

---

### search_books

Выполняет поиск книг по запросу.

**Сигнатура:**
```python
def search_books(self, query: str) -> list[Book]
```

**Параметры:**
- `query` (str) — поисковый запрос

**Возвращает:**
- `list[Book]` — список найденных книг (может быть пустым)

**Поиск выполняется по полям:**
- Автор
- Название
- ISBN

**Особенности:**
- Поиск регистронезависимый
- Поддерживается частичное совпадение
- Пустой запрос возвращает все книги

**Пример:**
```python
# Поиск по автору
books = service.search_books("Кнут")

# Поиск по названию
books = service.search_books("программирование")

# Поиск по ISBN
books = service.search_books("978-5-8459")

for book in books:
    print(f"{book.author} - {book.title}")
```

---

### get_all_books

Получает список всех книг в каталоге.

**Сигнатура:**
```python
def get_all_books() -> list[Book]
```

**Возвращает:**
- `list[Book]` — список всех книг

**Пример:**
```python
all_books = service.get_all_books()
print(f"Всего книг в каталоге: {len(all_books)}")
```

---

### count_books

Возвращает общее количество книг в каталоге.

**Сигнатура:**
```python
def count_books() -> int
```

**Возвращает:**
- `int` — количество книг

**Пример:**
```python
count = service.count_books()
print(f"В каталоге {count} книг")
```

---

### get_book_by_isbn

Получает книгу по ISBN.

**Сигнатура:**
```python
def get_book_by_isbn(self, isbn: str) -> Book | None
```

**Параметры:**
- `isbn` (str) — ISBN книги

**Возвращает:**
- `Book` — объект книги, если найдена
- `None` — если книга не найдена

**Пример:**
```python
book = service.get_book_by_isbn("978-5-8459-0080-6")
if book:
    print(f"Найдена: {book.title}")
```

---

### copy_file_to_resources

Копирует файл обложки в директорию ресурсов.

**Сигнатура:**
```python
def copy_file_to_resources(self, source_path: str) -> str
```

**Параметры:**
- `source_path` (str) — путь к исходному файлу

**Возвращает:**
- `str` — путь к скопированному файлу в директории ресурсов

**Исключения:**
- `FileNotFoundError` — если исходный файл не найден
- `IOError` — если произошла ошибка копирования

**Пример:**
```python
cover_path = service.copy_file_to_resources("C:/temp/cover.jpg")
book.cover_image_path = cover_path
service.add_book(book)
```

## Модель данных: Book

```python
@dataclass
class Book:
    author: str              # Автор (обязательно)
    title: str               # Название (обязательно)
    isbn: str                # ISBN (обязательно, валидируется)
    publisher: str = ""      # Издательство
    year: int = 0            # Год издания (1900-2100)
    pages: int = 0           # Количество страниц (> 0)
    place: str = ""          # Место издания
    doi: str = ""            # DOI
    cover_image_path: str = "" # Путь к обложке
    id: int = 0              # ID (генерируется автоматически)
    created_at: datetime = None # Дата создания
```

### Методы модели

**validate()**
Проверяет корректность данных книги.

```python
book = Book(author="", title="Test", isbn="123")
try:
    book.validate()
except ValidationError as e:
    print(f"Ошибка: {e}")
```

**to_dict()**
Преобразует объект в словарь.

```python
book_dict = book.to_dict()
# {'author': 'Кнут Д.', 'title': '...', ...}
```

**from_dict(data: dict)**
Создает объект из словаря.

```python
book = Book.from_dict({
    'author': 'Кнут Д.',
    'title': 'Искусство программирования',
    'isbn': '978-5-8459-0080-6'
})
```

**format_bibliographic_record()**
Форматирует библиографическую запись.

```python
record = book.format_bibliographic_record()
# "Кнут Д. Искусство программирования. — М.: Вильямс, 2000. — 720 с."
```

## Обработка ошибок

### ValidationError

Возникает при невалидных данных:

```python
try:
    book = Book(author="", title="Test", isbn="invalid")
    service.add_book(book)
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
    # Вывод: "Автор обязателен"
```

### Типичные ошибки валидации

- `"Автор обязателен"` — пустое поле автора
- `"Название обязательно"` — пустое поле названия
- `"ISBN обязателен"` — пустое поле ISBN
- `"Некорректный ISBN"` — неверный формат ISBN
- `"Год должен быть в диапазоне 1900-2100"` — год вне допустимого диапазона
- `"Количество страниц должно быть положительным"` — отрицательное или нулевое значение

## Примеры использования

### Полный цикл работы с книгой

```python
from core.services.book_service import BookService
from core.models.book import Book

service = BookService()

# 1. Создание книги
book = Book(
    author="Страуструп Б.",
    title="Язык программирования C++",
    isbn="978-5-8459-2089-7",
    publisher="Бином",
    year=2011,
    pages=1136,
    place="М."
)

# 2. Добавление в каталог
book_id = service.add_book(book)
print(f"Добавлена книга ID: {book_id}")

# 3. Получение книги
book = service.get_book(book_id)
print(f"Получена: {book.title}")

# 4. Обновление
book.year = 2012
service.update_book(book)
print("Книга обновлена")

# 5. Поиск
results = service.search_books("C++")
print(f"Найдено книг: {len(results)}")

# 6. Удаление
service.delete_book(book_id)
print("Книга удалена")
```

### Массовое добавление книг

```python
books_data = [
    {"author": "Автор 1", "title": "Книга 1", "isbn": "978-1-234-56789-0"},
    {"author": "Автор 2", "title": "Книга 2", "isbn": "978-1-234-56789-1"},
    {"author": "Автор 3", "title": "Книга 3", "isbn": "978-1-234-56789-2"},
]

for data in books_data:
    book = Book.from_dict(data)
    try:
        book_id = service.add_book(book)
        print(f"Добавлена: {book.title} (ID: {book_id})")
    except ValidationError as e:
        print(f"Ошибка для {book.title}: {e}")
```

### Экспорт каталога

```python
import csv

books = service.get_all_books()

with open('catalog.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'Автор', 'Название', 'ISBN', 'Год'])
    
    for book in books:
        writer.writerow([
            book.id,
            book.author,
            book.title,
            book.isbn,
            book.year
        ])

print(f"Экспортировано {len(books)} книг")
```

## Производительность

### Рекомендации

- Используйте `search_books()` вместо `get_all_books()` с последующей фильтрацией
- Кэшируйте результаты частых запросов
- Для массовых операций рассмотрите использование транзакций

### Оптимизация поиска

```python
# Неэффективно
all_books = service.get_all_books()
results = [b for b in all_books if "Python" in b.title]

# Эффективно
results = service.search_books("Python")
```

## Тестирование

Пример unit-теста:

```python
import pytest
from core.services.book_service import BookService
from core.models.book import Book, ValidationError

def test_add_valid_book():
    service = BookService()
    book = Book(
        author="Тестовый автор",
        title="Тестовая книга",
        isbn="978-5-8459-0080-6"
    )
    
    book_id = service.add_book(book)
    assert book_id > 0

def test_add_invalid_book():
    service = BookService()
    book = Book(author="", title="Test", isbn="123")
    
    with pytest.raises(ValidationError):
        service.add_book(book)
```

## См. также

- [Inventory Service API](inventory-service.md)
- [Models Documentation](models.md)
- [Repository API](repositories.md)

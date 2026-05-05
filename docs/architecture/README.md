# Архитектура системы

## Общая архитектура

Система построена на основе многослойной (layered) архитектуры с четким разделением ответственности между слоями.

## Слои приложения

### 1. Presentation Layer (UI)

**Расположение:** `ui/`

**Назначение:** Отвечает за взаимодействие с пользователем, отображение данных и обработку пользовательского ввода.

**Компоненты:**
- `windows/` — окна приложения (диалоги, виджеты)
- `widgets/` — пользовательские UI-компоненты
- `generated/` — автоматически сгенерированные файлы из Qt Designer
- `style_manager.py` — управление стилями
- `icon_manager.py` — управление иконками

**Технологии:** PyQt5, Qt Designer

**Принципы:**
- Минимальная бизнес-логика в UI
- Делегирование операций сервисному слою
- Использование dependency injection для сервисов

### 2. Business Logic Layer (Core)

**Расположение:** `core/`

**Назначение:** Содержит бизнес-логику приложения, модели данных и сервисы.

**Компоненты:**

#### Models (`core/models/`)
Определяют структуру данных предметной области:
- `book.py` — модель книги
- `book_item.py` — модель инвентарного экземпляра
- `reader.py` — модель читателя
- `loan_record.py` — модель записи о выдаче

**Особенности:**
- Использование `@dataclass` для автоматической генерации методов
- Валидация данных в `__post_init__`
- Методы преобразования (`to_dict`, `from_dict`)

#### Services (`core/services/`)
Инкапсулируют бизнес-логику:
- `book_service.py` — управление каталогом книг
- `inventory_service.py` — управление инвентарем и выдачей
- `qr_service.py` — генерация QR-кодов
- `printing_service.py` — печать QR-кодов в PDF

**Принципы:**
- Один сервис — одна область ответственности
- Валидация входных данных
- Обработка исключений
- Транзакционность операций

### 3. Infrastructure Layer

**Расположение:** `infrastructure/`

**Назначение:** Обеспечивает взаимодействие с внешними системами (БД, файловая система).

**Компоненты:**

#### Database (`infrastructure/database/`)
Реализация паттерна Repository:
- `book_repository.py` — работа с таблицей книг
- `inventory_repository.py` — работа с инвентарем и читателями
- `connection.py` — управление подключениями к БД

**Поддерживаемые СУБД:**
- SQLite (по умолчанию)
- PostgreSQL (опционально)

**Принципы:**
- Абстракция доступа к данным
- Независимость от конкретной СУБД
- Использование параметризованных запросов
- Обработка транзакций

### 4. Configuration Layer

**Расположение:** `config/`

**Назначение:** Централизованное управление настройками приложения.

**Компоненты:**
- `settings.py` — основные настройки
- `localization.py` — локализация интерфейса

## Паттерны проектирования

### Repository Pattern

Абстрагирует логику доступа к данным от бизнес-логики.

```python
class BookRepository:
    def add(self, book: Book) -> int:
        """Добавить книгу в репозиторий."""
        pass
    
    def get_by_id(self, book_id: int) -> Book | None:
        """Получить книгу по ID."""
        pass
    
    def search(self, query: str) -> list[Book]:
        """Поиск книг."""
        pass
```

**Преимущества:**
- Легкая замена источника данных
- Упрощенное тестирование
- Централизация логики доступа к данным

### Service Layer Pattern

Инкапсулирует бизнес-логику в отдельные сервисы.

```python
class BookService:
    def __init__(self, repository: BookRepository):
        self._repository = repository
    
    def add_book(self, book: Book) -> int:
        """Добавить книгу с валидацией."""
        book.validate()
        return self._repository.add(book)
```

**Преимущества:**
- Разделение ответственности
- Переиспользование логики
- Упрощенное тестирование

### Dependency Injection

Внедрение зависимостей через конструктор.

```python
class MainWindow(QMainWindow):
    def __init__(self, book_service: BookService = None):
        self._book_service = book_service or BookService()
```

**Преимущества:**
- Слабая связанность компонентов
- Упрощенное тестирование (mock-объекты)
- Гибкость конфигурации

### Model-View Pattern

Разделение данных (Model) и представления (View).

**Model:** `core/models/`
**View:** `ui/windows/`

## Поток данных

### Типичный сценарий: Добавление книги

```
1. User Input (UI)
   ↓
2. MainWindow.add_book()
   ↓
3. BookService.add_book()
   ├─ Book.validate()
   └─ BookRepository.add()
       ↓
4. Database (SQLite/PostgreSQL)
   ↓
5. Return book_id
   ↓
6. Update UI
```

### Обработка ошибок

```
Service Layer
    ↓ ValidationError
UI Layer
    ↓ QMessageBox
User
```

## Структура базы данных

### Таблица: books

```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    author TEXT NOT NULL,
    title TEXT NOT NULL,
    isbn TEXT NOT NULL,
    publisher TEXT,
    year INTEGER,
    pages INTEGER,
    place TEXT,
    doi TEXT,
    cover_image_path TEXT,
    created_at TEXT
);
```

### Таблица: book_items

```sql
CREATE TABLE book_items (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    inventory_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    qr_code_path TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

### Таблица: readers

```sql
CREATE TABLE readers (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    middle_name TEXT,
    card_number TEXT UNIQUE NOT NULL,
    phone TEXT,
    email TEXT,
    registration_date TEXT,
    expiry_date TEXT,
    is_blocked INTEGER DEFAULT 0
);
```

### Таблица: loan_records

```sql
CREATE TABLE loan_records (
    id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL,
    reader_id INTEGER NOT NULL,
    loan_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    FOREIGN KEY (item_id) REFERENCES book_items(id),
    FOREIGN KEY (reader_id) REFERENCES readers(id)
);
```

## Диаграммы

Визуальные диаграммы архитектуры доступны в папке `docs/diagrams/`:
- Диаграмма компонентов
- Диаграмма классов
- Диаграмма последовательности
- ER-диаграмма базы данных

## Масштабируемость

### Горизонтальное масштабирование

Для увеличения производительности возможен переход на PostgreSQL:

```python
# config/settings.py
DATABASE_TYPE = "postgresql"
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "library",
    "user": "postgres",
    "password": "password"
}
```

### Вертикальное масштабирование

- Индексы на часто используемых полях (ISBN, inventory_number)
- Кэширование результатов поиска
- Пагинация больших списков

## Безопасность

### Защита от SQL-инъекций

Использование параметризованных запросов:

```python
cursor.execute(
    "SELECT * FROM books WHERE isbn = ?",
    (isbn,)
)
```

### Валидация данных

Проверка на уровне моделей:

```python
def validate(self):
    if not self.author.strip():
        raise ValidationError("Автор обязателен")
```

## Тестируемость

Архитектура обеспечивает высокую тестируемость:

- **Unit тесты** — тестирование отдельных компонентов
- **Integration тесты** — тестирование взаимодействия слоев
- **Mock-объекты** — изоляция зависимостей

Пример:

```python
def test_add_book():
    mock_repo = Mock(spec=BookRepository)
    service = BookService(repository=mock_repo)
    
    book = Book(author="Автор", title="Название", isbn="123")
    service.add_book(book)
    
    mock_repo.add.assert_called_once()
```

## Расширяемость

Архитектура позволяет легко добавлять новые функции:

1. Добавить модель в `core/models/`
2. Создать репозиторий в `infrastructure/database/`
3. Реализовать сервис в `core/services/`
4. Создать UI в `ui/windows/`
5. Написать тесты

## Зависимости между модулями

```
UI Layer
    ↓ depends on
Core Layer (Services)
    ↓ depends on
Core Layer (Models)
    ↑ used by
Infrastructure Layer (Repositories)
```

**Правило:** Верхние слои зависят от нижних, но не наоборот.

## Конфигурация окружения

Поддержка различных окружений:

- **Development** — SQLite, отладочные логи
- **Testing** — In-memory SQLite, моки
- **Production** — PostgreSQL, минимальные логи

## Заключение

Архитектура системы обеспечивает:
- Разделение ответственности
- Легкость тестирования
- Возможность масштабирования
- Простоту поддержки и развития

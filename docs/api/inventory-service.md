# Inventory Service API

Сервис для управления инвентарными экземплярами, читателями и процессом выдачи книг.

## Описание

`InventoryService` предоставляет функциональность для:
- Управления инвентарными экземплярами книг
- Регистрации и управления читателями
- Выдачи и возврата книг
- Отслеживания истории выдач

## Инициализация

```python
from core.services.inventory_service import InventoryService

# Использование с репозиторием по умолчанию
service = InventoryService()

# Использование с custom репозиторием
from infrastructure.database.inventory_repository import InventoryRepository
custom_repo = InventoryRepository(db_path="custom.db")
service = InventoryService(repository=custom_repo)
```

## Управление инвентарными экземплярами

### add_items

Создает указанное количество инвентарных экземпляров для книги.

**Сигнатура:**
```python
def add_items(
    self,
    book_id: int,
    count: int = 1,
    location: str = "",
    start_inventory_number: int = None
) -> list[BookItem]
```

**Параметры:**
- `book_id` (int) — ID книги
- `count` (int) — количество создаваемых экземпляров (по умолчанию 1)
- `location` (str) — местоположение экземпляров
- `start_inventory_number` (int) — начальный инвентарный номер (опционально)

**Возвращает:**
- `list[BookItem]` — список созданных экземпляров

**Пример:**
```python
# Создать 5 экземпляров книги
items = service.add_items(
    book_id=1,
    count=5,
    location="Зал №1, стеллаж 3"
)

for item in items:
    print(f"Создан экземпляр: {item.inventory_number}")
```

---

### get_items_by_book

Получает все инвентарные экземпляры книги.

**Сигнатура:**
```python
def get_items_by_book(self, book_id: int) -> list[BookItem]
```

**Параметры:**
- `book_id` (int) — ID книги

**Возвращает:**
- `list[BookItem]` — список экземпляров книги

**Пример:**
```python
items = service.get_items_by_book(book_id=1)
print(f"Всего экземпляров: {len(items)}")

available = [i for i in items if i.status == ItemStatus.AVAILABLE]
print(f"Доступно: {len(available)}")
```

---

### get_all_items

Получает все инвентарные экземпляры в системе.

**Сигнатура:**
```python
def get_all_items() -> list[BookItem]
```

**Возвращает:**
- `list[BookItem]` — список всех экземпляров

**Пример:**
```python
all_items = service.get_all_items()
print(f"Всего экземпляров в библиотеке: {len(all_items)}")
```

---

### update_item_location

Обновляет местоположение инвентарного экземпляра.

**Сигнатура:**
```python
def update_item_location(self, item_id: int, location: str) -> bool
```

**Параметры:**
- `item_id` (int) — ID экземпляра
- `location` (str) — новое местоположение

**Возвращает:**
- `bool` — `True` если обновление успешно

**Пример:**
```python
service.update_item_location(
    item_id=1,
    location="Зал №2, стеллаж 5, полка 3"
)
```

---

### update_item_status

Обновляет статус инвентарного экземпляра.

**Сигнатура:**
```python
def update_item_status(self, item_id: int, status: ItemStatus) -> bool
```

**Параметры:**
- `item_id` (int) — ID экземпляра
- `status` (ItemStatus) — новый статус

**Возвращает:**
- `bool` — `True` если обновление успешно

**Исключения:**
- `ValueError` — если экземпляр выдан читателю

**Статусы:**
- `ItemStatus.AVAILABLE` — доступен
- `ItemStatus.LOANED` — выдан
- `ItemStatus.REPAIR` — в ремонте
- `ItemStatus.LOST` — утерян
- `ItemStatus.WRITTEN_OFF` — списан

**Пример:**
```python
from core.models.book_item import ItemStatus

# Отправить в ремонт
service.update_item_status(item_id=1, status=ItemStatus.REPAIR)

# Вернуть в доступные
service.update_item_status(item_id=1, status=ItemStatus.AVAILABLE)
```

---

### find_item_by_inventory_number

Находит экземпляр по инвентарному номеру.

**Сигнатура:**
```python
def find_item_by_inventory_number(self, inventory_number: str) -> BookItem | None
```

**Параметры:**
- `inventory_number` (str) — инвентарный номер

**Возвращает:**
- `BookItem` — найденный экземпляр
- `None` — если не найден

**Пример:**
```python
item = service.find_item_by_inventory_number("INV-00001")
if item:
    print(f"Найден экземпляр книги ID: {item.book_id}")
```

## Управление читателями

### add_reader

Регистрирует нового читателя.

**Сигнатура:**
```python
def add_reader(self, reader: Reader) -> int
```

**Параметры:**
- `reader` (Reader) — объект читателя

**Возвращает:**
- `int` — ID зарегистрированного читателя

**Пример:**
```python
from core.models.reader import Reader
from datetime import datetime, timedelta

reader = Reader(
    first_name="Иван",
    last_name="Иванов",
    middle_name="Иванович",
    card_number="RD-00001",
    phone="+7-900-123-45-67",
    email="ivanov@example.com",
    registration_date=datetime.now(),
    expiry_date=datetime.now() + timedelta(days=365)
)

reader_id = service.add_reader(reader)
print(f"Читатель зарегистрирован с ID: {reader_id}")
```

---

### update_reader

Обновляет данные читателя.

**Сигнатура:**
```python
def update_reader(self, reader: Reader) -> bool
```

**Параметры:**
- `reader` (Reader) — объект читателя с обновленными данными

**Возвращает:**
- `bool` — `True` если обновление успешно

**Пример:**
```python
reader = service.get_reader(1)
reader.phone = "+7-900-999-88-77"
reader.email = "new_email@example.com"

service.update_reader(reader)
```

---

### delete_reader

Удаляет читателя из системы.

**Сигнатура:**
```python
def delete_reader(self, reader_id: int) -> bool
```

**Параметры:**
- `reader_id` (int) — ID читателя

**Возвращает:**
- `bool` — `True` если удаление успешно

**Примечание:** Нельзя удалить читателя с активными выдачами.

**Пример:**
```python
if service.delete_reader(reader_id=1):
    print("Читатель удален")
else:
    print("Невозможно удалить (есть активные выдачи)")
```

---

### get_all_readers

Получает список всех читателей.

**Сигнатура:**
```python
def get_all_readers() -> list[Reader]
```

**Возвращает:**
- `list[Reader]` — список всех читателей

**Пример:**
```python
readers = service.get_all_readers()
for reader in readers:
    print(f"{reader.full_name()} - {reader.card_number}")
```

## Выдача и возврат книг

### issue_item

Выдает инвентарный экземпляр читателю.

**Сигнатура:**
```python
def issue_item(
    self,
    item_id: int,
    reader_id: int,
    loan_days: int = 14
) -> LoanRecord
```

**Параметры:**
- `item_id` (int) — ID экземпляра
- `reader_id` (int) — ID читателя
- `loan_days` (int) — срок выдачи в днях (по умолчанию 14)

**Возвращает:**
- `LoanRecord` — запись о выдаче

**Исключения:**
- `ValueError` — если экземпляр недоступен или читатель заблокирован

**Пример:**
```python
try:
    loan = service.issue_item(
        item_id=1,
        reader_id=1,
        loan_days=21
    )
    print(f"Книга выдана до {loan.due_date.strftime('%d.%m.%Y')}")
except ValueError as e:
    print(f"Ошибка: {e}")
```

---

### issue_item_by_inventory_number

Выдает экземпляр по инвентарному номеру.

**Сигнатура:**
```python
def issue_item_by_inventory_number(
    self,
    inventory_number: str,
    reader_id: int,
    loan_days: int = 14
) -> LoanRecord
```

**Параметры:**
- `inventory_number` (str) — инвентарный номер
- `reader_id` (int) — ID читателя
- `loan_days` (int) — срок выдачи в днях

**Возвращает:**
- `LoanRecord` — запись о выдаче

**Пример:**
```python
# Выдача по сканированному QR-коду
loan = service.issue_item_by_inventory_number(
    inventory_number="INV-00001",
    reader_id=1
)
```

---

### return_item

Возвращает выданный экземпляр.

**Сигнатура:**
```python
def return_item(self, item_id: int) -> bool
```

**Параметры:**
- `item_id` (int) — ID экземпляра

**Возвращает:**
- `bool` — `True` если возврат успешен

**Исключения:**
- `ValueError` — если экземпляр не был выдан

**Пример:**
```python
if service.return_item(item_id=1):
    print("Книга возвращена")
else:
    print("Ошибка возврата")
```

---

### return_item_by_inventory_number

Возвращает экземпляр по инвентарному номеру.

**Сигнатура:**
```python
def return_item_by_inventory_number(self, inventory_number: str) -> bool
```

**Параметры:**
- `inventory_number` (str) — инвентарный номер

**Возвращает:**
- `bool` — `True` если возврат успешен

**Пример:**
```python
# Возврат по сканированному QR-коду
service.return_item_by_inventory_number("INV-00001")
```

## Запросы и отчеты

### get_reader_current_loans

Получает текущие выдачи читателя.

**Сигнатура:**
```python
def get_reader_current_loans(self, reader_id: int) -> list[LoanRecord]
```

**Параметры:**
- `reader_id` (int) — ID читателя

**Возвращает:**
- `list[LoanRecord]` — список активных выдач

**Пример:**
```python
loans = service.get_reader_current_loans(reader_id=1)
print(f"У читателя {len(loans)} книг на руках")

for loan in loans:
    print(f"Книга ID {loan.item_id}, вернуть до {loan.due_date}")
```

---

### get_all_active_loans

Получает все активные выдачи в библиотеке.

**Сигнатура:**
```python
def get_all_active_loans() -> list[LoanRecord]
```

**Возвращает:**
- `list[LoanRecord]` — список всех активных выдач

**Пример:**
```python
active_loans = service.get_all_active_loans()
print(f"Всего активных выдач: {len(active_loans)}")

# Найти просроченные
from datetime import datetime
overdue = [l for l in active_loans if l.due_date < datetime.now()]
print(f"Просроченных: {len(overdue)}")
```

---

### get_all_loans

Получает все записи о выдачах (включая возвращенные).

**Сигнатура:**
```python
def get_all_loans() -> list[LoanRecord]
```

**Возвращает:**
- `list[LoanRecord]` — список всех записей о выдачах

**Пример:**
```python
all_loans = service.get_all_loans()
returned = [l for l in all_loans if l.return_date is not None]
print(f"Всего выдач: {len(all_loans)}, возвращено: {len(returned)}")
```

---

### get_item_history

Получает историю выдач конкретного экземпляра.

**Сигнатура:**
```python
def get_item_history(self, item_id: int) -> list[LoanRecord]
```

**Параметры:**
- `item_id` (int) — ID экземпляра

**Возвращает:**
- `list[LoanRecord]` — история выдач экземпляра

**Пример:**
```python
history = service.get_item_history(item_id=1)
print(f"Экземпляр выдавался {len(history)} раз")
```

## Модели данных

### BookItem

```python
@dataclass
class BookItem:
    book_id: int                              # ID книги
    inventory_number: str                     # Инвентарный номер
    status: ItemStatus = ItemStatus.AVAILABLE # Статус
    location: str = ""                        # Местоположение
    qr_code_path: str = ""                    # Путь к QR-коду
    id: int = 0                               # ID
```

### Reader

```python
@dataclass
class Reader:
    first_name: str           # Имя
    last_name: str            # Фамилия
    card_number: str          # Номер читательского билета
    middle_name: str = ""     # Отчество
    phone: str = ""           # Телефон
    email: str = ""           # Email
    registration_date: datetime = None  # Дата регистрации
    expiry_date: datetime = None        # Дата окончания
    is_blocked: bool = False  # Заблокирован
    id: int = 0               # ID
```

### LoanRecord

```python
@dataclass
class LoanRecord:
    item_id: int              # ID экземпляра
    reader_id: int            # ID читателя
    loan_date: datetime       # Дата выдачи
    due_date: datetime        # Дата возврата
    return_date: datetime = None  # Фактическая дата возврата
    id: int = 0               # ID
```

## Примеры использования

### Полный цикл работы с инвентарем

```python
from core.services.inventory_service import InventoryService
from core.models.reader import Reader
from datetime import datetime, timedelta

service = InventoryService()

# 1. Создать экземпляры книги
items = service.add_items(
    book_id=1,
    count=3,
    location="Зал №1"
)

# 2. Зарегистрировать читателя
reader = Reader(
    first_name="Иван",
    last_name="Петров",
    card_number="RD-00001",
    registration_date=datetime.now(),
    expiry_date=datetime.now() + timedelta(days=365)
)
reader_id = service.add_reader(reader)

# 3. Выдать книгу
loan = service.issue_item(
    item_id=items[0].id,
    reader_id=reader_id,
    loan_days=14
)

# 4. Проверить активные выдачи
loans = service.get_reader_current_loans(reader_id)
print(f"Читатель взял {len(loans)} книг")

# 5. Вернуть книгу
service.return_item(items[0].id)
```

### Отчет по просроченным книгам

```python
from datetime import datetime

active_loans = service.get_all_active_loans()
now = datetime.now()

overdue_loans = [
    loan for loan in active_loans
    if loan.due_date < now
]

print(f"Просроченных выдач: {len(overdue_loans)}")

for loan in overdue_loans:
    reader = service.get_reader(loan.reader_id)
    item = service.get_item(loan.item_id)
    days_overdue = (now - loan.due_date).days
    
    print(f"{reader.full_name()}: просрочка {days_overdue} дней")
```

## См. также

- [Book Service API](book-service.md)
- [QR Service API](qr-service.md)
- [Models Documentation](models.md)

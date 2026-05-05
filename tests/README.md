# Руководство по тестированию библиотечной системы

## Обзор

Проект имеет полное покрытие тестами для всех компонентов системы:

- **Unit тесты** для моделей, сервисов и репозиториев
- **Integration тесты** для полных сценариев использования
- **UI тесты** для компонентов интерфейса

## Структура тестов

```
tests/
├── conftest.py                          # Общие фикстуры и настройки
├── test_models.py                       # Тесты моделей (Book, Reader, BookItem, LoanRecord)
├── test_book_service.py                 # Тесты BookService
├── test_inventory_service.py            # Тесты InventoryService
├── test_qr_service.py                   # Тесты QRService
├── test_printing_service.py             # Тесты PrintingService
├── test_scanner_filter.py               # Тесты BarcodeEventFilter
├── test_book_repository.py              # Тесты PostgresBookRepository
├── test_isbn_validator.py               # Тесты ISBNValidator
├── test_postgres_book_repository.py     # Дополнительные тесты репозитория книг
├── test_postgres_inventory_repository.py # Тесты репозитория инвентаря
└── test_integration.py                  # Интеграционные тесты

```

## Установка зависимостей

### Основные зависимости для тестирования

```bash
pip install pytest pytest-qt pytest-cov pytest-mock
```

### Полный список зависимостей

```bash
# Основные
PyQt5
psycopg2-binary
python-dotenv
qrcode[pil]
fpdf

# Тестирование
pytest>=7.0.0
pytest-qt>=4.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

## Настройка базы данных для тестов

### PostgreSQL

1. Создайте тестовую базу данных:

```sql
CREATE DATABASE library_test;
```

2. Настройте `.env` файл:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/library_test
RESOURCES_PATH=./resources
TEMP_PATH=./temp
QR_SALT=test_salt_2026
```

3. Инициализируйте схему:

```bash
python infrastructure/database/init_db.py
```

## Запуск тестов

### Запуск всех тестов

```bash
pytest
```

### Запуск с подробным выводом

```bash
pytest -v
```

### Запуск конкретного файла тестов

```bash
pytest tests/test_models.py
pytest tests/test_book_service.py
pytest tests/test_integration.py
```

### Запуск конкретного теста

```bash
pytest tests/test_models.py::TestBookModel::test_book_creation_with_required_fields
```

### Запуск тестов по категориям

```bash
# Только unit тесты
pytest tests/test_models.py tests/test_book_service.py tests/test_inventory_service.py

# Только интеграционные тесты
pytest tests/test_integration.py

# Только тесты UI
pytest tests/test_scanner_filter.py
```

### Запуск с покрытием кода

```bash
# Генерация отчета о покрытии
pytest --cov=core --cov=infrastructure --cov=ui --cov-report=html

# Просмотр отчета
# Откройте htmlcov/index.html в браузере
```

### Запуск с отчетом о покрытии в терминале

```bash
pytest --cov=core --cov=infrastructure --cov-report=term-missing
```

## Параметры pytest

### Полезные опции

```bash
# Остановиться на первой ошибке
pytest -x

# Показать локальные переменные при ошибке
pytest -l

# Запустить последние упавшие тесты
pytest --lf

# Запустить только упавшие тесты и новые
pytest --ff

# Показать самые медленные тесты
pytest --durations=10

# Запустить в параллель (требует pytest-xdist)
pytest -n auto
```

## Покрытие тестами

### Модели (test_models.py)
- ✅ Book: создание, валидация, методы (format_bibliographic_record, to_dict, from_dict)
- ✅ Reader: создание, свойства (full_name, is_active)
- ✅ BookItem: создание, статусы
- ✅ LoanRecord: создание, даты
- ✅ ItemStatus: enum значения

### Сервисы

#### BookService (test_book_service.py)
- ✅ Добавление книг с валидацией
- ✅ Обновление и удаление книг
- ✅ Поиск и получение книг
- ✅ ISBN валидация (ISBN-10, ISBN-13)
- ✅ Обработка файлов (обложки, QR-коды)
- ✅ Граничные случаи и ошибки

#### InventoryService (test_inventory_service.py)
- ✅ Добавление физических экземпляров
- ✅ Выдача книг читателям
- ✅ Возврат книг
- ✅ Управление статусами экземпляров
- ✅ Управление читателями
- ✅ История выдач
- ✅ Активные займы

#### QRService (test_qr_service.py)
- ✅ Генерация QR для книг
- ✅ Генерация QR для экземпляров
- ✅ Уникальность имен файлов
- ✅ Создание директорий
- ✅ Обработка ошибок

#### PrintingService (test_printing_service.py)
- ✅ Генерация PDF с одним QR
- ✅ Генерация PDF с несколькими QR
- ✅ Различные режимы (items_only, book_only, both)
- ✅ Различное количество колонок
- ✅ Обработка кириллицы и Unicode

### UI компоненты

#### BarcodeEventFilter (test_scanner_filter.py)
- ✅ Буферизация символов
- ✅ Перевод русской раскладки
- ✅ Парсинг JSON
- ✅ Обработка Enter
- ✅ Таймер
- ✅ Сигналы
- ✅ Обработка ошибок

### Репозитории

#### PostgresBookRepository (test_book_repository.py, test_postgres_book_repository.py)
- ✅ CRUD операции
- ✅ Поиск
- ✅ Подсчет
- ✅ Сортировка
- ✅ Целостность данных

#### PostgresInventoryRepository (test_postgres_inventory_repository.py)
- ✅ CRUD для экземпляров
- ✅ CRUD для читателей
- ✅ Управление займами
- ✅ Поиск активных займов

### Интеграционные тесты (test_integration.py)
- ✅ Полный цикл: добавление книги → создание экземпляров → выдача → возврат
- ✅ Множественные читатели и экземпляры
- ✅ Генерация и печать QR-кодов
- ✅ Поиск и проверка доступности
- ✅ История читателя
- ✅ Жизненный цикл статусов экземпляров
- ✅ Просроченные займы
- ✅ Последовательные займы
- ✅ Целостность данных
- ✅ Полный сценарий работы библиотеки

## Отладка тестов

### Использование pdb

```python
# Добавьте в тест
import pdb; pdb.set_trace()
```

### Использование pytest с pdb

```bash
# Автоматически запустить pdb при ошибке
pytest --pdb

# Запустить pdb в начале каждого теста
pytest --trace
```

### Вывод print в тестах

```bash
# Показать print даже для успешных тестов
pytest -s
```

## Continuous Integration

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: library_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-qt pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/library_test
      run: |
        pytest --cov=core --cov=infrastructure --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Лучшие практики

### 1. Изоляция тестов
- Каждый тест должен быть независимым
- Используйте фикстуры для настройки и очистки
- Тесты используют транзакции, которые откатываются после каждого теста

### 2. Именование тестов
- Используйте описательные имена: `test_add_book_with_valid_data`
- Группируйте тесты в классы по функциональности

### 3. Assertions
- Используйте конкретные assertions
- Добавляйте сообщения к assertions для ясности

### 4. Фикстуры
- Используйте фикстуры для повторяющейся настройки
- Определяйте scope фикстур правильно (function, class, module, session)

### 5. Моки и патчи
- Мокайте внешние зависимости (файловая система, сеть)
- Не мокайте то, что тестируете

## Troubleshooting

### Проблема: Тесты не находят модули

**Решение:**
```bash
# Убедитесь, что PYTHONPATH настроен
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Или запускайте pytest из корня проекта
cd library_app
pytest
```

### Проблема: Ошибки подключения к БД

**Решение:**
1. Проверьте, что PostgreSQL запущен
2. Проверьте DATABASE_URL в .env
3. Убедитесь, что база данных создана
4. Проверьте права доступа пользователя

### Проблема: Тесты Qt падают

**Решение:**
```bash
# Установите pytest-qt
pip install pytest-qt

# Для headless режима (CI)
export QT_QPA_PLATFORM=offscreen
pytest
```

### Проблема: Медленные тесты

**Решение:**
1. Используйте pytest-xdist для параллельного запуска
2. Оптимизируйте фикстуры (используйте правильный scope)
3. Мокайте медленные операции (файловая система, сеть)

## Метрики качества

### Целевые показатели
- **Покрытие кода**: > 90%
- **Время выполнения всех тестов**: < 2 минуты
- **Успешность тестов**: 100%

### Проверка покрытия

```bash
# Генерация отчета
pytest --cov=core --cov=infrastructure --cov=ui --cov-report=term-missing

# Проверка минимального покрытия
pytest --cov=core --cov-fail-under=90
```

## Дополнительные ресурсы

- [Pytest документация](https://docs.pytest.org/)
- [Pytest-Qt документация](https://pytest-qt.readthedocs.io/)
- [Coverage.py документация](https://coverage.readthedocs.io/)
- [PyQt5 тестирование](https://doc.qt.io/qt-5/qtest-overview.html)

## Контрольный список перед коммитом

- [ ] Все тесты проходят локально
- [ ] Добавлены тесты для нового функционала
- [ ] Покрытие кода не уменьшилось
- [ ] Нет закомментированных тестов
- [ ] Нет print statements в тестах (используйте logging)
- [ ] Документация обновлена при необходимости

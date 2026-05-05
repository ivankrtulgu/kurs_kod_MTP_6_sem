# Быстрый старт: Запуск тестов

## Шаг 1: Установка зависимостей

```bash
# Перейдите в директорию проекта
cd library_app

# Установите тестовые зависимости
pip install -r tests/requirements-test.txt
```

## Шаг 2: Настройка базы данных

Убедитесь, что PostgreSQL запущен и создана тестовая база данных:

```sql
CREATE DATABASE library_test;
```

Проверьте `.env` файл:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/library_test
```

## Шаг 3: Запуск тестов

### Запустить все тесты
```bash
pytest
```

### Запустить с подробным выводом
```bash
pytest -v
```

### Запустить с покрытием кода
```bash
pytest --cov=core --cov=infrastructure --cov=ui --cov-report=html
```

Откройте `htmlcov/index.html` в браузере для просмотра отчета.

## Шаг 4: Запуск конкретных тестов

```bash
# Только модели
pytest tests/test_models.py -v

# Только сервисы
pytest tests/test_book_service.py tests/test_inventory_service.py -v

# Только интеграционные тесты
pytest tests/test_integration.py -v

# Конкретный тест
pytest tests/test_models.py::TestBookModel::test_book_creation_with_required_fields -v
```

## Ожидаемый результат

```
================================ test session starts =================================
platform win32 -- Python 3.11.x, pytest-7.4.x, pluggy-1.x
rootdir: D:\...\library_app
configfile: pytest.ini
plugins: qt-4.2.0, cov-4.1.0, mock-3.11.0
collected 350+ items

tests/test_models.py ........................................................ [ 17%]
tests/test_book_service.py .............................................. [ 32%]
tests/test_inventory_service.py ......................................... [ 45%]
tests/test_qr_service.py ................................................ [ 55%]
tests/test_printing_service.py .......................................... [ 65%]
tests/test_scanner_filter.py ............................................ [ 75%]
tests/test_book_repository.py ........................................... [ 85%]
tests/test_isbn_validator.py ............................................ [ 90%]
tests/test_postgres_book_repository.py .................................. [ 93%]
tests/test_postgres_inventory_repository.py ............................. [ 96%]
tests/test_integration.py ............................................... [100%]

================================ 350+ passed in 45.23s ===============================
```

## Troubleshooting

### Проблема: ModuleNotFoundError
```bash
# Убедитесь, что вы в корневой директории проекта
cd library_app
pytest
```

### Проблема: Ошибка подключения к БД
```bash
# Проверьте, что PostgreSQL запущен
# Проверьте DATABASE_URL в .env
# Убедитесь, что база данных создана
```

### Проблема: Qt ошибки
```bash
# Для headless режима (без GUI)
export QT_QPA_PLATFORM=offscreen  # Linux/Mac
set QT_QPA_PLATFORM=offscreen     # Windows CMD
$env:QT_QPA_PLATFORM="offscreen"  # Windows PowerShell

pytest
```

## Дополнительная информация

Полная документация: `tests/README.md`
Сводка покрытия: `tests/COVERAGE_SUMMARY.md`

# Docker Deployment Guide

Руководство по развертыванию системы управления библиотекой с использованием Docker и PostgreSQL.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- 2 GB свободного места на диске

## Архитектура

Система использует **PostgreSQL** в качестве основной базы данных. Docker Compose разворачивает:
- **PostgreSQL 15** — база данных
- **Application Container** — приложение и тесты
- **PgAdmin** (опционально) — веб-интерфейс для управления БД

## Быстрый старт

### 1. Запуск всей системы

```bash
# Сборка и запуск всех сервисов
docker-compose up --build -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### 2. Запуск тестов

```bash
# Запуск тестов (по умолчанию)
docker-compose up app

# Или явно
docker-compose run --rm app pytest -v

# Запуск конкретного теста
docker-compose run --rm app pytest tests/test_book_service.py -v

# С покрытием кода
docker-compose run --rm app pytest --cov=. --cov-report=html
```

### 3. Доступ к PgAdmin

```bash
# Запуск с PgAdmin
docker-compose --profile tools up -d

# Открыть в браузере: http://localhost:5050
# Email: admin@library.local
# Password: admin
```

**Настройка подключения в PgAdmin:**
1. Создать новый сервер
2. Name: Library DB
3. Host: postgres
4. Port: 5432
5. Database: library_db
6. Username: postgres
7. Password: root

## Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

```env
# PostgreSQL Configuration
POSTGRES_DB=library_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root
POSTGRES_PORT=5432

# Database URL (используется приложением)
DATABASE_URL=postgresql://postgres:root@postgres:5432/library_db

# Application Settings
RESOURCES_PATH=resources
TEMP_PATH=temp
QR_SALT=lib_unique_salt_2026
```

### Изменение пароля PostgreSQL

Для production рекомендуется изменить пароль:

```env
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:your_secure_password_here@postgres:5432/library_db
```

## Команды Docker Compose

### Управление контейнерами

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Остановка с удалением volumes (ОСТОРОЖНО: удалит данные!)
docker-compose down -v

# Перезапуск
docker-compose restart

# Просмотр логов
docker-compose logs -f [service_name]

# Статус сервисов
docker-compose ps

# Пересборка образов
docker-compose build --no-cache
```

### Работа с приложением

```bash
# Запуск тестов
docker-compose run --rm app pytest -v

# Интерактивная оболочка Python
docker-compose run --rm app python

# Bash в контейнере приложения
docker-compose exec app bash

# Запуск конкретного Python скрипта
docker-compose run --rm app python your_script.py
```

### Работа с PostgreSQL

```bash
# Подключение к PostgreSQL через psql
docker-compose exec postgres psql -U postgres -d library_db

# Список таблиц
docker-compose exec postgres psql -U postgres -d library_db -c "\dt"

# Выполнение SQL запроса
docker-compose exec postgres psql -U postgres -d library_db -c "SELECT COUNT(*) FROM books;"

# Бэкап базы данных
docker-compose exec postgres pg_dump -U postgres library_db > backup_$(date +%Y%m%d).sql

# Восстановление из бэкапа
docker-compose exec -T postgres psql -U postgres library_db < backup.sql

# Просмотр активных подключений
docker-compose exec postgres psql -U postgres -d library_db -c "SELECT * FROM pg_stat_activity;"
```

## Volumes (Персистентные данные)

Docker Compose создает следующие volumes:

- `postgres_data` — данные PostgreSQL (таблицы, индексы)
- `library_resources` — QR-коды, обложки книг
- `library_temp` — временные файлы
- `library_logs` — логи приложения
- `pgadmin_data` — настройки PgAdmin

### Управление volumes

```bash
# Список volumes
docker volume ls | grep library

# Просмотр информации о volume
docker volume inspect library_app_postgres_data

# Бэкап volume с данными PostgreSQL
docker run --rm \
  -v library_app_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz -C /data .

# Восстановление volume
docker run --rm \
  -v library_app_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## Инициализация базы данных

При первом запуске PostgreSQL автоматически выполняет `init.sql`:

```sql
-- Создание таблиц
CREATE TABLE books (...);
CREATE TABLE book_items (...);
CREATE TABLE readers (...);
CREATE TABLE loan_records (...);

-- Создание индексов
CREATE INDEX idx_books_isbn ON books(isbn);
-- и т.д.
```

Если нужно пересоздать БД:

```bash
# Остановить и удалить volume
docker-compose down -v

# Запустить заново (выполнится init.sql)
docker-compose up -d
```

## Сценарии использования

### Сценарий 1: Разработка и тестирование

```bash
# Запуск PostgreSQL в фоне
docker-compose up -d postgres

# Код редактируется локально
# Тесты запускаются в контейнере
docker-compose run --rm app pytest -v

# Изменения в коде видны сразу (volume mount)
```

### Сценарий 2: CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run tests in Docker
        run: |
          docker-compose up --build --abort-on-container-exit app
          docker-compose down -v
```

### Сценарий 3: Production-like окружение

```bash
# Полное развертывание
docker-compose up -d

# Проверка работоспособности
docker-compose exec postgres psql -U postgres -d library_db -c "SELECT version();"

# Мониторинг логов
docker-compose logs -f
```

## Архитектура Docker

```
┌─────────────────────────────────────────┐
│         Docker Host                     │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  app container                    │ │
│  │  - Python 3.11                    │ │
│  │  - PyQt5                          │ │
│  │  - Application code               │ │
│  │  - Tests                          │ │
│  │  - psycopg2 (PostgreSQL driver)  │ │
│  └───────────────┬───────────────────┘ │
│                  │                      │
│                  │ library_network      │
│                  ↓                      │
│  ┌───────────────────────────────────┐ │
│  │  postgres container               │ │
│  │  - PostgreSQL 15                  │ │
│  │  - Database: library_db           │ │
│  │  - Auto-initialized from init.sql │ │
│  └───────────────────────────────────┘ │
│                  ↑                      │
│                  │ (optional)           │
│  ┌───────────────────────────────────┐ │
│  │  pgadmin container                │ │
│  │  - Web UI: localhost:5050         │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Проблема: PostgreSQL не запускается

```bash
# Проверить логи
docker-compose logs postgres

# Проверить healthcheck
docker-compose exec postgres pg_isready -U postgres

# Пересоздать контейнер
docker-compose down
docker-compose up -d postgres
```

### Проблема: Приложение не может подключиться к БД

```bash
# Проверить DATABASE_URL
docker-compose run --rm app env | grep DATABASE_URL

# Проверить, что PostgreSQL доступен
docker-compose exec app ping postgres

# Проверить подключение вручную
docker-compose run --rm app python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:root@postgres:5432/library_db')
print('Connection OK')
"
```

### Проблема: Тесты падают

```bash
# Запустить с подробным выводом
docker-compose run --rm app pytest -vv --tb=short

# Проверить, что БД инициализирована
docker-compose exec postgres psql -U postgres -d library_db -c "\dt"

# Пересоздать БД
docker-compose down -v
docker-compose up -d
```

### Проблема: Нет места на диске

```bash
# Очистить неиспользуемые образы
docker image prune -a

# Очистить volumes (ОСТОРОЖНО!)
docker volume prune

# Полная очистка Docker
docker system prune -a --volumes
```

## Производительность

### Оптимизация PostgreSQL

Для production можно настроить PostgreSQL через переменные окружения:

```yaml
postgres:
  environment:
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    POSTGRES_MAX_CONNECTIONS: 100
```

### Мониторинг производительности

```bash
# Использование ресурсов
docker stats

# Размер базы данных
docker-compose exec postgres psql -U postgres -d library_db -c "
SELECT pg_size_pretty(pg_database_size('library_db'));
"

# Медленные запросы
docker-compose exec postgres psql -U postgres -d library_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

## Безопасность

### Рекомендации для production

1. **Измените пароли**
   ```bash
   # Генерация случайного пароля
   openssl rand -base64 32
   ```

2. **Не публикуйте порты PostgreSQL**
   ```yaml
   # Закомментируйте в docker-compose.yml
   # ports:
   #   - "5432:5432"
   ```

3. **Используйте Docker secrets**
   ```yaml
   secrets:
     postgres_password:
       file: ./secrets/postgres_password.txt
   ```

4. **Регулярные бэкапы**
   ```bash
   # Автоматический бэкап (cron)
   0 2 * * * cd /path/to/app && docker-compose exec postgres pg_dump -U postgres library_db > backup_$(date +\%Y\%m\%d).sql
   ```

## Миграции базы данных

Для изменения схемы БД:

1. Создайте SQL-скрипт миграции
2. Выполните его:
   ```bash
   docker-compose exec -T postgres psql -U postgres library_db < migration.sql
   ```

Или используйте инструменты миграций (Alembic, Flyway).

## Заключение

Docker-конфигурация обеспечивает:
- Изолированное окружение с PostgreSQL
- Воспроизводимые тесты
- Простое развертывание
- Готовность к CI/CD
- Production-ready архитектуру

Для локальной разработки без Docker используйте локальный PostgreSQL и `.env` файл.

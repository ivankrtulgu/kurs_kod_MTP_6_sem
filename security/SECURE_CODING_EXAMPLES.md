# Secure Coding Examples for Library Management System

Примеры безопасного кода для системы управления библиотекой.

## Безопасная работа с базой данных

### BookRepository - параметризованные запросы

```python
class BookRepository:
    """Репозиторий для работы с книгами"""
    
    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Безопасный поиск книги по ISBN"""
        query = """
            SELECT id, title, author, isbn, publisher, year, pages
            FROM books
            WHERE isbn = %s
        """
        # ✅ Параметризованный запрос защищает от SQL-injection
        self.cursor.execute(query, (isbn,))
        row = self.cursor.fetchone()
        return self._map_to_book(row) if row else None
    
    def search_books(self, search_term: str) -> List[Book]:
        """Безопасный поиск книг"""
        query = """
            SELECT id, title, author, isbn, publisher, year, pages
            FROM books
            WHERE title ILIKE %s OR author ILIKE %s
            ORDER BY title
        """
        # ✅ Параметризация для LIKE-запросов
        pattern = f"%{search_term}%"
        self.cursor.execute(query, (pattern, pattern))
        return [self._map_to_book(row) for row in self.cursor.fetchall()]
```

## Безопасная работа с QR-кодами

### QRCodeService - валидация данных

```python
class QRCodeService:
    """Сервис для работы с QR-кодами"""
    
    def __init__(self, salt: str):
        # ✅ Соль из переменных окружения, не хардкод
        self.salt = salt
    
    def generate_qr_code(self, book_item_id: int) -> str:
        """Генерация QR-кода с проверкой входных данных"""
        # ✅ Валидация входных данных
        if not isinstance(book_item_id, int) or book_item_id <= 0:
            raise ValueError("Invalid book_item_id")
        
        # ✅ Использование криптографически безопасного хеширования
        data = f"{book_item_id}:{self.salt}"
        hash_value = hashlib.sha256(data.encode()).hexdigest()
        
        qr_data = f"LIBRARY:{book_item_id}:{hash_value[:16]}"
        
        # ✅ Безопасное создание пути к файлу
        filename = self._get_safe_filename(book_item_id)
        filepath = self.qr_dir / filename
        
        # Генерация QR-кода
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(str(filepath))
        
        return str(filepath)
    
    def _get_safe_filename(self, book_item_id: int) -> str:
        """Безопасное имя файла"""
        # ✅ Только цифры, никаких специальных символов
        return f"qr_{book_item_id}.png"
    
    def verify_qr_code(self, qr_data: str) -> Optional[int]:
        """Проверка QR-кода"""
        # ✅ Валидация формата
        if not qr_data.startswith("LIBRARY:"):
            return None
        
        try:
            parts = qr_data.split(":")
            if len(parts) != 3:
                return None
            
            book_item_id = int(parts[1])
            provided_hash = parts[2]
            
            # ✅ Проверка хеша
            expected_data = f"{book_item_id}:{self.salt}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()[:16]
            
            # ✅ Защита от timing attacks
            if not secrets.compare_digest(provided_hash, expected_hash):
                return None
            
            return book_item_id
            
        except (ValueError, IndexError):
            return None
```

## Безопасная работа с файлами

### FileService - защита от path traversal

```python
class FileService:
    """Сервис для работы с файлами"""
    
    def __init__(self, base_dir: Path):
        # ✅ Базовая директория из конфигурации
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_cover_image(self, book_id: int, image_data: bytes) -> str:
        """Безопасное сохранение обложки книги"""
        # ✅ Валидация входных данных
        if not isinstance(book_id, int) or book_id <= 0:
            raise ValueError("Invalid book_id")
        
        if not image_data or len(image_data) > 5 * 1024 * 1024:  # 5 MB
            raise ValueError("Invalid image data or size")
        
        # ✅ Безопасное имя файла (только цифры)
        filename = f"cover_{book_id}.jpg"
        filepath = self.base_dir / filename
        
        # ✅ Проверка, что путь внутри базовой директории
        if not str(filepath.resolve()).startswith(str(self.base_dir)):
            raise ValueError("Invalid file path")
        
        # ✅ Проверка типа файла по magic bytes
        if not self._is_valid_image(image_data):
            raise ValueError("Invalid image format")
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return str(filepath)
    
    def _is_valid_image(self, data: bytes) -> bool:
        """Проверка, что данные - это изображение"""
        # ✅ Проверка magic bytes для JPEG и PNG
        jpeg_magic = b'\xff\xd8\xff'
        png_magic = b'\x89PNG\r\n\x1a\n'
        
        return data.startswith(jpeg_magic) or data.startswith(png_magic)
    
    def read_file(self, filename: str) -> bytes:
        """Безопасное чтение файла"""
        # ✅ Санитизация имени файла
        safe_filename = Path(filename).name  # Только имя, без пути
        filepath = self.base_dir / safe_filename
        
        # ✅ Проверка, что путь внутри базовой директории
        if not str(filepath.resolve()).startswith(str(self.base_dir)):
            raise ValueError("Invalid file path")
        
        # ✅ Проверка существования
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {safe_filename}")
        
        with open(filepath, 'rb') as f:
            return f.read()
```

## Безопасное логирование

### Logger - без чувствительных данных

```python
import logging
from typing import Any, Dict

class SecureLogger:
    """Безопасное логирование без чувствительных данных"""
    
    SENSITIVE_KEYS = {'password', 'token', 'secret', 'api_key', 'salt'}
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_operation(self, operation: str, data: Dict[str, Any]):
        """Логирование операции с фильтрацией чувствительных данных"""
        # ✅ Удаление чувствительных данных перед логированием
        safe_data = self._sanitize_data(data)
        self.logger.info(f"Operation: {operation}, Data: {safe_data}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Удаление чувствительных данных"""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_KEYS:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        return sanitized
    
    def log_error(self, error: Exception, context: str = ""):
        """Безопасное логирование ошибок"""
        # ✅ Логируем тип ошибки, но не детали, которые могут содержать секреты
        self.logger.error(
            f"Error in {context}: {type(error).__name__}",
            exc_info=False  # Не логируем полный traceback в production
        )

# Использование
logger = SecureLogger(__name__)

# ✅ Безопасно
logger.log_operation("create_user", {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secret123"  # Будет заменено на ***REDACTED***
})
```

## Безопасная конфигурация

### Settings - секреты из окружения

```python
import os
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    """Безопасная конфигурация приложения"""
    
    def __init__(self):
        # ✅ Загрузка из .env файла
        load_dotenv()
        
        # ✅ Секреты только из переменных окружения
        self.database_url = self._get_required_env("DATABASE_URL")
        self.qr_salt = self._get_required_env("QR_SALT")
        
        # ✅ Опциональные настройки с безопасными значениями по умолчанию
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # ✅ Пути из конфигурации
        self.resources_path = Path(os.getenv("RESOURCES_PATH", "resources"))
        self.temp_path = Path(os.getenv("TEMP_PATH", "temp"))
        
        # ✅ Валидация критических настроек
        self._validate()
    
    def _get_required_env(self, key: str) -> str:
        """Получение обязательной переменной окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _validate(self):
        """Валидация конфигурации"""
        # ✅ Проверка формата DATABASE_URL
        if not self.database_url.startswith("postgresql://"):
            raise ValueError("Invalid DATABASE_URL format")
        
        # ✅ Проверка длины соли
        if len(self.qr_salt) < 16:
            raise ValueError("QR_SALT must be at least 16 characters")
        
        # ✅ DEBUG должен быть отключен в production
        if self.debug and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("DEBUG must be False in production")

# Использование
settings = Settings()
```

## Безопасная обработка ошибок

### Error Handling - без раскрытия деталей

```python
from PyQt5.QtWidgets import QMessageBox

class ErrorHandler:
    """Безопасная обработка ошибок в UI"""
    
    def __init__(self, logger: SecureLogger):
        self.logger = logger
    
    def handle_error(self, error: Exception, parent=None):
        """Обработка ошибки с безопасным сообщением пользователю"""
        # ✅ Логируем детали для разработчиков
        self.logger.log_error(error, context="UI operation")
        
        # ✅ Показываем общее сообщение пользователю
        user_message = self._get_user_friendly_message(error)
        
        QMessageBox.critical(
            parent,
            "Ошибка",
            user_message
        )
    
    def _get_user_friendly_message(self, error: Exception) -> str:
        """Безопасное сообщение для пользователя"""
        # ✅ Не раскрываем внутренние детали
        error_messages = {
            ValueError: "Введены некорректные данные",
            FileNotFoundError: "Файл не найден",
            PermissionError: "Недостаточно прав доступа",
            ConnectionError: "Ошибка подключения к базе данных"
        }
        
        return error_messages.get(
            type(error),
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )
```

## Рекомендации

1. **Всегда валидируйте входные данные**
2. **Используйте параметризованные SQL-запросы**
3. **Не храните секреты в коде**
4. **Проверяйте пути к файлам**
5. **Фильтруйте чувствительные данные в логах**
6. **Показывайте пользователям общие сообщения об ошибках**
7. **Используйте криптографически безопасные функции**
8. **Проверяйте типы и форматы данных**
9. **Ограничивайте размеры загружаемых файлов**
10. **Регулярно обновляйте зависимости**

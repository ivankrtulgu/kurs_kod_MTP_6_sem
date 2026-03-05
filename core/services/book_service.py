"""
Book service module.

Provides business logic layer for book operations with validation
and file path management.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.models.book import Book
from infrastructure.database.book_repository import SQLiteBookRepository
from infrastructure.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class BookServiceError(Exception):
    """Base exception for book service errors."""
    pass


class ValidationError(BookServiceError):
    """Raised when book data validation fails."""
    pass


class FileOperationError(BookServiceError):
    """Raised when file operations fail."""
    pass


class BookService:
    """
    Service layer for book operations.

    Wraps BookRepository with validation and file path management.
    Handles cover images and QR code storage.

    Example:
        >>> service = BookService()
        >>> book = Book(author="Иванов И.И.", title="Test", ...)
        >>> book_id = service.add_book(book)
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize book service.

        Args:
            db_path: Optional custom database path. Uses settings default if None.
        """
        settings.ensure_dirs()
        database_path = db_path or settings.DATABASE_PATH
        db_manager = DatabaseManager(database_path)
        self._repository = SQLiteBookRepository(db_manager)
        logger.info(f"BookService initialized with database: {database_path}")

    def _validate_book(self, book: Book) -> None:
        """
        Validate book data before saving.

        Args:
            book: Book object to validate.

        Raises:
            ValidationError: If any required field is invalid.
        """
        errors: list[str] = []

        # Validate author
        if not book.author or not book.author.strip():
            errors.append("Author is required")

        # Validate title
        if not book.title or not book.title.strip():
            errors.append("Title is required")

        # Validate year (1900-2100)
        if not (1900 <= book.year <= 2100):
            errors.append(f"Year must be between 1900 and 2100, got {book.year}")

        # Validate pages (> 0)
        if book.pages <= 0:
            errors.append(f"Pages must be greater than 0, got {book.pages}")

        # Validate ISBN (non-empty)
        if not book.isbn or not book.isbn.strip():
            errors.append("ISBN is required")

        # Validate place (non-empty)
        if not book.place or not book.place.strip():
            errors.append("Place of publication is required")

        # Validate publisher (non-empty)
        if not book.publisher or not book.publisher.strip():
            errors.append("Publisher is required")

        if errors:
            error_msg = "; ".join(errors)
            logger.warning(f"Book validation failed: {error_msg}")
            raise ValidationError(f"Validation failed: {error_msg}")

        logger.debug(f"Book validation passed for: {book.title}")

    def _copy_file_to_resources(
        self, source_path: str, resource_type: str
    ) -> str:
        """
        Copy file to resources directory.

        Args:
            source_path: Source file path.
            resource_type: Type of resource ('cover' or 'qr').

        Returns:
            str: New path in resources directory.

        Raises:
            FileOperationError: If file operation fails.
        """
        if not source_path:
            return ""

        source = Path(source_path)
        if not source.exists():
            logger.warning(f"Source file not found: {source_path}")
            return ""

        # Create resource subdirectory
        resource_dir = settings.RESOURCES_PATH / resource_type
        resource_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        dest_path = resource_dir / source.name

        try:
            shutil.copy2(source, dest_path)
            logger.info(f"Copied {resource_type} to: {dest_path}")
            return str(dest_path)
        except Exception as e:
            logger.error(f"Failed to copy {resource_type}: {e}")
            raise FileOperationError(f"Failed to copy {resource_type}: {e}")

    def add_book(self, book: Book) -> int:
        """
        Add a new book to the repository.

        Validates book data and handles file paths for cover images
        and QR codes before saving to database.

        Args:
            book: Book object to add.

        Returns:
            int: ID of the newly added book.

        Raises:
            ValidationError: If book data is invalid.
            FileOperationError: If file operations fail.
        """
        logger.info(f"Adding book: {book.title} by {book.author}")

        # Validate book data
        self._validate_book(book)

        # Handle cover image
        if book.cover_image_path:
            book.cover_image_path = self._copy_file_to_resources(
                book.cover_image_path, "covers"
            )

        # Handle QR code
        if book.qr_code_path:
            book.qr_code_path = self._copy_file_to_resources(
                book.qr_code_path, "qr_codes"
            )

        # Add to repository
        book_id = self._repository.add(book)
        logger.info(f"Book added with ID: {book_id}")
        return book_id

    def update_book(self, book: Book) -> bool:
        """
        Update an existing book.

        Validates book data and handles file paths before updating.

        Args:
            book: Book object with updated data.

        Returns:
            bool: True if update was successful, False otherwise.

        Raises:
            ValidationError: If book data is invalid.
            FileOperationError: If file operations fail.
        """
        logger.info(f"Updating book ID: {book.id}")

        # Validate book data
        self._validate_book(book)

        # Handle cover image
        if book.cover_image_path:
            book.cover_image_path = self._copy_file_to_resources(
                book.cover_image_path, "covers"
            )

        # Handle QR code
        if book.qr_code_path:
            book.qr_code_path = self._copy_file_to_resources(
                book.qr_code_path, "qr_codes"
            )

        # Update in repository
        success = self._repository.update(book)
        if success:
            logger.info(f"Book updated: ID {book.id}")
        else:
            logger.warning(f"Book not found for update: ID {book.id}")
        return success

    def delete_book(self, book_id: int) -> bool:
        """
        Delete a book by ID.

        Args:
            book_id: ID of book to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        logger.info(f"Deleting book ID: {book_id}")
        success = self._repository.delete(book_id)
        if success:
            logger.info(f"Book deleted: ID {book_id}")
        else:
            logger.warning(f"Book not found for delete: ID {book_id}")
        return success

    def get_book(self, book_id: int) -> Optional[Book]:
        """
        Get a book by ID.

        Args:
            book_id: Book ID.

        Returns:
            Book | None: Book object if found, None otherwise.
        """
        logger.debug(f"Getting book ID: {book_id}")
        return self._repository.get_by_id(book_id)

    def get_all_books(self) -> list[Book]:
        """
        Get all books from the repository.

        Returns:
            list[Book]: List of all books.
        """
        logger.debug("Getting all books")
        return self._repository.get_all()

    def search_books(self, query: str) -> list[Book]:
        """
        Search books by author, title, or ISBN.

        Args:
            query: Search query string.

        Returns:
            list[Book]: List of matching books.
        """
        logger.debug(f"Searching books with query: {query}")
        return self._repository.search(query)

    def count_books(self) -> int:
        """
        Get total number of books.

        Returns:
            int: Number of books in repository.
        """
        return self._repository.count()

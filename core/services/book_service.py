"""
Book service module.

Provides business logic layer for book operations with validation
and file path management.
"""

import logging
import re
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


class ISBNValidator:
    """
    ISBN-10 and ISBN-13 validation with check digit verification.
    
    Supports:
    - ISBN-10: 10 digits with check digit (0-10, where 10 = X)
    - ISBN-13: 13 digits starting with 978 or 979
    
    Examples:
        >>> ISBNValidator.validate("978-5-02-040500-0")
        (True, None)
        >>> ISBNValidator.validate("2-266-11156-6")
        (True, None)
        >>> ISBNValidator.validate("invalid-isbn")
        (False, "Invalid ISBN format")
    """
    
    @staticmethod
    def validate(isbn: str) -> tuple[bool, Optional[str]]:
        """
        Validate ISBN format and check digit.
        
        Args:
            isbn: ISBN string (with or without hyphens).
            
        Returns:
            tuple[bool, str | None]: (is_valid, error_message)
        """
        if not isbn:
            return False, "ISBN is required"
        
        # Remove hyphens and spaces
        clean_isbn = re.sub(r'[-\s]', '', isbn)
        
        # Determine ISBN type
        if len(clean_isbn) == 10:
            return ISBNValidator._validate_isbn10(clean_isbn.upper())  # Normalize X to uppercase
        elif len(clean_isbn) == 13:
            return ISBNValidator._validate_isbn13(clean_isbn)
        else:
            return False, f"ISBN must be 10 or 13 digits, got {len(clean_isbn)}"
    
    @staticmethod
    def _validate_isbn10(isbn: str) -> tuple[bool, Optional[str]]:
        """
        Validate ISBN-10 format and check digit.
        
        Check digit calculation:
        - Multiply each digit by weights 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
        - Sum must be divisible by 11
        - Check digit can be 0-9 or X (for 10)
        
        Args:
            isbn: 10-character ISBN string.
            
        Returns:
            tuple[bool, str | None]: (is_valid, error_message)
        """
        # Check format: 9 digits + (digit or X)
        pattern = r'^[0-9]{9}[0-9X]$'
        if not re.match(pattern, isbn, re.IGNORECASE):
            return False, "ISBN-10 must be 9 digits followed by digit or X"
        
        # Convert to list of values (X = 10)
        digits = []
        for i, char in enumerate(isbn):
            if char.upper() == 'X':
                digits.append(10)
            else:
                digits.append(int(char))
        
        # Calculate weighted sum
        weights = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        total = sum(d * w for d, w in zip(digits, weights))
        
        # Check if divisible by 11
        if total % 11 != 0:
            expected_check = (11 - (sum(d * w for d, w in zip(digits[:9], weights[:9])) % 11)) % 11
            return False, f"Invalid ISBN-10 check digit. Expected {expected_check}, got {digits[9]}"
        
        return True, None
    
    @staticmethod
    def _validate_isbn13(isbn: str) -> tuple[bool, Optional[str]]:
        """
        Validate ISBN-13 format and check digit.
        
        Check digit calculation:
        - Multiply digits alternately by 1 and 3
        - Sum must be divisible by 10
        - Must start with 978 or 979
        
        Args:
            isbn: 13-character ISBN string.
            
        Returns:
            tuple[bool, str | None]: (is_valid, error_message)
        """
        # Check format: 13 digits
        if not isbn.isdigit():
            return False, "ISBN-13 must contain only digits"
        
        # Check prefix
        if not isbn.startswith(('978', '979')):
            return False, "ISBN-13 must start with 978 or 979"
        
        # Convert to list of integers
        digits = [int(d) for d in isbn]
        
        # Calculate weighted sum (alternate 1, 3)
        weights = [1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1]
        total = sum(d * w for d, w in zip(digits, weights))
        
        # Check if divisible by 10
        if total % 10 != 0:
            # Calculate expected check digit
            sum_without_check = sum(d * w for d, w in zip(digits[:12], weights[:12]))
            expected_check = (10 - (sum_without_check % 10)) % 10
            return False, f"Invalid ISBN-13 check digit. Expected {expected_check}, got {digits[12]}"
        
        return True, None


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

    def __init__(self, db_manager: Optional[DatabaseManager] = None, db_path: Optional[Path] = None) -> None:
        """
        Initialize book service.

        Args:
            db_manager: Optional pre-initialized DatabaseManager.
            db_path: Optional custom database path. Uses settings default if both are None.
        """
        settings.ensure_dirs()
        
        if db_manager:
            manager = db_manager
        else:
            database_path = db_path or settings.DATABASE_PATH
            manager = DatabaseManager(database_path)
            
        self._repository = SQLiteBookRepository(manager)
        logger.info(f"BookService initialized.")

    def _validate_book(self, book: Book) -> None:
        """
        Validate book data before saving.

        Validates according to GOST R 7.0.4-2020:
        - Required fields: author, title, place, publisher, year, pages, isbn
        - Year must be between 1900 and 2100
        - Pages must be greater than 0
        - ISBN must be valid (ISBN-10 or ISBN-13)

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

        # Validate year (1900-2100) - also validated in Model.__post_init__()
        if not isinstance(book.year, int) or not (1900 <= book.year <= 2100):
            errors.append(f"Year must be between 1900 and 2100, got {book.year}")

        # Validate pages (> 0) - also validated in Model.__post_init__()
        if not isinstance(book.pages, int) or book.pages <= 0:
            errors.append(f"Pages must be greater than 0, got {book.pages}")

        # Validate ISBN (format and check digit) - also validated in Model.__post_init__()
        if not book.isbn or not book.isbn.strip():
            errors.append("ISBN is required")
        else:
            is_valid, error = ISBNValidator.validate(book.isbn)
            if not is_valid:
                errors.append(f"Invalid ISBN: {error}")

        # Validate place
        if not book.place or not book.place.strip():
            errors.append("Place of publication is required")

        # Validate publisher
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

        # Check if source and destination are the same file
        if source.resolve() == dest_path.resolve():
            logger.info(f"File already exists in target location, skipping copy: {dest_path}")
            return str(dest_path) # Return the existing path

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

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """
        Helper method to get a book by ID.
        
        Args:
            book_id: Book ID.
            
        Returns:
            Book | None: Book object if found, None otherwise.
        """
        return self.get_book(book_id)

    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """
        Get a book by its ISBN.
        
        Args:
            isbn: ISBN string.
            
        Returns:
            Book | None: Book object if found, None otherwise.
        """
        return self._repository.get_by_isbn(isbn)


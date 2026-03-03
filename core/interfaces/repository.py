"""Repository interface module."""

from abc import ABC, abstractmethod
from typing import Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models.book import Book


class BookRepository(ABC):
    """
    Abstract repository for book operations.
    
    Defines the contract for book data access layer.
    Implementation should be database-agnostic.
    """

    @abstractmethod
    def add(self, book: Book) -> int:
        """
        Add a new book to the repository.
        
        Args:
            book: Book object to add.
            
        Returns:
            int: ID of the newly added book.
        """
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Book]:
        """
        Get a book by its ID.
        
        Args:
            id: Book ID.
            
        Returns:
            Book | None: Book object if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Book]:
        """
        Get all books from the repository.
        
        Returns:
            list[Book]: List of all books.
        """
        pass

    @abstractmethod
    def search(self, query: str) -> list[Book]:
        """
        Search books by author, title, or ISBN.
        
        Args:
            query: Search query string.
            
        Returns:
            list[Book]: List of matching books.
        """
        pass

    @abstractmethod
    def update(self, book: Book) -> bool:
        """
        Update an existing book.
        
        Args:
            book: Book object with updated data.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete a book by ID.
        
        Args:
            id: Book ID to delete.
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get total number of books in the repository.
        
        Returns:
            int: Number of books.
        """
        pass

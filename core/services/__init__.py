"""
Services module for business logic layer.

Provides service classes that wrap repository operations
with validation and additional business logic.
"""

from core.services.book_service import BookService

__all__ = ["BookService"]

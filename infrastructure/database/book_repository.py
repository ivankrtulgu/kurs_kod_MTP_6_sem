"""SQLite book repository implementation."""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.repository import BookRepository
from core.models.book import Book
from infrastructure.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class SQLiteBookRepository(BookRepository):
    """
    SQLite implementation of BookRepository.
    
    Uses prepared statements for SQL injection protection.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """
        Initialize repository.
        
        Args:
            db_manager: Database connection manager.
        """
        self._db = db_manager

    def _row_to_book(self, row: sqlite3.Row) -> Book:
        """Convert database row to Book object."""
        return Book(
            id=row["id"],
            author=row["author"],
            title=row["title"],
            subtitle=row["subtitle"] or "",
            responsibility=row["responsibility"] or "",
            edition=row["edition"] or "",
            place=row["place"],
            publisher=row["publisher"],
            year=row["year"],
            pages=row["pages"],
            isbn=row["isbn"],
            copyright=row["copyright"] or "",
            udc=row["udc"] or "",
            bbk=row["bbk"] or "",
            author_mark=row["author_mark"] or "",
            reviewers=row["reviewers"] or "",
            annotation=row["annotation"] or "",
            abstract=row["abstract"] or "",
            doi=row["doi"] or "",
            content_type=row["content_type"] or "Текст",
            access_method=row["access_method"] or "непосредственный",
            created_at=datetime.fromisoformat(row["created_at"]),
            qr_code_path=row["qr_code_path"] or "",
            cover_image_path=row["cover_image_path"] or "",
        )

    def add(self, book: Book) -> int:
        """Add a new book to the database."""
        query = """
            INSERT INTO books (
                author, title, subtitle, responsibility, edition,
                place, publisher, year, pages, isbn, copyright,
                udc, bbk, author_mark, reviewers, annotation,
                abstract, doi, content_type, access_method,
                qr_code_path, cover_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    book.author,
                    book.title,
                    book.subtitle,
                    book.responsibility,
                    book.edition,
                    book.place,
                    book.publisher,
                    book.year,
                    book.pages,
                    book.isbn,
                    book.copyright,
                    book.udc,
                    book.bbk,
                    book.author_mark,
                    book.reviewers,
                    book.annotation,
                    book.abstract,
                    book.doi,
                    book.content_type,
                    book.access_method,
                    book.qr_code_path,
                    book.cover_image_path,
                ),
            )
            conn.commit()
            book_id = cursor.lastrowid
            logger.info(f"Book added with ID: {book_id}")
            return book_id

    def get_by_id(self, id: int) -> Optional[Book]:
        """Get a book by ID."""
        query = "SELECT * FROM books WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_book(row)
            return None

    def get_all(self) -> list[Book]:
        """Get all books."""
        query = "SELECT * FROM books ORDER BY year DESC, title ASC"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._row_to_book(row) for row in rows]

    def search(self, query: str) -> list[Book]:
        """Search books by author, title, or ISBN."""
        search_pattern = f"%{query}%"
        sql = """
            SELECT * FROM books
            WHERE author LIKE ? OR title LIKE ? OR isbn LIKE ?
            ORDER BY year DESC, title ASC
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            return [self._row_to_book(row) for row in rows]

    def update(self, book: Book) -> bool:
        """Update an existing book."""
        query = """
            UPDATE books SET
                author = ?, title = ?, subtitle = ?, responsibility = ?,
                edition = ?, place = ?, publisher = ?, year = ?, pages = ?,
                isbn = ?, copyright = ?, udc = ?, bbk = ?, author_mark = ?,
                reviewers = ?, annotation = ?, abstract = ?, doi = ?,
                content_type = ?, access_method = ?,
                qr_code_path = ?, cover_image_path = ?
            WHERE id = ?
        """
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    book.author,
                    book.title,
                    book.subtitle,
                    book.responsibility,
                    book.edition,
                    book.place,
                    book.publisher,
                    book.year,
                    book.pages,
                    book.isbn,
                    book.copyright,
                    book.udc,
                    book.bbk,
                    book.author_mark,
                    book.reviewers,
                    book.annotation,
                    book.abstract,
                    book.doi,
                    book.content_type,
                    book.access_method,
                    book.qr_code_path,
                    book.cover_image_path,
                    book.id,
                ),
            )
            conn.commit()
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Book updated: ID {book.id}")
            else:
                logger.warning(f"Book not found for update: ID {book.id}")
            return updated

    def delete(self, id: int) -> bool:
        """Delete a book by ID."""
        query = "DELETE FROM books WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Book deleted: ID {id}")
            else:
                logger.warning(f"Book not found for delete: ID {id}")
            return deleted

    def count(self) -> int:
        """Get total number of books."""
        query = "SELECT COUNT(*) FROM books"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchone()[0]

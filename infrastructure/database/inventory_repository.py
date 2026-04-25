"""SQLite inventory repository implementation."""

import logging
from datetime import datetime
from typing import Optional, List


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models.inventory import BookItem, Reader, LoanRecord, ItemStatus
from infrastructure.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


class SQLiteInventoryRepository:
    """
    SQLite implementation for managing physical inventory, readers, and loans.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager
        self._init_db()

    def _init_db(self) -> None:
        """Initialize inventory tables."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS readers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS book_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_number TEXT UNIQUE NOT NULL,
                book_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                location TEXT,
                qr_code_path TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS loan_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                reader_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                condition_on_issue TEXT,
                condition_on_return TEXT,
                FOREIGN KEY (item_id) REFERENCES book_items (id),
                FOREIGN KEY (reader_id) REFERENCES readers (id)
            )
            """,
        ]
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            
            # Migration: Add qr_code_path if it doesn't exist
            try:
                cursor.execute("ALTER TABLE book_items ADD COLUMN qr_code_path TEXT")
            except Exception:
                pass # Column already exists
                
            conn.commit()

    # --- BookItem Methods ---

    def add_item(self, item: BookItem) -> int:
        query = """
            INSERT INTO book_items (inventory_number, book_id, status, location)
            VALUES (?, ?, ?, ?)
        """
        params = (item.inventory_number, item.book_id, item.status.value, item.location)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_item_by_id(self, item_id: int) -> Optional[BookItem]:
        query = "SELECT * FROM book_items WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (item_id,))
            row = cursor.fetchone()
            if row:
                return BookItem(
                    id=row["id"],
                    inventory_number=row["inventory_number"],
                    book_id=row["book_id"],
                    status=ItemStatus(row["status"]),
                    location=row["location"] or "",
                    qr_code_path=row["qr_code_path"]
                )
            return None

    def get_item_by_inventory_number(self, inv_num: str) -> Optional[BookItem]:
        """Find a book item by its unique inventory number."""
        query = "SELECT * FROM book_items WHERE inventory_number = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (inv_num,))
            row = cursor.fetchone()
            if row:
                return BookItem(
                    id=row["id"],
                    inventory_number=row["inventory_number"],
                    book_id=row["book_id"],
                    status=ItemStatus(row["status"]),
                    location=row["location"] or "",
                    qr_code_path=row["qr_code_path"]
                )
            return None

    def get_items_by_book(self, book_id: int) -> List[BookItem]:
        query = "SELECT * FROM book_items WHERE book_id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (book_id,))
            rows = cursor.fetchall()
            return [
                BookItem(
                    id=row["id"],
                    inventory_number=row["inventory_number"],
                    book_id=row["book_id"],
                    status=ItemStatus(row["status"]),
                    location=row["location"] or "",
                    qr_code_path=row["qr_code_path"]
                ) for row in rows
            ]

    def get_all_items(self) -> List[BookItem]:
        """Fetch all physical book items from the database."""
        query = "SELECT * FROM book_items"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                BookItem(
                    id=row["id"],
                    inventory_number=row["inventory_number"],
                    book_id=row["book_id"],
                    status=ItemStatus(row["status"]),
                    location=row["location"] or ""
                ) for row in rows
            ]

    def update_item_qr_path(self, item_id: int, qr_path: str) -> bool:
        """Update the QR code file path for a book item."""
        query = "UPDATE book_items SET qr_code_path = ? WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (qr_path, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_item_location(self, item_id: int, location: str) -> bool:
        """Update the shelf location for a book item."""
        query = "UPDATE book_items SET location = ? WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (location, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_item_status(self, item_id: int, status: ItemStatus) -> bool:
        query = "UPDATE book_items SET status = ? WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status.value, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_max_inventory_number(self) -> int:
        """Find the maximum existing inventory number for sequential numbering."""
        query = "SELECT MAX(CAST(inventory_number AS INTEGER)) FROM book_items"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    # --- Reader Methods ---
    
    def add_reader(self, reader: Reader) -> int:
        query = "INSERT INTO readers (full_name, phone, is_active) VALUES (?, ?, ?)"
        params = (reader.full_name, reader.phone, reader.is_active)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def update_reader(self, reader: Reader) -> bool:
        """Update existing reader information."""
        query = "UPDATE readers SET full_name = ?, phone = ?, is_active = ? WHERE id = ?"
        params = (reader.full_name, reader.phone, reader.is_active, reader.id)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_reader(self, reader_id: int) -> bool:
        """Delete a reader from the database."""
        query = "DELETE FROM readers WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reader_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_readers(self) -> List[Reader]:
        """Fetch all readers."""
        query = "SELECT * FROM readers"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                Reader(
                    id=row["id"],
                    full_name=row["full_name"],
                    phone=row["phone"],
                    is_active=bool(row["is_active"])
                ) for row in rows
            ]

    def get_reader_by_id(self, reader_id: int) -> Optional[Reader]:
        query = "SELECT * FROM readers WHERE id = ?"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reader_id,))
            row = cursor.fetchone()
            if row:
                return Reader(
                    id=row["id"],
                    full_name=row["full_name"],
                    phone=row["phone"],
                    is_active=bool(row["is_active"])
                )
            return None

    # --- LoanRecord Methods ---

    def create_loan(self, loan: LoanRecord) -> int:
        query = """
            INSERT INTO loan_records (
                item_id, reader_id, issue_date, due_date, 
                return_date, condition_on_issue, condition_on_return
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            loan.item_id, loan.reader_id, 
            loan.issue_date.isoformat(), loan.due_date.isoformat(),
            loan.return_date.isoformat() if loan.return_date else None,
            loan.condition_on_issue, loan.condition_on_return
        )
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def find_active_loan(self, item_id: int) -> Optional[LoanRecord]:
        """Find the current open loan for a specific item."""
        query = "SELECT * FROM loan_records WHERE item_id = ? AND return_date IS NULL"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (item_id,))
            row = cursor.fetchone()
            if row:
                return LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=datetime.fromisoformat(row["issue_date"]),
                    due_date=datetime.fromisoformat(row["due_date"]),
                    return_date=datetime.fromisoformat(row["return_date"]) if row["return_date"] else None,
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                )
            return None

    def close_loan(self, loan_id: int, return_date: datetime, condition: str) -> bool:
        """Update a loan record when a book is returned."""
        query = "UPDATE loan_records SET return_date = ?, condition_on_return = ? WHERE id = ?"
        params = (return_date.isoformat(), condition, loan_id)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def get_item_history(self, item_id: int) -> List[LoanRecord]:
        query = "SELECT * FROM loan_records WHERE item_id = ? ORDER BY issue_date ASC"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (item_id,))
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=datetime.fromisoformat(row["issue_date"]),
                    due_date=datetime.fromisoformat(row["due_date"]),
                    return_date=datetime.fromisoformat(row["return_date"]) if row["return_date"] else None,
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

    def get_loans_by_reader(self, reader_id: int, active_only: bool = True) -> List[LoanRecord]:
        if active_only:
            query = "SELECT * FROM loan_records WHERE reader_id = ? AND return_date IS NULL"
        else:
            query = "SELECT * FROM loan_records WHERE reader_id = ?"
            
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reader_id,))
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=datetime.fromisoformat(row["issue_date"]),
                    due_date=datetime.fromisoformat(row["due_date"]),
                    return_date=datetime.fromisoformat(row["return_date"]) if row["return_date"] else None,
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

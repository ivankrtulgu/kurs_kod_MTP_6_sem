"""Postgres inventory repository implementation."""

import logging
from datetime import datetime
from typing import Optional, List


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models.inventory import BookItem, Reader, LoanRecord, ItemStatus
from infrastructure.database.connection import PostgresDatabaseManager

logger = logging.getLogger(__name__)


class PostgresInventoryRepository:
    """
    Postgres implementation for managing physical inventory, readers, and loans.
    """

    def __init__(self, db_manager: PostgresDatabaseManager) -> None:
        self._db = db_manager

    # --- BookItem Methods ---

    def add_item(self, item: BookItem) -> int:
        query = """
            INSERT INTO book_items (inventory_number, book_id, status, location)
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        params = (item.inventory_number, item.book_id, item.status.value, item.location)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()["id"]

    def get_item_by_id(self, item_id: int) -> Optional[BookItem]:
        query = "SELECT * FROM book_items WHERE id = %s"
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
        query = "SELECT * FROM book_items WHERE inventory_number = %s"
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
        query = "SELECT * FROM book_items WHERE book_id = %s"
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
        query = "UPDATE book_items SET qr_code_path = %s WHERE id = %s"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (qr_path, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_item_location(self, item_id: int, location: str) -> bool:
        """Update the shelf location for a book item."""
        query = "UPDATE book_items SET location = %s WHERE id = %s"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (location, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def update_item_status(self, item_id: int, status: ItemStatus) -> bool:
        query = "UPDATE book_items SET status = %s WHERE id = %s"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status.value, item_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_max_inventory_number(self) -> int:
        """Find the maximum existing inventory number for sequential numbering."""
        query = "SELECT MAX(CAST(inventory_number AS INTEGER)) as max_inv FROM book_items"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            result = row["max_inv"] if row else None
            return result if result is not None else 0

    # --- Reader Methods ---
    
    def add_reader(self, reader: Reader) -> int:
        query = """
            INSERT INTO readers (
                last_name, first_name, middle_name, birth_date, 
                phone, email, home_address, registration_date, status, notes,
                passport_series, passport_number
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            reader.last_name, 
            reader.first_name, 
            reader.middle_name or None, 
            reader.birth_date if reader.birth_date not in (None, "") else None,
            reader.phone, 
            reader.email, 
            reader.home_address, 
            reader.registration_date if reader.registration_date not in (None, "") else None,
            reader.status, 
            reader.notes, 
            reader.passport_series, 
            reader.passport_number
        )
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchone()["id"]

    def update_reader(self, reader: Reader) -> bool:
        """Update existing reader information."""
        query = """
            UPDATE readers SET 
                last_name = %s, first_name = %s, middle_name = %s, birth_date = %s, 
                phone = %s, email = %s, home_address = %s, registration_date = %s, 
                status = %s, notes = %s, passport_series = %s, passport_number = %s
            WHERE id = %s
        """
        params = (
            reader.last_name, 
            reader.first_name, 
            reader.middle_name or None, 
            reader.birth_date if reader.birth_date not in (None, "") else None,
            reader.phone, 
            reader.email, 
            reader.home_address, 
            reader.registration_date if reader.registration_date not in (None, "") else None,
            reader.status, 
            reader.notes, 
            reader.passport_series, 
            reader.passport_number, 
            reader.id
        )
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_reader(self, reader_id: int) -> bool:
        """Delete a reader from the database."""
        query = "DELETE FROM readers WHERE id = %s"
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
                    last_name=row["last_name"],
                    first_name=row["first_name"],
                    middle_name=row["middle_name"] or "",
                    birth_date=row["birth_date"] or "",
                    phone=row["phone"] or "",
                    email=row["email"] or "",
                    home_address=row["home_address"] or "",
                    registration_date=row["registration_date"] or "",
                    status=row["status"] or "active",
                    notes=row["notes"] or "",
                    passport_series=row["passport_series"] or "",
                    passport_number=row["passport_number"] or ""
                ) for row in rows
            ]

    def get_reader_by_id(self, reader_id: int) -> Optional[Reader]:
        query = "SELECT * FROM readers WHERE id = %s"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reader_id,))
            row = cursor.fetchone()
            if row:
                return Reader(
                    id=row["id"],
                    last_name=row["last_name"],
                    first_name=row["first_name"],
                    middle_name=row["middle_name"] or "",
                    birth_date=row["birth_date"] or "",
                    phone=row["phone"] or "",
                    email=row["email"] or "",
                    home_address=row["home_address"] or "",
                    registration_date=row["registration_date"] or "",
                    status=row["status"] or "active",
                    notes=row["notes"] or "",
                    passport_series=row["passport_series"] or "",
                    passport_number=row["passport_number"] or ""
                )
            return None

    # --- LoanRecord Methods ---

    def create_loan(self, loan: LoanRecord) -> int:
        query = """
            INSERT INTO loan_records (
                item_id, reader_id, issue_date, due_date, 
                return_date, condition_on_issue, condition_on_return
            ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
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
            return cursor.fetchone()["id"]

    def find_active_loan(self, item_id: int) -> Optional[LoanRecord]:
        """Find the current open loan for a specific item."""
        query = "SELECT * FROM loan_records WHERE item_id = %s AND return_date IS NULL"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (item_id,))
            row = cursor.fetchone()
            if row:
                return LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=row["issue_date"] if isinstance(row["issue_date"], datetime) else datetime.fromisoformat(row["issue_date"]),
                    due_date=row["due_date"] if isinstance(row["due_date"], datetime) else datetime.fromisoformat(row["due_date"]),
                    return_date=row["return_date"] if isinstance(row["return_date"], datetime) else (datetime.fromisoformat(row["return_date"]) if row["return_date"] else None),
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                )
            return None

    def close_loan(self, loan_id: int, return_date: datetime, condition: str) -> bool:
        """Update a loan record when a book is returned."""
        query = "UPDATE loan_records SET return_date = %s, condition_on_return = %s WHERE id = %s"
        params = (return_date.isoformat(), condition, loan_id)
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def get_item_history(self, item_id: int) -> List[LoanRecord]:
        query = "SELECT * FROM loan_records WHERE item_id = %s ORDER BY issue_date ASC"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (item_id,))
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=row["issue_date"] if isinstance(row["issue_date"], datetime) else datetime.fromisoformat(row["issue_date"]),
                    due_date=row["due_date"] if isinstance(row["due_date"], datetime) else datetime.fromisoformat(row["due_date"]),
                    return_date=row["return_date"] if isinstance(row["return_date"], datetime) else (datetime.fromisoformat(row["return_date"]) if row["return_date"] else None),
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

    def get_loans_by_reader(self, reader_id: int, active_only: bool = True) -> List[LoanRecord]:
        if active_only:
            query = "SELECT * FROM loan_records WHERE reader_id = %s AND return_date IS NULL"
        else:
            query = "SELECT * FROM loan_records WHERE reader_id = %s"
            
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (reader_id,))
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=row["issue_date"] if isinstance(row["issue_date"], datetime) else datetime.fromisoformat(row["issue_date"]),
                    due_date=row["due_date"] if isinstance(row["due_date"], datetime) else datetime.fromisoformat(row["due_date"]),
                    return_date=row["return_date"] if isinstance(row["return_date"], datetime) else (datetime.fromisoformat(row["return_date"]) if row["return_date"] else None),
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

    def get_all_active_loans(self) -> List[LoanRecord]:
        """Fetch all currently active loans from the database."""
        query = "SELECT * FROM loan_records WHERE return_date IS NULL"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=row["issue_date"] if isinstance(row["issue_date"], datetime) else datetime.fromisoformat(row["issue_date"]),
                    due_date=row["due_date"] if isinstance(row["due_date"], datetime) else datetime.fromisoformat(row["due_date"]),
                    return_date=row["return_date"] if isinstance(row["return_date"], datetime) else (datetime.fromisoformat(row["return_date"]) if row["return_date"] else None),
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

    def get_all_loans(self) -> List[LoanRecord]:
        """Fetch all loan records, including closed ones."""
        query = "SELECT * FROM loan_records"
        with self._db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                LoanRecord(
                    id=row["id"],
                    item_id=row["item_id"],
                    reader_id=row["reader_id"],
                    issue_date=row["issue_date"] if isinstance(row["issue_date"], datetime) else datetime.fromisoformat(row["issue_date"]),
                    due_date=row["due_date"] if isinstance(row["due_date"], datetime) else datetime.fromisoformat(row["due_date"]),
                    return_date=row["return_date"] if isinstance(row["return_date"], datetime) else (datetime.fromisoformat(row["return_date"]) if row["return_date"] else None),
                    condition_on_issue=row["condition_on_issue"] or "",
                    condition_on_return=row["condition_on_return"]
                ) for row in rows
            ]

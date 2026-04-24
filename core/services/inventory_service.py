"""
Inventory service module.

Implements business logic for managing physical book copies, readers, and circulation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from core.models.inventory import BookItem, LoanRecord, ItemStatus
from infrastructure.database.inventory_repository import SQLiteInventoryRepository

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Service for managing the library's physical inventory and circulation.
    """

    def __init__(self, repository: SQLiteInventoryRepository) -> None:
        self._repo = repository

    # --- Fund Management ---

    def add_items(self, book_id: int, count: int, start_inv: Optional[int] = None, location: Optional[str] = None) -> List[int]:
        """
        Generate N physical copies for a specific book with sequential inventory numbers.
        """
        if start_inv is None:
            start_inv = self._repo.get_max_inventory_number() + 1

        created_ids = []
        for i in range(count):
            inv_num = str(start_inv + i)
            item = BookItem(
                inventory_number=inv_num,
                book_id=book_id,
                status=ItemStatus.AVAILABLE,
                location=location or ""
            )
            item_id = self._repo.add_item(item)
            created_ids.append(item_id)
            
        logger.info(f"Added {count} copies for book {book_id}, starting from {start_inv}, location: {location}")
        return created_ids

    def get_items_by_book(self, book_id: int) -> List[BookItem]:
        """Get all physical copies of a specific book."""
        return self._repo.get_items_by_book(book_id)

    # --- Circulation (Loans & Returns) ---

    def issue_item_by_inv(self, inv_num: str, reader_id: int, days: int = 14) -> int:
        """
        Issue a physical copy using its inventory number.
        """
        item = self._find_item_by_inv(inv_num)
        return self.issue_item(item.id, reader_id, days)

    def return_item_by_inv(self, inv_num: str, condition: str) -> bool:
        """
        Return a physical copy using its inventory number.
        """
        item = self._find_item_by_inv(inv_num)
        return self.return_item(item.id, condition)

    def _find_item_by_inv(self, inv_num: str) -> BookItem:
        """
        Helper to find a BookItem by its inventory number.
        """
        item = self._repo.get_item_by_inventory_number(inv_num)
        if not item:
            raise ValueError(f"Экземпляр с номером {inv_num} не найден")
        return item

    def issue_item(self, item_id: int, reader_id: int, days: int = 14) -> int:
        """
        Issue a physical copy to a reader.
        
        Validates that the item is AVAILABLE and the reader is ACTIVE.
        """
        item = self._repo.get_item_by_id(item_id)
        reader = self._repo.get_reader_by_id(reader_id)

        if not item:
            raise ValueError(f"Book item with ID {item_id} not found.")
        if not reader:
            raise ValueError(f"Reader with ID {reader_id} not found.")
        
        if item.status != ItemStatus.AVAILABLE:
            raise ValueError(f"Item {item.inventory_number} is not available (Status: {item.status.value}).")
        
        if not reader.is_active:
            raise ValueError(f"Reader {reader.full_name} is not active.")

        # Create Loan Record
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=days)
        
        loan = LoanRecord(
            item_id=item_id,
            reader_id=reader_id,
            issue_date=issue_date,
            due_date=due_date,
            condition_on_issue="Good" # Default condition
        )
        
        loan_id = self._repo.create_loan(loan)
        
        # Update Item Status to LOANED
        self._repo.update_item_status(item_id, ItemStatus.LOANED)
        
        logger.info(f"Item {item.inventory_number} issued to reader {reader.full_name}. Due: {due_date.date()}")
        return loan_id

    def return_item(self, item_id: int, condition: str) -> bool:
        """
        Return a physical copy.
        
        Finds the active loan record, closes it, and sets item status back to AVAILABLE.
        """
        active_loan = self._repo.find_active_loan(item_id)
        if not active_loan:
            raise ValueError(f"No active loan found for item ID {item_id}.")

        return_date = datetime.now()
        
        # Close the loan record
        success = self._repo.close_loan(active_loan.id, return_date, condition)
        
        if success:
            # Update item status to AVAILABLE
            self._repo.update_item_status(item_id, ItemStatus.AVAILABLE)
            logger.info(f"Item ID {item_id} returned. Condition: {condition}")
            return True
            
        return False

    def update_item_status(self, item_id: int, new_status: ItemStatus) -> bool:
        """
        Universal method to change item status (REPAIR, LOST, etc.).
        
        Prevents status change if the book is currently LOANED.
        """
        item = self._repo.get_item_by_id(item_id)
        if not item:
            raise ValueError(f"Item with ID {item_id} not found.")

        if item.status == ItemStatus.LOANED:
            raise ValueError(f"Cannot change status of item {item.inventory_number} while it is LOANED. Please return it first.")

        success = self._repo.update_item_status(item_id, new_status)
        if success:
            logger.info(f"Item {item.inventory_number} status updated to {new_status.value}")
        return success

    # --- Audit & History ---

    def get_item_history(self, item_id: int) -> List[LoanRecord]:
        """Get chronological history of all loans for a specific item."""
        return self._repo.get_item_history(item_id)

    def get_reader_current_loans(self, reader_id: int) -> List[LoanRecord]:
        """Get books currently held by a reader."""
        return self._repo.get_loans_by_reader(reader_id, active_only=True)

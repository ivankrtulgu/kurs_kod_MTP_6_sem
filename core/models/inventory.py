"""
Inventory model module.

Provides models for tracking physical book copies, readers, and loan history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ItemStatus(Enum):
    """
    Statuses for physical book copies.
    """
    AVAILABLE = "AVAILABLE"
    LOANED = "LOANED"
    LOST = "LOST"
    REPAIR = "REPAIR"
    WRITTEN_OFF = "WRITTEN_OFF"


@dataclass
class BookItem:
    """
    Represents a physical copy of a book.
    
    Attributes:
        id: Primary key.
        inventory_number: Unique sequential inventory number.
        book_id: Foreign key to Book.id.
        status: Current status of the item.
        location: Shelf/room location according to GOST R 7.0.93-2015.
    """
    inventory_number: str
    book_id: int
    status: ItemStatus = ItemStatus.AVAILABLE
    location: str = ""
    id: int = 0


@dataclass
class Reader:
    """
    Represents a library reader.
    
    Attributes:
        full_name: Reader's full name.
        phone: Contact phone number.
        is_active: Whether the reader is allowed to borrow books.
    """
    full_name: str
    phone: str
    is_active: bool = True
    id: int = 0


@dataclass
class LoanRecord:
    """
    Represents a record in the loan journal.
    
    Attributes:
        item_id: Foreign key to BookItem.id.
        reader_id: Foreign key to Reader.id.
        issue_date: Date and time of issuance.
        due_date: Expected return date.
        return_date: Actual return date (None if still loaned).
        condition_on_issue: State of the book when issued.
        condition_on_return: State of the book when returned.
    """
    item_id: int
    reader_id: int
    issue_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=datetime.now)
    return_date: Optional[datetime] = None
    condition_on_issue: str = ""
    condition_on_return: Optional[str] = None
    id: int = 0

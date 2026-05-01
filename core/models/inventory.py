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
        qr_code_path: Path to the generated QR code image.
    """
    inventory_number: str
    book_id: int
    status: ItemStatus = ItemStatus.AVAILABLE
    location: str = ""
    qr_code_path: Optional[str] = None
    id: int = 0


@dataclass
class Reader:
    """
    Represents a library reader.
    
    Attributes:
        last_name: Reader's surname.
        first_name: Reader's given name.
        middle_name: Reader's patronymic (optional).
        birth_date: Date of birth (ISO format).
        phone: Contact phone number.
        email: Contact email address.
        home_address: Residential address.
        registration_date: Date of library registration.
        status: Current status ('active', 'blocked', 'expired').
        notes: Additional remarks.
        passport_series: Passport series.
        passport_number: Passport number.
        id: Primary key.
    """
    last_name: str
    first_name: str
    middle_name: str = ""
    birth_date: str = ""
    phone: str = ""
    email: str = ""
    home_address: str = ""
    registration_date: str = ""
    status: str = "active"
    notes: str = ""
    passport_series: str = ""
    passport_number: str = ""
    id: int = 0

    @property
    def full_name(self) -> str:
        """Returns the full name of the reader formatted as 'Last Name First Name Middle Name'."""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p and p.strip())

    @property
    def is_active(self) -> bool:
        """Checks if the reader is currently active."""
        return self.status == "active"


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

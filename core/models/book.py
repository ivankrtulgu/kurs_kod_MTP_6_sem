"""
Book model module.

Provides the Book dataclass for representing bibliographic records
according to GOST R 7.0.4-2020 standard.

GOST R 7.0.4-2020 defines:
- Required fields: author, title, place, publisher, year, pages, isbn
- Optional fields: subtitle, responsibility, edition, copyright, udc, bbk, author_mark
- Additional fields: reviewers, annotation, abstract, doi, content_type, access_method
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


@dataclass
class Book:
    """
    Represents a bibliographic record following GOST R 7.0.4-2020 standard.

    This dataclass encapsulates all required and optional fields for
    describing a book publication according to Russian bibliographic
    standards.

    Attributes:
        Required fields (per GOST R 7.0.4-2020):
            author: Author name(s) in format "Фамилия И.О."
            title: Main title of the work
            place: Place of publication (city)
            publisher: Publisher name
            year: Publication year (1900-2100)
            pages: Number of pages (> 0)
            isbn: ISBN number (ISBN-10 or ISBN-13)

        Optional fields (per GOST R 7.0.4-2020):
            subtitle: Subtitle info (учебник, справочник и др.)
            responsibility: Responsibility info (editors, organizations)
            edition: Edition info (2-е изд., перераб. и доп.)
            copyright: Copyright mark
            udc: UDC index (УДК)
            bbk: BBK index (ББК)
            author_mark: Author mark

        Additional fields:
            reviewers: Reviewer info
            annotation: Publisher annotation
            abstract: Abstract
            doi: Digital Object Identifier
            content_type: Content type (Текст)
            access_method: Access method (непосредственный)

        System fields:
            id: Primary key (auto-generated)
            created_at: Creation date (auto-generated)
            qr_code_path: Path to QR code image
            cover_image_path: Path to cover image

    Example:
        >>> book = Book(
        ...     author="Иванов И.И.",
        ...     title="Основы программирования",
        ...     place="Москва",
        ...     publisher="Наука",
        ...     year=2024,
        ...     pages=350,
        ...     isbn="978-5-02-040500-0"
        ... )
        >>> print(book.format_bibliographic_record())
    """

    # Required fields (per GOST R 7.0.4-2020)
    author: str
    title: str
    place: str
    publisher: str
    year: int
    pages: int
    isbn: str

    # Optional fields (per GOST R 7.0.4-2020)
    subtitle: str = ""
    responsibility: str = ""
    edition: str = ""
    copyright: str = ""
    udc: str = ""
    bbk: str = ""
    author_mark: str = ""

    # Additional fields
    reviewers: str = ""
    annotation: str = ""
    abstract: str = ""
    doi: str = ""
    content_type: str = "Текст"
    access_method: str = "непосредственный"

    # System fields
    id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    qr_code_path: str = ""
    cover_image_path: str = ""

    def format_bibliographic_record(self) -> str:
        """
        Format the book data as a bibliographic record per GOST R 7.0.4-2020.

        Returns:
            str: Formatted bibliographic record string following
                 GOST R 7.0.4-2020 template.

        Example:
            >>> book = Book(
            ...     author="Иванов И.И.",
            ...     title="Основы программирования",
            ...     subtitle="Учебное пособие",
            ...     responsibility="Под ред. Петрова П.П.",
            ...     edition="2-е изд., перераб. и доп.",
            ...     place="Москва",
            ...     publisher="Наука",
            ...     year=2024,
            ...     pages=350,
            ...     isbn="978-5-02-040500-0"
            ... )
            >>> record = book.format_bibliographic_record()
            >>> print(record)
            Иванов И.И. Основы программирования : Учебное пособие /
            Под ред. Петрова П.П. — 2-е изд., перераб. и доп. —
            Москва : Наука, 2024. — 350 с. — ISBN 978-5-02-040500-0.
        """
        # Build the bibliographic record following GOST R 7.0.4-2020 template
        parts: list[str] = []

        # Author
        if self.author:
            parts.append(self.author)

        # Title and subtitle
        title_part = self.title
        if self.subtitle:
            title_part += f" : {self.subtitle}"
        parts.append(title_part)

        # Responsibility
        if self.responsibility:
            parts.append(f"/ {self.responsibility}")

        # Edition
        if self.edition:
            parts.append(f"— {self.edition}")

        # Place, Publisher, Year
        publication_info = f"{self.place} : {self.publisher}, {self.year}"
        parts.append(f"— {publication_info}")

        # Pages
        parts.append(f"— {self.pages} с.")

        # ISBN
        if self.isbn:
            parts.append(f"— ISBN {self.isbn}")

        # Join parts with appropriate separators
        record = " ".join(parts)

        # Add UDC and BBK if present
        extras: list[str] = []
        if self.udc:
            extras.append(f"УДК {self.udc}")
        if self.bbk:
            extras.append(f"ББК {self.bbk}")

        if extras:
            record += " — " + "; ".join(extras)

        # Add DOI if present
        if self.doi:
            record += f" — DOI {self.doi}"

        # Add content type and access method
        if self.content_type or self.access_method:
            content_parts = []
            if self.content_type:
                content_parts.append(self.content_type)
            if self.access_method:
                content_parts.append(f"режим доступа: {self.access_method}")
            record += f" — {'; '.join(content_parts)}"

        return record

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """
        Create a Book instance from a dictionary.

        Args:
            data: Dictionary containing book field values.

        Returns:
            Book: New Book instance with fields populated from the dictionary.

        Example:
            >>> data = {
            ...     "author": "Иванов И.И.",
            ...     "title": "Основы программирования",
            ...     ...
            ... }
            >>> book = Book.from_dict(data)
        """
        # Extract datetime if present as string
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        # Filter out None values and use defaults for missing fields
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {
            k: v for k, v in data.items()
            if k in field_names and v is not None
        }

        return cls(**filtered_data)

    def to_dict(self) -> dict:
        """
        Convert the Book instance to a dictionary.

        Returns:
            dict: Dictionary representation of the Book with all fields.

        Example:
            >>> book = Book(author="Иванов И.И.", title="Test", ...)
            >>> data = book.to_dict()
            >>> print(data["author"])
            Иванов И.И.
        """
        return {
            "id": self.id,
            "author": self.author,
            "title": self.title,
            "subtitle": self.subtitle,
            "responsibility": self.responsibility,
            "edition": self.edition,
            "place": self.place,
            "publisher": self.publisher,
            "year": self.year,
            "pages": self.pages,
            "isbn": self.isbn,
            "copyright": self.copyright,
            "udc": self.udc,
            "bbk": self.bbk,
            "author_mark": self.author_mark,
            "reviewers": self.reviewers,
            "annotation": self.annotation,
            "abstract": self.abstract,
            "doi": self.doi,
            "content_type": self.content_type,
            "access_method": self.access_method,
            "created_at": self.created_at.isoformat(),
            "qr_code_path": self.qr_code_path,
            "cover_image_path": self.cover_image_path,
        }

    def __str__(self) -> str:
        """
        Return a string representation of the Book.

        Returns:
            str: Human-readable string with author and title.
        """
        return f"{self.author}. {self.title} ({self.year})"

    def __post_init__(self) -> None:
        """
        Validate required fields after initialization.

        Validates according to GOST R 7.0.4-2020:
        - Required fields must be non-empty
        - Year must be between 1900 and 2100
        - Pages must be greater than 0
        - ISBN must be valid (ISBN-10 or ISBN-13)

        Raises:
            ValueError: If any required field is invalid.
        """
        # Import ISBNValidator here to avoid circular import
        from core.services.book_service import ISBNValidator

        errors: list[str] = []

        # Validate required fields are non-empty
        required_fields = ["author", "title", "place", "publisher", "isbn"]

        for field_name in required_fields:
            value = getattr(self, field_name)
            if not value or not str(value).strip():
                errors.append(f"Required field '{field_name}' cannot be empty")

        # Validate year (1900-2100 per GOST R 7.0.4-2020)
        if not isinstance(self.year, int):
            errors.append(f"Year must be an integer, got {type(self.year).__name__}")
        elif not (1900 <= self.year <= 2100):
            errors.append(f"Year must be between 1900 and 2100, got {self.year}")

        # Validate pages (> 0)
        if not isinstance(self.pages, int):
            errors.append(f"Pages must be an integer, got {type(self.pages).__name__}")
        elif self.pages <= 0:
            errors.append(f"Pages must be greater than 0, got {self.pages}")

        # Validate ISBN format and check digit
        if self.isbn and str(self.isbn).strip():
            is_valid, error = ISBNValidator.validate(str(self.isbn))
            if not is_valid:
                errors.append(f"Invalid ISBN: {error}")

        if errors:
            raise ValueError("; ".join(errors))

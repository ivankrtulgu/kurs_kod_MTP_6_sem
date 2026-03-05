"""
Tests for ISBN validation.

Tests the ISBNValidator class for ISBN-10 and ISBN-13 validation.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.book_service import ISBNValidator


class TestISBN10Validation:
    """Tests for ISBN-10 validation."""

    def test_valid_isbn10_with_hyphens(self):
        """Test valid ISBN-10 with hyphens."""
        is_valid, error = ISBNValidator.validate("2-266-11156-6")
        assert is_valid is True
        assert error is None

    def test_valid_isbn10_without_hyphens(self):
        """Test valid ISBN-10 without hyphens."""
        is_valid, error = ISBNValidator.validate("2266111566")
        assert is_valid is True
        assert error is None

    def test_valid_isbn10_with_x_check_digit(self):
        """Test valid ISBN-10 with X as check digit."""
        # 0-8044-2957-X is a valid ISBN with X check digit
        is_valid, error = ISBNValidator.validate("0-8044-2957-X")
        assert is_valid is True, f"Expected valid ISBN, got error: {error}"

    def test_valid_isbn10_russian_book(self):
        """Test valid Russian ISBN-10."""
        is_valid, error = ISBNValidator.validate("5-02-040500-0")
        assert is_valid is True
        assert error is None

    def test_invalid_isbn10_wrong_check_digit(self):
        """Test ISBN-10 with wrong check digit."""
        is_valid, error = ISBNValidator.validate("2-266-11156-5")  # Should be 6
        assert is_valid is False
        assert "check digit" in error.lower()

    def test_invalid_isbn10_too_short(self):
        """Test ISBN-10 that is too short."""
        is_valid, error = ISBNValidator.validate("2-266-1115-6")
        assert is_valid is False
        assert "digits" in error.lower()

    def test_invalid_isbn10_too_long(self):
        """Test ISBN-10 that is too long."""
        is_valid, error = ISBNValidator.validate("2-266-111567-6")
        assert is_valid is False
        assert "digits" in error.lower()

    def test_invalid_isbn10_non_digit_characters(self):
        """Test ISBN-10 with non-digit characters (except X)."""
        is_valid, error = ISBNValidator.validate("2-26A-11156-6")
        assert is_valid is False

    def test_invalid_isbn10_x_in_wrong_position(self):
        """Test ISBN-10 with X in wrong position."""
        is_valid, error = ISBNValidator.validate("X-266-11156-6")
        assert is_valid is False


class TestISBN13Validation:
    """Tests for ISBN-13 validation."""

    def test_valid_isbn13_with_hyphens_978(self):
        """Test valid ISBN-13 with 978 prefix."""
        is_valid, error = ISBNValidator.validate("978-2-266-11156-0")
        assert is_valid is True
        assert error is None

    def test_valid_isbn13_without_hyphens(self):
        """Test valid ISBN-13 without hyphens."""
        is_valid, error = ISBNValidator.validate("9782266111560")
        assert is_valid is True
        assert error is None

    def test_valid_isbn13_979_prefix(self):
        """Test valid ISBN-13 with 979 prefix."""
        # Valid ISBN-13 with 979 prefix
        is_valid, error = ISBNValidator.validate("979-10-90636-07-1")
        assert is_valid is True
        assert error is None

    def test_valid_isbn13_russian_book(self):
        """Test valid Russian ISBN-13."""
        # 978-5-699-12345-? - calculated check digit is 2
        is_valid, error = ISBNValidator.validate("978-5-699-12345-2")
        assert is_valid is True
        assert error is None

    def test_invalid_isbn13_wrong_check_digit(self):
        """Test ISBN-13 with wrong check digit."""
        is_valid, error = ISBNValidator.validate("978-2-266-11156-1")  # Should be 0
        assert is_valid is False
        assert "check digit" in error.lower()

    def test_invalid_isbn13_wrong_prefix(self):
        """Test ISBN-13 with invalid prefix."""
        is_valid, error = ISBNValidator.validate("977-2-266-11156-0")
        assert is_valid is False
        assert "978 or 979" in error

    def test_invalid_isbn13_too_short(self):
        """Test ISBN-13 that is too short."""
        is_valid, error = ISBNValidator.validate("978-2-266-1115-0")
        assert is_valid is False
        assert "13 digits" in error.lower()

    def test_invalid_isbn13_too_long(self):
        """Test ISBN-13 that is too long."""
        is_valid, error = ISBNValidator.validate("978-2-266-111567-0")
        assert is_valid is False
        assert "13 digits" in error.lower()

    def test_invalid_isbn13_non_digit_characters(self):
        """Test ISBN-13 with non-digit characters."""
        is_valid, error = ISBNValidator.validate("978-2-26A-11156-0")
        assert is_valid is False
        assert "only digits" in error.lower()


class TestISBNGeneral:
    """General ISBN validation tests."""

    def test_empty_isbn(self):
        """Test empty ISBN."""
        is_valid, error = ISBNValidator.validate("")
        assert is_valid is False
        assert "required" in error.lower()

    def test_none_isbn(self):
        """Test None ISBN."""
        is_valid, error = ISBNValidator.validate(None)
        assert is_valid is False
        assert "required" in error.lower()

    def test_isbn_with_spaces(self):
        """Test ISBN with spaces instead of hyphens."""
        # 978-5-699-12345-2 with spaces
        is_valid, error = ISBNValidator.validate("978 5 699 12345 2")
        assert is_valid is True
        assert error is None

    def test_isbn_with_mixed_separators(self):
        """Test ISBN with mixed separators."""
        # 978-5-699-12345-2 with mixed separators
        is_valid, error = ISBNValidator.validate("978-5 699-12345 2")
        assert is_valid is True
        assert error is None

    def test_completely_invalid_isbn(self):
        """Test completely invalid ISBN."""
        is_valid, error = ISBNValidator.validate("invalid-isbn")
        assert is_valid is False
        assert "digits" in error.lower()

    def test_isbn10_lowercase_x(self):
        """Test ISBN-10 with lowercase x."""
        # lowercase x should be normalized to uppercase
        is_valid, error = ISBNValidator.validate("0-8044-2957-x")
        assert is_valid is True, f"Expected valid ISBN, got: {error}"


class TestISBNValidatorExamples:
    """Test real-world ISBN examples."""

    def test_real_isbns(self):
        """Test various real ISBNs with valid check digits."""
        valid_isbns = [
            "978-5-699-12345-2",  # Russian book ISBN-13 (calculated)
            "978-0-13-468599-1",  # English book ISBN-13
            "978-3-16-148410-0",  # German book ISBN-13
            "5-02-040500-0",      # Russian book ISBN-10
            "0-8044-2957-X",      # ISBN-10 with X check digit
            "2-266-11156-6",      # French book ISBN-10
        ]
        
        for isbn in valid_isbns:
            is_valid, error = ISBNValidator.validate(isbn)
            assert is_valid is True, f"Failed for ISBN: {isbn}, error: {error}"

    def test_known_invalid_isbns(self):
        """Test known invalid ISBNs."""
        invalid_isbns = [
            "978-5-02-040500-1",  # Wrong check digit
            "5-02-040500-1",      # Wrong check digit ISBN-10
            "977-5-02-040500-0",  # Wrong prefix
            "1234567890",         # Random 10 digits
            "1234567890123",      # Random 13 digits
        ]
        
        for isbn in invalid_isbns:
            is_valid, error = ISBNValidator.validate(isbn)
            assert is_valid is False, f"Should be invalid: {isbn}"

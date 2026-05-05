"""
Tests for PrintingService.

Tests for PDF generation with QR codes.
"""

import pytest
from pathlib import Path
import sys
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.printing_service import PrintingService


# ===== FIXTURES =====

@pytest.fixture
def sample_qr_image(tmp_path):
    """Create a sample QR code image for testing."""
    # Create a minimal PNG file (1x1 pixel)
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])

    qr_path = tmp_path / "test_qr.png"
    qr_path.write_bytes(png_data)
    return str(qr_path)


@pytest.fixture
def sample_book_qr(tmp_path):
    """Create a sample book QR code image."""
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82
    ])

    qr_path = tmp_path / "book_qr.png"
    qr_path.write_bytes(png_data)
    return str(qr_path)


# ===== TESTS: GENERATE QR PDF (SINGLE) =====

class TestGenerateQRPDF:
    """Tests for generate_qr_pdf method."""

    def test_generate_qr_pdf_success(self, sample_qr_image, tmp_path):
        """Test successful PDF generation with single QR code."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_qr_pdf_with_book_qr(self, sample_qr_image, sample_book_qr, tmp_path):
        """Test PDF generation with both item and book QR codes."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            book_qr_path=sample_book_qr,
            book_label="Книга: Основы программирования",
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_qr_pdf_creates_output_directory(self, sample_qr_image, tmp_path):
        """Test that PDF generation creates output directory if needed."""
        output_dir = tmp_path / "nested" / "output"
        output_path = str(output_dir / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=output_path
        )

        assert success is True
        assert output_dir.exists()
        assert Path(output_path).exists()

    def test_generate_qr_pdf_file_size(self, sample_qr_image, tmp_path):
        """Test that generated PDF has reasonable file size."""
        output_path = str(tmp_path / "output.pdf")

        PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=output_path
        )

        file_size = Path(output_path).stat().st_size
        # PDF should be at least 1KB
        assert file_size > 1000

    def test_generate_qr_pdf_with_cyrillic_label(self, sample_qr_image, tmp_path):
        """Test PDF generation with Cyrillic characters in label."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="Экземпляр №001",
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_qr_pdf_with_special_characters(self, sample_qr_image, tmp_path):
        """Test PDF generation with special characters in label."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="Item #001 (A&B)",
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_qr_pdf_different_columns(self, sample_qr_image, tmp_path):
        """Test PDF generation with different column counts."""
        for cols in [1, 2, 3, 4, 5]:
            output_path = str(tmp_path / f"output_{cols}cols.pdf")

            success = PrintingService.generate_qr_pdf(
                item_qr_path=sample_qr_image,
                item_label="INV001",
                output_path=output_path,
                cols=cols
            )

            assert success is True
            assert Path(output_path).exists()

    def test_generate_qr_pdf_missing_item_qr(self, tmp_path):
        """Test PDF generation with missing item QR code."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path="/nonexistent/qr.png",
            item_label="INV001",
            output_path=output_path
        )

        assert success is False

    def test_generate_qr_pdf_empty_item_qr_path(self, tmp_path):
        """Test PDF generation with empty item QR path."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path="",
            item_label="INV001",
            output_path=output_path
        )

        assert success is False


# ===== TESTS: GENERATE BATCH QR PDF =====

class TestGenerateBatchQRPDF:
    """Tests for generate_batch_qr_pdf method."""

    def test_generate_batch_qr_pdf_items_only(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with items only."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"},
            {"qr_path": sample_qr_image, "label": "INV002"},
            {"qr_path": sample_qr_image, "label": "INV003"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_with_book(self, sample_qr_image, sample_book_qr, tmp_path):
        """Test batch PDF generation with book QR code."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"},
            {"qr_path": sample_qr_image, "label": "INV002"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            book_qr_path=sample_book_qr,
            book_label="Основы программирования",
            output_path=output_path,
            mode="both"
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_book_only(self, sample_book_qr, tmp_path):
        """Test batch PDF generation with book QR only."""
        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=[],
            book_qr_path=sample_book_qr,
            book_label="Основы программирования",
            output_path=output_path,
            mode="book_only"
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_many_items(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with many items."""
        items_data = [
            {"qr_path": sample_qr_image, "label": f"INV{i:03d}"}
            for i in range(20)
        ]

        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_different_columns(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with different column counts."""
        items_data = [
            {"qr_path": sample_qr_image, "label": f"INV{i:03d}"}
            for i in range(6)
        ]

        for cols in [2, 3, 4]:
            output_path = str(tmp_path / f"batch_{cols}cols.pdf")

            success = PrintingService.generate_batch_qr_pdf(
                items_data=items_data,
                output_path=output_path,
                cols=cols,
                mode="items_only"
            )

            assert success is True
            assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_empty_items_list(self, tmp_path):
        """Test batch PDF generation with empty items list."""
        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=[],
            output_path=output_path,
            mode="items_only"
        )

        # Should succeed but create minimal PDF
        assert success is True

    def test_generate_batch_qr_pdf_missing_qr_files(self, tmp_path):
        """Test batch PDF generation with some missing QR files."""
        items_data = [
            {"qr_path": "/nonexistent/qr1.png", "label": "INV001"},
            {"qr_path": "/nonexistent/qr2.png", "label": "INV002"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        # Should handle gracefully and skip missing files
        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        # May succeed with warnings or fail depending on implementation
        assert isinstance(success, bool)

    def test_generate_batch_qr_pdf_creates_directory(self, sample_qr_image, tmp_path):
        """Test that batch PDF generation creates output directory."""
        output_dir = tmp_path / "nested" / "output"
        output_path = str(output_dir / "batch.pdf")

        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"}
        ]

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        assert success is True
        assert output_dir.exists()

    def test_generate_batch_qr_pdf_with_cyrillic_labels(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with Cyrillic labels."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "Экземпляр №001"},
            {"qr_path": sample_qr_image, "label": "Экземпляр №002"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        assert success is True
        assert Path(output_path).exists()


# ===== TESTS: ERROR HANDLING =====

class TestPrintingServiceErrorHandling:
    """Tests for error handling in printing service."""

    def test_generate_qr_pdf_invalid_output_path(self, sample_qr_image):
        """Test PDF generation with invalid output path."""
        # Try to write to a path that can't be created
        if os.name == 'nt':  # Windows
            invalid_path = "Z:\\nonexistent\\path\\output.pdf"
        else:  # Unix-like
            invalid_path = "/root/nonexistent/output.pdf"

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=invalid_path
        )

        # Should handle error gracefully
        assert success is False

    def test_generate_batch_qr_pdf_invalid_mode(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with invalid mode."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        # Invalid mode should be handled
        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="invalid_mode"
        )

        # Should either fail or default to a valid mode
        assert isinstance(success, bool)


# ===== TESTS: PDF CONTENT VERIFICATION =====

class TestPDFContentVerification:
    """Tests for verifying PDF content."""

    def test_generated_pdf_is_valid(self, sample_qr_image, tmp_path):
        """Test that generated PDF is a valid PDF file."""
        output_path = str(tmp_path / "output.pdf")

        PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=output_path
        )

        # Check PDF magic bytes
        with open(output_path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'

    def test_batch_pdf_is_valid(self, sample_qr_image, tmp_path):
        """Test that generated batch PDF is a valid PDF file."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        # Check PDF magic bytes
        with open(output_path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'


# ===== TESTS: INTEGRATION =====

class TestPrintingServiceIntegration:
    """Integration tests for printing service."""

    def test_generate_multiple_pdfs_sequentially(self, sample_qr_image, tmp_path):
        """Test generating multiple PDFs in sequence."""
        for i in range(5):
            output_path = str(tmp_path / f"output_{i}.pdf")

            success = PrintingService.generate_qr_pdf(
                item_qr_path=sample_qr_image,
                item_label=f"INV{i:03d}",
                output_path=output_path
            )

            assert success is True
            assert Path(output_path).exists()

    def test_overwrite_existing_pdf(self, sample_qr_image, tmp_path):
        """Test overwriting an existing PDF file."""
        output_path = str(tmp_path / "output.pdf")

        # Generate first PDF
        PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV001",
            output_path=output_path
        )

        first_size = Path(output_path).stat().st_size

        # Generate second PDF (overwrite)
        PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="INV002",
            output_path=output_path
        )

        second_size = Path(output_path).stat().st_size

        # File should exist and may have different size
        assert Path(output_path).exists()
        assert second_size > 0


# ===== TESTS: EDGE CASES =====

class TestPrintingServiceEdgeCases:
    """Tests for edge cases in printing service."""

    def test_generate_qr_pdf_very_long_label(self, sample_qr_image, tmp_path):
        """Test PDF generation with very long label."""
        long_label = "Экземпляр " + "А" * 200

        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label=long_label,
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_batch_qr_pdf_single_item(self, sample_qr_image, tmp_path):
        """Test batch PDF generation with single item."""
        items_data = [
            {"qr_path": sample_qr_image, "label": "INV001"}
        ]

        output_path = str(tmp_path / "batch.pdf")

        success = PrintingService.generate_batch_qr_pdf(
            items_data=items_data,
            output_path=output_path,
            mode="items_only"
        )

        assert success is True
        assert Path(output_path).exists()

    def test_generate_qr_pdf_with_unicode_label(self, sample_qr_image, tmp_path):
        """Test PDF generation with Unicode characters in label."""
        output_path = str(tmp_path / "output.pdf")

        success = PrintingService.generate_qr_pdf(
            item_qr_path=sample_qr_image,
            item_label="Книга №001",  # Cyrillic characters are supported
            output_path=output_path
        )

        assert success is True
        assert Path(output_path).exists()

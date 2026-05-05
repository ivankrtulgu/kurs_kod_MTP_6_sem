"""
Tests for BarcodeEventFilter (Scanner Integration).

Tests for barcode/QR scanner event filtering and processing.
"""

import pytest
import json
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget
from ui.scanner_filter import BarcodeEventFilter


# ===== FIXTURES =====

@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_main_window(qapp):
    """Create mock main window for testing."""
    window = QWidget()
    return window


@pytest.fixture
def scanner_filter(mock_main_window):
    """Create BarcodeEventFilter instance."""
    return BarcodeEventFilter(mock_main_window)


# ===== TESTS: INITIALIZATION =====

class TestBarcodeEventFilterInitialization:
    """Tests for BarcodeEventFilter initialization."""

    def test_filter_initialization(self, scanner_filter):
        """Test that filter initializes correctly."""
        assert scanner_filter is not None
        assert scanner_filter._buffer == ""
        assert scanner_filter._timer is not None

    def test_filter_has_scan_detected_signal(self, scanner_filter):
        """Test that filter has scan_detected signal."""
        assert hasattr(scanner_filter, 'scan_detected')

    def test_filter_has_layout_map(self, scanner_filter):
        """Test that filter has Russian-to-Latin layout map."""
        assert hasattr(scanner_filter, '_layout_map')
        assert isinstance(scanner_filter._layout_map, dict)
        # Check some mappings
        assert 'й' in scanner_filter._layout_map
        assert 'ц' in scanner_filter._layout_map


# ===== TESTS: CHARACTER BUFFERING =====

class TestCharacterBuffering:
    """Tests for character buffering functionality."""

    def test_buffer_single_character(self, scanner_filter, qapp):
        """Test buffering a single character."""
        # Simulate key press
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a")

        scanner_filter._buffer = ""
        scanner_filter.eventFilter(scanner_filter._main_window, event)

        assert "a" in scanner_filter._buffer

    def test_buffer_multiple_characters(self, scanner_filter, qapp):
        """Test buffering multiple characters."""
        scanner_filter._buffer = ""

        chars = "test"
        for char in chars:
            key = getattr(Qt, f'Key_{char.upper()}')
            event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, char)
            scanner_filter.eventFilter(scanner_filter._main_window, event)

        assert "test" in scanner_filter._buffer

    def test_buffer_clears_after_processing(self, scanner_filter, qapp):
        """Test that buffer clears after processing."""
        scanner_filter._buffer = "test_data"
        scanner_filter._process_buffer()

        assert scanner_filter._buffer == ""


# ===== TESTS: RUSSIAN LAYOUT TRANSLATION =====

class TestRussianLayoutTranslation:
    """Tests for Russian keyboard layout translation."""

    def test_translate_russian_to_latin(self, scanner_filter):
        """Test translating Russian characters to Latin."""
        # Test some common mappings
        assert scanner_filter._layout_map.get('й') == 'q'
        assert scanner_filter._layout_map.get('ц') == 'w'
        assert scanner_filter._layout_map.get('у') == 'e'

    def test_translate_russian_brackets(self, scanner_filter):
        """Test translating Russian brackets for JSON."""
        assert scanner_filter._layout_map.get('х') == '['
        assert scanner_filter._layout_map.get('ъ') == ']'

    def test_translate_russian_quotes(self, scanner_filter):
        """Test translating Russian quotes for JSON."""
        assert scanner_filter._layout_map.get('э') == '"'


# ===== TESTS: JSON PARSING =====

class TestJSONParsing:
    """Tests for JSON parsing from scanned data."""

    def test_parse_valid_item_json(self, scanner_filter, qapp, qtbot):
        """Test parsing valid item JSON."""
        item_data = {
            "item_inv": "INV001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2"
        }

        scanner_filter._buffer = json.dumps(item_data)

        # Connect signal to capture emission
        scan_type = None
        identifier = None

        def on_scan(st, id):
            nonlocal scan_type, identifier
            scan_type = st
            identifier = id

        scanner_filter.scan_detected.connect(on_scan)
        scanner_filter._process_buffer()

        assert scan_type == "item"
        assert identifier == "INV001"

    def test_parse_valid_book_json(self, scanner_filter, qapp, qtbot):
        """Test parsing valid book JSON."""
        book_data = {
            "isbn": "978-5-699-12345-2",
            "doi": "10.1000/test",
            "biblio": "Test bibliographic record"
        }

        scanner_filter._buffer = json.dumps(book_data)

        scan_type = None
        identifier = None

        def on_scan(st, id):
            nonlocal scan_type, identifier
            scan_type = st
            identifier = id

        scanner_filter.scan_detected.connect(on_scan)
        scanner_filter._process_buffer()

        assert scan_type == "book"
        assert identifier == "978-5-699-12345-2"

    def test_parse_invalid_json(self, scanner_filter, qapp):
        """Test parsing invalid JSON."""
        scanner_filter._buffer = "not valid json"

        # Should not raise exception
        scanner_filter._process_buffer()

        # Buffer should be cleared
        assert scanner_filter._buffer == ""

    def test_parse_json_without_required_keys(self, scanner_filter, qapp):
        """Test parsing JSON without required keys."""
        data = {"some_key": "some_value"}
        scanner_filter._buffer = json.dumps(data)

        scan_type = None

        def on_scan(st, id):
            nonlocal scan_type
            scan_type = st

        scanner_filter.scan_detected.connect(on_scan)
        scanner_filter._process_buffer()

        # Should not emit signal for unrecognized data
        assert scan_type is None


# ===== TESTS: ENTER KEY PROCESSING =====

class TestEnterKeyProcessing:
    """Tests for Enter key immediate processing."""

    def test_enter_key_triggers_processing(self, scanner_filter, qapp):
        """Test that Enter key triggers immediate buffer processing."""
        scanner_filter._buffer = json.dumps({"item_inv": "INV001", "book_id": 1, "isbn": "123"})

        # Simulate Enter key
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\r")

        scan_type = None

        def on_scan(st, id):
            nonlocal scan_type
            scan_type = st

        scanner_filter.scan_detected.connect(on_scan)

        # Process event
        result = scanner_filter.eventFilter(scanner_filter._main_window, event)

        # Should consume the event
        assert result is True
        # Buffer should be cleared
        assert scanner_filter._buffer == ""


# ===== TESTS: TIMER FUNCTIONALITY =====

class TestTimerFunctionality:
    """Tests for timer-based buffer processing."""

    def test_timer_starts_on_key_press(self, scanner_filter, qapp):
        """Test that timer starts when key is pressed."""
        scanner_filter._buffer = ""

        event = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a")
        scanner_filter.eventFilter(scanner_filter._main_window, event)

        # Timer should be active
        assert scanner_filter._timer.isActive()

    def test_timer_resets_on_each_key(self, scanner_filter, qapp):
        """Test that timer resets on each key press."""
        scanner_filter._buffer = ""

        # First key
        event1 = QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a")
        scanner_filter.eventFilter(scanner_filter._main_window, event1)

        # Second key (should reset timer)
        event2 = QKeyEvent(QEvent.KeyPress, Qt.Key_B, Qt.NoModifier, "b")
        scanner_filter.eventFilter(scanner_filter._main_window, event2)

        # Timer should still be active
        assert scanner_filter._timer.isActive()


# ===== TESTS: SIGNAL EMISSION =====

class TestSignalEmission:
    """Tests for scan_detected signal emission."""

    def test_signal_emits_for_item_scan(self, scanner_filter, qapp, qtbot):
        """Test that signal emits correctly for item scan."""
        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps({
                "item_inv": "INV001",
                "book_id": 1,
                "isbn": "978-5-699-12345-2"
            })
            scanner_filter._process_buffer()

        assert blocker.args == ["item", "INV001"]

    def test_signal_emits_for_book_scan(self, scanner_filter, qapp, qtbot):
        """Test that signal emits correctly for book scan."""
        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps({
                "isbn": "978-5-699-12345-2",
                "doi": "",
                "biblio": "Test"
            })
            scanner_filter._process_buffer()

        assert blocker.args == ["book", "978-5-699-12345-2"]

    def test_no_signal_for_invalid_data(self, scanner_filter, qapp, qtbot):
        """Test that no signal emits for invalid data."""
        scanner_filter._buffer = "invalid data"

        # Should not emit signal
        with qtbot.assertNotEmitted(scanner_filter.scan_detected):
            scanner_filter._process_buffer()


# ===== TESTS: EDGE CASES =====

class TestBarcodeEventFilterEdgeCases:
    """Tests for edge cases in barcode event filter."""

    def test_empty_buffer_processing(self, scanner_filter, qapp):
        """Test processing empty buffer."""
        scanner_filter._buffer = ""

        # Should not raise exception
        scanner_filter._process_buffer()

        assert scanner_filter._buffer == ""

    def test_whitespace_only_buffer(self, scanner_filter, qapp):
        """Test processing buffer with only whitespace."""
        scanner_filter._buffer = "   \t\n  "

        scanner_filter._process_buffer()

        assert scanner_filter._buffer == ""

    def test_very_long_buffer(self, scanner_filter, qapp):
        """Test processing very long buffer."""
        long_data = "A" * 10000
        scanner_filter._buffer = long_data

        # Should handle gracefully
        scanner_filter._process_buffer()

        assert scanner_filter._buffer == ""

    def test_nested_json_structure(self, scanner_filter, qapp, qtbot):
        """Test processing nested JSON structure."""
        nested_data = {
            "item_inv": "INV001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2",
            "metadata": {
                "location": "Shelf A1",
                "status": "available"
            }
        }

        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps(nested_data)
            scanner_filter._process_buffer()

        assert blocker.args[0] == "item"

    def test_unicode_in_json(self, scanner_filter, qapp, qtbot):
        """Test processing JSON with Unicode characters."""
        unicode_data = {
            "item_inv": "ИНВ001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2"
        }

        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps(unicode_data, ensure_ascii=False)
            scanner_filter._process_buffer()

        assert blocker.args == ["item", "ИНВ001"]

    def test_special_characters_in_inventory_number(self, scanner_filter, qapp, qtbot):
        """Test processing inventory number with special characters."""
        data = {
            "item_inv": "INV-2024-001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2"
        }

        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps(data)
            scanner_filter._process_buffer()

        assert blocker.args == ["item", "INV-2024-001"]


# ===== TESTS: INTEGRATION =====

class TestBarcodeEventFilterIntegration:
    """Integration tests for barcode event filter."""

    def test_full_scan_simulation_item(self, scanner_filter, qapp, qtbot):
        """Test full scan simulation for item."""
        # Simulate scanner typing JSON and pressing Enter
        json_data = json.dumps({
            "item_inv": "INV001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2"
        })

        scanner_filter._buffer = ""

        # Type each character
        for char in json_data:
            if char == '{':
                key = Qt.Key_BraceLeft
            elif char == '}':
                key = Qt.Key_BraceRight
            elif char == '"':
                key = Qt.Key_QuoteDbl
            elif char == ':':
                key = Qt.Key_Colon
            elif char == ',':
                key = Qt.Key_Comma
            else:
                key = ord(char.upper()) if char.isalpha() else ord(char)

            event = QKeyEvent(QEvent.KeyPress, key, Qt.NoModifier, char)
            scanner_filter.eventFilter(scanner_filter._main_window, event)

        # Press Enter
        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            enter_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\r")
            scanner_filter.eventFilter(scanner_filter._main_window, enter_event)

        assert blocker.args[0] == "item"

    def test_multiple_scans_in_sequence(self, scanner_filter, qapp, qtbot):
        """Test multiple scans in sequence."""
        scans = [
            {"item_inv": "INV001", "book_id": 1, "isbn": "978-5-699-12345-2"},
            {"item_inv": "INV002", "book_id": 1, "isbn": "978-5-699-12345-2"},
            {"isbn": "978-5-699-12345-2", "doi": "", "biblio": "Test"}
        ]

        results = []

        def on_scan(scan_type, identifier):
            results.append((scan_type, identifier))

        scanner_filter.scan_detected.connect(on_scan)

        for scan_data in scans:
            scanner_filter._buffer = json.dumps(scan_data)
            scanner_filter._process_buffer()

        assert len(results) == 3
        assert results[0] == ("item", "INV001")
        assert results[1] == ("item", "INV002")
        assert results[2] == ("book", "978-5-699-12345-2")


# ===== TESTS: ERROR RECOVERY =====

class TestErrorRecovery:
    """Tests for error recovery in barcode event filter."""

    def test_recovery_after_invalid_json(self, scanner_filter, qapp, qtbot):
        """Test that filter recovers after invalid JSON."""
        # First, invalid JSON
        scanner_filter._buffer = "invalid json"
        scanner_filter._process_buffer()

        # Then, valid JSON
        with qtbot.waitSignal(scanner_filter.scan_detected, timeout=1000) as blocker:
            scanner_filter._buffer = json.dumps({
                "item_inv": "INV001",
                "book_id": 1,
                "isbn": "978-5-699-12345-2"
            })
            scanner_filter._process_buffer()

        assert blocker.args[0] == "item"

    def test_recovery_after_exception(self, scanner_filter, qapp):
        """Test that filter recovers after exception."""
        # Simulate exception during processing
        scanner_filter._buffer = "test"

        try:
            scanner_filter._process_buffer()
        except Exception:
            pass

        # Should be able to process next scan
        scanner_filter._buffer = json.dumps({
            "item_inv": "INV001",
            "book_id": 1,
            "isbn": "978-5-699-12345-2"
        })

        # Should not raise exception
        scanner_filter._process_buffer()

        assert scanner_filter._buffer == ""

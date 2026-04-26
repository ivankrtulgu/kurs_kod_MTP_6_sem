"""
Scanner filter module.

Implements a global event filter to intercept fast keyboard input from QR/Barcode scanners
simulating keyboard entry, and dispatches it to the MainWindow.
"""

import json
import logging
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QKeyEvent

logger = logging.getLogger("ScannerFilter")

class BarcodeEventFilter(QObject):
    """
    Global event filter that buffers fast keyboard input.
    If the input is recognized as a JSON string containing item or book identifiers,
    it triggers the corresponding action in the main window.
    """
    
    # Signal to notify MainWindow about recognized scans
    # (type, identifier)
    scan_detected = pyqtSignal(str, str)

    def __init__(self, main_window):
        super().__init__()
        self._main_window = main_window
        self._buffer = ""
        
        # Timer to detect end of fast input burst (increased to 500ms for very long strings)
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._process_buffer)
        
        # Full Layout translation map: Russian keyboard -> Latin symbols (QWERTY)
        ru_chars = "йцукенгшщзхъфывапролджэячсмитьбю"
        en_chars = "qwertyuiop[]asdfghjkl;\"zxcvbnm,."
        
        self._layout_map = {}
        for ru, en in zip(ru_chars, en_chars):
            self._layout_map[ru] = en
            self._layout_map[ru.upper()] = en.upper()
            
        # Manual overrides for JSON critical symbols
        self._layout_map.update({
            'х': '[', 'Х': '{',
            'ъ': ']', 'Ъ': '}',
            'э': '"', 'Э': '"',
            'ж': ';', 'Ж': ':',
            'б': ',', 'Б': ',',
        })
        
        print("DEBUG: BarcodeEventFilter initialized. Timer: 500ms, Enter-key detection active.")

    def eventFilter(self, obj, event):
        """
        Intercept key press events.
        """
        if event.type() == QEvent.KeyPress:
            from PyQt5.QtWidgets import QApplication, QWidget
            from PyQt5.QtCore import Qt
            
            focus_widget = QApplication.focusWidget()
            if focus_widget is not None and obj != focus_widget:
                return False
                
            if not isinstance(obj, QWidget):
                return False

            key_event = event # type: QKeyEvent
            key_code = key_event.key()
            text = key_event.text()
            
            # 1. Immediate processing on Enter key (Standard for most scanners)
            if key_code in (Qt.Key_Return, Qt.Key_Enter):
                print("DEBUG SCANNER: Enter key detected! Processing buffer immediately...")
                self._process_buffer()
                return True # Consume event so it doesn't trigger a newline in UI
            
            # 2. Character accumulation
            if text and text.strip() != "":
                # Translate Russian layout to Latin if necessary
                char = self._layout_map.get(text, text)
                self._buffer += char
                
                print(f"DEBUG SCANNER: Intercepted char: '{char}' | Buffer: '{self._buffer}'")
                
                # Reset timer on every key press
                self._timer.start(500)
        
        return super().eventFilter(obj, event)


    def _process_buffer(self):
        """
        Analyze the buffered text and dispatch to MainWindow.
        """
        if not self._buffer:
            return

        print(f"DEBUG SCANNER: Timer expired. Processing buffer: '{self._buffer}'")
        
        try:
            # Attempt to parse as JSON
            data = json.loads(self._buffer)
            print(f"DEBUG SCANNER: JSON parsed successfully: {data}")
            
            if isinstance(data, dict):
                # Scenario A: Physical Item
                if "item_inv" in data:
                    inv_num = str(data["item_inv"])
                    print(f"DEBUG SCANNER: Scan detected: Item {inv_num}")
                    self.scan_detected.emit("item", inv_num)
                    from PyQt5.QtWidgets import QApplication
                    QApplication.beep()
                    
                # Scenario B: Book (Edition)
                elif "isbn" in data:
                    isbn = str(data["isbn"])
                    print(f"DEBUG SCANNER: Scan detected: Book ISBN {isbn}")
                    self.scan_detected.emit("book", isbn)
                    from PyQt5.QtWidgets import QApplication
                    QApplication.beep()
                else:
                    print("DEBUG SCANNER: JSON valid but no recognized keys (item_inv/isbn)")
            else:
                print("DEBUG SCANNER: Parsed JSON is not a dictionary")
                
        except json.JSONDecodeError as e:
            print(f"DEBUG SCANNER: Buffer is not valid JSON: {e}")
        except Exception as e:
            print(f"DEBUG SCANNER: Unexpected error during buffer processing: {e}")
        finally:
            # Always clear buffer after timer expires
            self._buffer = ""
            print("DEBUG SCANNER: Buffer cleared.")


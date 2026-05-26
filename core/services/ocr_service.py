"""
OCR service module.

Encapsulates Tesseract OCR logic — path discovery, language configuration,
and text recognition. Pure business logic without UI dependencies.

Usage:
    >>> service = OcrService()
    >>> text = service.recognize_from_pil(pil_image, lang='rus+eng')
    >>> print(text)
"""

import os
import shutil
from typing import Optional

from PIL import Image

import pytesseract
from config.settings import settings


class OcrService:
    """
    Service for text recognition via Tesseract OCR.
    
    Handles:
    - Tesseract executable discovery (settings → $PATH → common paths)
    - Language/profile configuration (rus, eng, rus+eng, digits)
    - Calling pytesseract with proper config
    
    Pure Python — no PyQt/Qt dependencies.
    """

    def __init__(self, tesseract_path: str = "") -> None:
        """
        Initialize OCR service.

        Args:
            tesseract_path: Optional explicit path to tesseract executable.
                           If empty, auto-discovery is used.
        """
        self._tesseract_path = self._resolve_tesseract_path(tesseract_path)
        if self._tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_path

    @staticmethod
    def _resolve_tesseract_path(path: str) -> Optional[str]:
        """
        Find the Tesseract executable.

        Priority:
        1. Explicit path argument
        2. settings.TESSERACT_PATH (from .env)
        3. shutil.which('tesseract') — system $PATH
        4. Common installation paths

        Args:
            path: Explicit path hint.

        Returns:
            str | None: Absolute path to tesseract executable, or None.
        """
        # 1. Explicit path
        if path and os.path.exists(path):
            return path

        # 2. From .env config
        env_path = settings.TESSERACT_PATH.strip() if hasattr(settings, 'TESSERACT_PATH') else ""
        if env_path and os.path.exists(env_path):
            return env_path

        # 3. System $PATH
        detected = shutil.which("tesseract")
        if detected:
            return detected

        # 4. Common fallback paths
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"D:\Main_programms\Tesseract\Tesseract-OCR\tesseract.exe",
            r"/usr/bin/tesseract",
            r"/usr/local/bin/tesseract",
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p

        return None

    @property
    def is_available(self) -> bool:
        """Check if Tesseract was found and configured."""
        return self._tesseract_path is not None

    @property
    def tesseract_path(self) -> Optional[str]:
        """Path to the Tesseract executable, or None."""
        return self._tesseract_path

    def recognize_from_pil(self, image: Image.Image, lang: str = 'rus+eng') -> str:
        """
        Recognize text from a PIL Image.

        Args:
            image: PIL Image object to recognize.
            lang: Language mode:
                  - 'rus' — русский
                  - 'eng' — английский
                  - 'rus+eng' — русский + английский (смешанный)
                  - 'eng+rus' — английский + русский (приоритет EN)
                  - 'digits' — только цифры и символы

        Returns:
            str: Recognized text, or error message string.
        """
        if not self._tesseract_path:
            return (
                "(Ошибка: Tesseract не установлен. "
                "Установите Tesseract-OCR с https://github.com/UB-Mannheim/tesseract/wiki)"
            )

        lang_map = {
            'rus':       ('rus',     r'--oem 3 --psm 6'),
            'eng':       ('eng',     r'--oem 3 --psm 6'),
            'rus+eng':   ('rus+eng', r'--oem 3 --psm 6'),
            'eng+rus':   ('eng+rus', r'--oem 3 --psm 6'),
            'digits':    ('eng',     r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.,-:;()/'),
        }
        # Default fallback
        ocr_lang, config = lang_map.get(lang, ('rus+eng', r'--oem 3 --psm 6'))

        try:
            text = pytesseract.image_to_string(image, lang=ocr_lang, config=config)
            return text.strip()
        except Exception as e:
            print(f" OCR ошибка: {e}")
            return f"(OCR ошибка: {str(e)})"

    def recognize_from_bytes(self, image_bytes: bytes, lang: str = 'rus+eng') -> str:
        """
        Recognize text from raw image bytes.

        Convenience wrapper — converts bytes to PIL Image, then delegates
        to recognize_from_pil().

        Args:
            image_bytes: Raw image file bytes (PNG, JPEG, etc.).
            lang: Language mode (see recognize_from_pil).

        Returns:
            str: Recognized text.
        """
        import io
        image = Image.open(io.BytesIO(image_bytes))
        return self.recognize_from_pil(image, lang)

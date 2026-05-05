import qrcode
import json
import secrets
import string
from pathlib import Path
from typing import Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class QRService:
    """
    Service for generating QR codes for Books and BookItems.
    """

    @staticmethod
    def generate_book_qr(book) -> Optional[str]:
        """
        Generates a QR code for a Book bibliographic record.
        
        Args:
            book: Book object containing bibliographic data.
            
        Returns:
            Optional[str]: Path to the generated QR code image, or None if failed.
        """
        try:
            settings.ensure_dirs()
            
            qr_dict = {
                "isbn": book.isbn,
                "doi": book.doi,
                "biblio": book.format_bibliographic_record()
            }
            qr_data = json.dumps(qr_dict, ensure_ascii=False)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            qr_dir = settings.RESOURCES_PATH / "qr_codes"
            qr_dir.mkdir(parents=True, exist_ok=True)
            
            random_salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            filename = f"qr_{book.id}_{book.isbn}_{random_salt}.png"
            qr_path = qr_dir / filename
            img.save(qr_path)
            
            return str(qr_path)
            
        except Exception as e:
            logger.exception(f"Failed to generate Book QR: {e}")
            return None

    @staticmethod
    def generate_item_qr(item, book_isbn: str) -> Optional[str]:
        """
        Generates a QR code for a specific physical BookItem.
        
        Args:
            item: BookItem object.
            book_isbn: ISBN of the associated book.
            
        Returns:
            Optional[str]: Path to the generated QR code image, or None if failed.
        """
        try:
            settings.ensure_dirs()
            
            qr_dict = {
                "item_inv": item.inventory_number,
                "book_id": item.book_id,
                "isbn": book_isbn
            }
            qr_data = json.dumps(qr_dict, ensure_ascii=False)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            qr_dir = settings.RESOURCES_PATH / "qr_codes" / "items"
            qr_dir.mkdir(parents=True, exist_ok=True)
            
            random_salt = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            filename = f"qr_item_{item.inventory_number}_{book_isbn}_{random_salt}.png"
            qr_path = qr_dir / filename
            img.save(qr_path)
            
            return str(qr_path)
            
        except Exception as e:
            logger.exception(f"Failed to generate Item QR: {e}")
            return None

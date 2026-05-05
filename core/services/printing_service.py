from fpdf import FPDF
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class PrintingService:
    """
    Service for generating printable documents for library assets.
    """

    @staticmethod
    def generate_qr_pdf(
        item_qr_path: str, 
        item_label: str, 
        book_qr_path: Optional[str] = None, 
        book_label: Optional[str] = None, 
        output_path: str = "",
        cols: int = 3
    ) -> bool:
        """
        Generates a PDF containing QR codes in a tabular grid layout.
        Optimizes layout (horizontal vs vertical) to maximize QR size and minimize empty space.
        """
        try:
            pdf = FPDF(unit="mm", format="A4")
            pdf.add_page()
            
            font_path = r"C:\Windows\Fonts\arial.ttf"
            if os.path.exists(font_path):
                pdf.add_font("DejaVu", "", font_path, uni=True)
                pdf.set_font("DejaVu", size=10)
            else:
                pdf.set_font("Arial", size=10)
            
            page_width = 210
            margin = 10
            usable_width = page_width - (2 * margin)
            
            cell_width = usable_width / cols
            padding = 2
            label_h = 5
            
            has_item = os.path.exists(item_qr_path) if item_qr_path else False
            has_book = os.path.exists(book_qr_path) if book_qr_path else False
            
            if not has_item:
                logger.error(f"Item QR image not found at {item_qr_path}")
                return False

            is_pair = has_book
            
            qr_size = min(cell_width - 2 * padding, 30)
            if is_pair:
                cell_height = (qr_size + label_h) * 2 + 3 * padding
            else:
                cell_height = qr_size + label_h + 2 * padding
            
            current_col = 0
            current_row = 0
            
            x = margin + (current_col * cell_width)
            y = margin + (current_row * cell_height)
            pdf.rect(x, y, cell_width, cell_height)
            
            dynamic_font_size = max(6, min(12, int(cell_width * 0.2)))
            pdf.set_font("DejaVu" if os.path.exists(font_path) else "Arial", size=dynamic_font_size)
            
            qr_x = x + (cell_width - qr_size) / 2
            qr_y = y + padding
            pdf.image(item_qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
            
            pdf.set_xy(x, qr_y + qr_size + 1)
            pdf.cell(cell_width, label_h, txt=item_label, ln=True, align='C')
            
            if is_pair:
                book_qr_x = qr_x
                book_qr_y = qr_y + qr_size + label_h + padding
                pdf.image(book_qr_path, x=book_qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                pdf.set_xy(x, book_qr_y + qr_size + 1)
                pdf.cell(cell_width, label_h, txt=book_label or "Произведение", ln=True, align='C')
            
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False

    @staticmethod
    def generate_batch_qr_pdf(
        items_data: list[dict], 
        book_qr_path: Optional[str] = None, 
        book_label: Optional[str] = None, 
        output_path: str = "", 
        cols: int = 3,
        mode: str = "both"
    ) -> bool:
        """
        Generates a PDF containing multiple QR codes in a tabular grid layout.
        Supports three modes:
        - 'book_only': Only the book QR code
        - 'items_only': Only item QR codes (no book QR)
        - 'both': Each item QR is paired with the book QR
        """
        try:
            pdf = FPDF(unit="mm", format="A4")
            pdf.add_page()
            
            font_path = r"C:\Windows\Fonts\arial.ttf"
            has_font = os.path.exists(font_path)
            if has_font:
                pdf.add_font("DejaVu", "", font_path, uni=True)
                pdf.set_font("DejaVu", size=10)
            else:
                pdf.set_font("Arial", size=10)
            
            page_width = 210
            margin = 10
            usable_width = page_width - (2 * margin)
            cell_width = usable_width / cols
            padding = 2
            label_h = 5
            
            is_pair = (mode == "both") and book_qr_path and os.path.exists(book_qr_path)
            
            qr_size = min(cell_width - 2 * padding, 30)
            if is_pair:
                cell_height = (qr_size + label_h) * 2 + 3 * padding
            else:
                cell_height = qr_size + label_h + 2 * padding
            
            dynamic_font_size = max(6, min(12, int(cell_width * 0.2)))
            font_name = "DejaVu" if has_font else "Arial"
            
            current_col = 0
            current_row = 0
            
            def draw_cell(pdf, x, y, cell_width, cell_height, qr_path, label, qr_size, padding, label_h, font_name, dynamic_font_size):
                pdf.rect(x, y, cell_width, cell_height)
                qr_x = x + (cell_width - qr_size) / 2
                qr_y = y + padding
                pdf.image(qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
                pdf.set_font(font_name, size=dynamic_font_size)
                pdf.set_xy(x, qr_y + qr_size + 1)
                pdf.cell(cell_width, label_h, txt=label, ln=True, align='C')
                return qr_x, qr_y

            if mode == "book_only":
                if book_qr_path and os.path.exists(book_qr_path):
                    x = margin
                    y = margin
                    pdf.rect(x, y, cell_width, cell_height)
                    pdf.image(book_qr_path, x=x + (cell_width - qr_size)/2, y=y + padding, w=qr_size, h=qr_size)
                    pdf.set_font(font_name, size=dynamic_font_size)
                    pdf.set_xy(x, y + padding + qr_size + 1)
                    pdf.cell(cell_width, label_h, txt=book_label or "Произведение", ln=True, align='C')
            else:
                for item in items_data:
                    x = margin + (current_col * cell_width)
                    y = margin + (current_row * cell_height)
                    
                    if not os.path.exists(item['qr_path']):
                        logger.warning(f"QR image not found: {item['qr_path']}")
                        continue
                        
                    qr_x, qr_y = draw_cell(pdf, x, y, cell_width, cell_height, item['qr_path'], item['label'], qr_size, padding, label_h, font_name, dynamic_font_size)
                    
                    if is_pair:
                        book_qr_x = qr_x
                        book_qr_y = qr_y + qr_size + label_h + padding
                        pdf.image(book_qr_path, x=book_qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                        pdf.set_font(font_name, size=dynamic_font_size)
                        pdf.set_xy(x, book_qr_y + qr_size + 1)
                        pdf.cell(cell_width, label_h, txt=book_label or "Произведение", ln=True, align='C')
                    
                    current_col += 1
                    if current_col >= cols:
                        current_col = 0
                        current_row += 1
            
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate batch QR PDF: {e}")
            return False

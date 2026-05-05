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
            padding = 2 # Reduced padding to minimize empty space
            label_h = 5
            
            has_item = os.path.exists(item_qr_path) if item_qr_path else False
            has_book = os.path.exists(book_qr_path) if book_qr_path else False
            
            if not has_item:
                logger.error(f"Item QR image not found at {item_qr_path}")
                return False

            is_pair = has_book
            
            # 1. Determine Layout and QR Size
            # We want the QR to be as large as possible, up to 30mm
            if is_pair:
                # Check if we can fit two QRs side-by-side (horizontal)
                # We can go horizontal if the cell is wide enough to hold two QRs and labels comfortably
                # Min width for horizontal = 2 * (min_qr_size + padding)
                if cell_width >= 60: # Threshold for horizontal layout
                    layout = "horizontal"
                    qr_size = min((cell_width - 3 * padding) / 2, 30)
                    cell_height = qr_size + label_h + 2 * padding
                else:
                    layout = "vertical"
                    qr_size = min(cell_width - 2 * padding, 30)
                    cell_height = (qr_size + label_h) * 2 + 3 * padding
            else:
                layout = "vertical"
                qr_size = min(cell_width - 2 * padding, 30)
                cell_height = qr_size + label_h + 2 * padding
            
            current_col = 0
            current_row = 0
            
            # Draw the cell
            x = margin + (current_col * cell_width)
            y = margin + (current_row * cell_height)
            pdf.rect(x, y, cell_width, cell_height)
            
            # Common font size
            dynamic_font_size = max(6, min(12, int(cell_width * 0.2)))
            pdf.set_font("DejaVu" if os.path.exists(font_path) else "Arial", size=dynamic_font_size)
            
            # 2. Render Item QR
            qr_x = x + (cell_width - qr_size) / 2 if layout == "vertical" else x + padding
            qr_y = y + padding
            pdf.image(item_qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
            
            # Item Label
            pdf.set_xy(x, qr_y + qr_size + 1)
            pdf.cell(cell_width, label_h, txt=item_label, ln=True, align='C')
            
            # 3. Render Book QR if paired
            if is_pair:
                if layout == "horizontal":
                    # Place Book QR to the right of Item QR
                    book_qr_x = qr_x + qr_size + padding
                    book_qr_y = qr_y
                    pdf.image(book_qr_path, x=book_qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                    
                    # Book Label
                    pdf.set_xy(book_qr_x, book_qr_y + qr_size + 1)
                    pdf.cell(qr_size + 2 * padding, label_h, txt=book_label or "Произведение", ln=True, align='C')
                else:
                    # Place Book QR below Item label
                    book_qr_x = qr_x
                    book_qr_y = qr_y + qr_size + label_h + padding
                    pdf.image(book_qr_path, x=book_qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                    
                    # Book Label
                    pdf.set_xy(x, book_qr_y + qr_size + 1)
                    pdf.cell(cell_width, label_h, txt=book_label or "Произведение", ln=True, align='C')
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False

            # Determine if we are printing a pair or a single item
            is_pair = has_book
            
            # Calculate proportional QR size first to determine cell height
            # QR should be square and fit in cell width
            qr_size = min(cell_width - (2 * padding), 30)
            label_h = 6
            
            # Calculate cell height based on content
            if is_pair:
                # Two QRs + Two Labels + Padding
                cell_height = (qr_size + label_h) * 2 + (padding * 3)
            else:
                # One QR + One Label + Padding
                cell_height = qr_size + label_h + (padding * 2)
            
            # We only have one logical unit to print in this specific call
            # (one item and optionally its book)
            current_col = 0
            current_row = 0
            
            # Draw the cell
            x = margin + (current_col * cell_width)
            y = margin + (current_row * cell_height)
            pdf.rect(x, y, cell_width, cell_height)
            
            # 1. Render Item QR
            qr_x = x + (cell_width - qr_size) / 2
            qr_y = y + padding
            pdf.image(item_qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
            
            # Item Label
            pdf.set_xy(x, qr_y + qr_size + 1)
            # Dynamic font size for label
            dynamic_font_size = max(6, min(12, int(cell_width * 0.2)))
            pdf.set_font("DejaVu" if os.path.exists(font_path) else "Arial", size=dynamic_font_size)
            pdf.cell(cell_width, label_h, txt=item_label, ln=True, align='C')
            
            # 2. Render Book QR if paired
            if is_pair:
                # Position Book QR below Item label
                book_qr_y = qr_y + qr_size + label_h + padding
                pdf.image(book_qr_path, x=qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                
                # Book Label
                pdf.set_xy(x, book_qr_y + qr_size + 1)
                pdf.cell(cell_width, label_h, txt=book_label or "Произведение", ln=True, align='C')
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False
                
            if book_qr_path and os.path.exists(book_qr_path):
                items_to_print.append((book_qr_path, book_label or "Произведение"))
            
            current_col = 0
            current_row = 0
            
            for qr_path, label in items_to_print:
                # Calculate cell position
                x = margin + (current_col * cell_width)
                y = margin + (current_row * cell_height)
                
                # Draw cell border
                pdf.rect(x, y, cell_width, cell_height)
                
                # Calculate dynamic font size based on cell width (shared for all labels in cell)
                dynamic_font_size = max(6, min(12, int(cell_width * 0.2)))
                font_name = "DejaVu" if os.path.exists(font_path) else "Arial"
                
                # Calculate proportional QR size
                qr_size = min(cell_width - (2 * padding), 30)
                
                # Center QR in cell
                qr_x = x + (cell_width - qr_size) / 2
                qr_y = y + padding
                
                pdf.image(qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)
                
                # Item Label - Set font explicitly before printing
                pdf.set_font(font_name, size=dynamic_font_size)
                pdf.set_xy(x, qr_y + qr_size + 1)
                pdf.cell(cell_width, label_h, txt=label, ln=True, align='C')
                
                # 2. Render Book QR if paired
                if is_pair:
                    # Position Book QR below Item label
                    book_qr_y = qr_y + qr_size + label_h + padding
                    pdf.image(book_qr_path, x=qr_x, y=book_qr_y, w=qr_size, h=qr_size)
                    
                    # Book Label - Set font explicitly before printing
                    pdf.set_font(font_name, size=dynamic_font_size)
                    pdf.set_xy(x, book_qr_y + qr_size + 1)
                    pdf.cell(cell_width, label_h, txt=book_label, ln=True, align='C')
                
                # Advance grid
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
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False
                
            # 2. Book QR (Optional)
            if book_qr_path and os.path.exists(book_qr_path):
                pdf.image(book_qr_path, x=margin_x, y=current_y, w=qr_size, h=qr_size)
                pdf.set_xy(margin_x, current_y + qr_size + 2)
                pdf.cell(0, 10, txt=book_label or "Произведение", ln=True, align='C')
            elif book_qr_path:
                logger.error(f"Book QR image not found at {book_qr_path}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False
                
            # 2. Book QR (Optional)
            if book_qr_path and os.path.exists(book_qr_path):
                pdf.image(book_qr_path, x=margin_x, y=current_y, w=qr_size, h=qr_size)
                pdf.set_xy(margin_x, current_y + qr_size + 2)
                pdf.cell(0, 10, txt=book_label or "Произведение", ln=True, align='C')
            elif book_qr_path:
                logger.error(f"Book QR image not found at {book_qr_path}")
                # We continue as the item QR is the priority
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate QR PDF: {e}")
            return False

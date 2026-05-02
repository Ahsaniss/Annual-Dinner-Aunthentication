import qrcode
import uuid
import os
import io

def generate_uuid():
    """Generates a unique Short ID."""
    return str(uuid.uuid4())

from PIL import Image, ImageDraw, ImageFont

def generate_qr_code(data, output_path=None, name=None, student_id=None, section=None):
    """
    Generates a QR code for the given data.
    If name, student_id, or section are provided, adds them as text below the QR code.
    If output_path is provided, saves to file.
    Returns the image object.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_width, qr_height = qr_img.size
    
    padding = 10
    line_height = 25
    small_line_height = 15
    
    lines_count = sum(1 for item in [name, student_id, section] if item)
    extra_height = padding + (lines_count * line_height) + small_line_height + padding
    
    combined_img = Image.new('RGB', (qr_width, qr_height + extra_height), color='white')
    combined_img.paste(qr_img, (0, 0))
    
    draw = ImageDraw.Draw(combined_img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font
        font_small = font
        
    y_offset = qr_height + (padding // 2)
    
    if name:
        draw.text((qr_width // 2, y_offset), f"Name: {name}", fill="black", font=font_bold, anchor="mt")
        y_offset += line_height
        
    if student_id:
        draw.text((qr_width // 2, y_offset), f"ID: {student_id}", fill="black", font=font, anchor="mt")
        y_offset += line_height

    if section:
        draw.text((qr_width // 2, y_offset), f"Section: {section}", fill="black", font=font, anchor="mt")
        y_offset += line_height
        
    y_offset += (padding // 2)
    draw.text((qr_width // 2, y_offset), "Developed by: Ahsan", fill="#666666", font=font_small, anchor="mt")
    
    img = combined_img
    
    if output_path:
        # Standardize path
        output_path = os.path.abspath(output_path)
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
    
    return img

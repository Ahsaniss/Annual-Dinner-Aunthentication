import qrcode
import uuid
import os
import io

def generate_uuid():
    """Generates a unique Short ID."""
    return str(uuid.uuid4())

from PIL import Image, ImageDraw, ImageFont


def _load_font(size, bold=False):
    font_candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered_text(draw, center_x, y, text, font, fill, anchor="ma"):
    draw.text((center_x, y), text, font=font, fill=fill, anchor=anchor)


def _draw_wrapped_centered_text(draw, center_x, start_y, text, font, fill, max_width, line_spacing=10):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        trial_line = " ".join(current_line + [word])
        line_width, _ = _text_size(draw, trial_line, font)
        if current_line and line_width > max_width:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    y = start_y
    line_height = _text_size(draw, "Ag", font)[1]
    for line in lines:
        _draw_centered_text(draw, center_x, y, line, font, fill)
        y += line_height + line_spacing

    return y


def _draw_key_value_row(draw, center_x, y, label, value, label_font, value_font, label_fill, value_fill, gap=18):
    label_width, _ = _text_size(draw, label, label_font)
    value_width, _ = _text_size(draw, value, value_font)
    total_width = label_width + gap + value_width
    start_x = center_x - (total_width // 2)
    draw.text((start_x, y), label, fill=label_fill, font=label_font, anchor="la")
    draw.text((start_x + label_width + gap, y), value, fill=value_fill, font=value_font, anchor="la")

def generate_qr_code(data, output_path=None, name=None, student_id=None, section=None):
    """
    Generates a decorative QR card for the given data.
    If name, student_id, or section are provided, adds them to the card.
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

    width, height = 1240, 1754
    background = (0, 0, 0)
    accent = (232, 182, 90)
    soft_white = (250, 247, 240)

    img = Image.new('RGB', (width, height), color=background)
    draw = ImageDraw.Draw(img)

    title_font = _load_font(56, bold=False)
    heading_font = _load_font(48, bold=False)
    body_font = _load_font(34, bold=False)
    body_bold_font = _load_font(38, bold=True)
    small_font = _load_font(30, bold=False)
    footer_font = _load_font(28, bold=False)

    def draw_line(y_pos, x_margin=0):
        draw.line((x_margin, y_pos, width - x_margin, y_pos), fill=accent, width=3)

    def draw_star(cx, cy, size=15):
        points = [
            (cx, cy - size),
            (cx + size, cy),
            (cx, cy + size),
            (cx - size, cy),
        ]
        draw.polygon(points, fill=accent)

    top_rule_y = 130
    bottom_rule_y = height - 105

    draw_line(top_rule_y)
    draw_star(width // 2, top_rule_y, size=18)
    draw_line(bottom_rule_y)
    draw_star(width // 2, bottom_rule_y, size=18)

    _draw_centered_text(draw, width // 2, 185, "ANNUAL FUNCTION", title_font, accent, anchor="ma")

    qr_size = 430
    qr_img = qr_img.resize((qr_size, qr_size))
    qr_left = (width - qr_size) // 2
    qr_top = 360
    arch_padding = 24
    arch_box = (qr_left - arch_padding, qr_top - 18, qr_left + qr_size + arch_padding, qr_top + qr_size + 26)

    _draw_centered_text(draw, width // 2, 255, "DEPARTMENT OF SOFTWARE ENGINEERING", heading_font, accent, anchor="ma")

    draw.arc(arch_box, start=180, end=360, fill=accent, width=3)
    draw.line((qr_left - arch_padding, qr_top + qr_size + 26, qr_left - arch_padding, qr_top + 55), fill=accent, width=3)
    draw.line((qr_left + qr_size + arch_padding, qr_top + qr_size + 26, qr_left + qr_size + arch_padding, qr_top + 55), fill=accent, width=3)
    draw.line((qr_left - arch_padding, qr_top + qr_size + 26, qr_left + qr_size + arch_padding, qr_top + qr_size + 26), fill=accent, width=3)

    inner_margin = 10
    draw.rounded_rectangle(
        (qr_left + inner_margin, qr_top + inner_margin, qr_left + qr_size - inner_margin, qr_top + qr_size - inner_margin),
        radius=20,
        outline=accent,
        width=2,
    )
    img.paste(qr_img, (qr_left, qr_top))

    info_y = 1065
    info_gap = 82
    if name:
        _draw_key_value_row(draw, width // 2, info_y, "NAME:", str(name), body_font, body_bold_font, soft_white, soft_white)
    if student_id:
        _draw_key_value_row(draw, width // 2, info_y + info_gap, "ID:", str(student_id), body_font, body_bold_font, soft_white, soft_white)
    if section:
        _draw_key_value_row(draw, width // 2, info_y + info_gap * 2, "SECTION:", str(section), body_font, body_bold_font, soft_white, soft_white)

    message = (
        "The Department of Software Engineering warmly welcomes you to the Annual Function 2022-2026. "
        "Join us as we celebrate achievements, memories, talent, and the journey of growth shared by our students. "
        "Your presence will make this occasion even more special."
    )
    _draw_wrapped_centered_text(draw, width // 2, 1405, message, small_font, soft_white, max_width=900, line_spacing=12)

    _draw_centered_text(draw, width // 2, 1680, "DEVELOPED BY: AHSAN RAZA", footer_font, accent, anchor="ma")
    
    if output_path:
        # Standardize path
        output_path = os.path.abspath(output_path)
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
    
    return img

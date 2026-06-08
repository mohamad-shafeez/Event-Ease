"""
EventEase — QR Ticket Generator
"""
import os
import json
import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import current_app

def generate_qr(ticket_code, event_title, user_name, event_date_str):
    """
    Generate QR with embedded JSON, append text below, and save as PNG.
    """
    payload = json.dumps({
        "code": ticket_code,
        "event": event_title,
        "user": user_name,
        "date": event_date_str
    })

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_w, qr_h = img_qr.size
    
    # Create canvas with extra space at the bottom for text
    text_height = 80
    canvas_w = qr_w
    canvas_h = qr_h + text_height
    
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    canvas.paste(img_qr, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    
    try:
        # Try to use a default sans-serif font
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Center text
    # Pillow < 10 uses textsize, >=10 uses textbbox. Try fallback approach:
    def get_text_x(text, font, img_w):
        try:
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w, h = draw.textsize(text, font=font)
        return (img_w - w) / 2

    x_code = get_text_x(ticket_code, font_large, canvas_w)
    draw.text((x_code, qr_h + 10), ticket_code, fill="black", font=font_large)
    
    x_title = get_text_x(event_title, font_small, canvas_w)
    draw.text((x_title, qr_h + 40), event_title[:40], fill="dimgray", font=font_small)

    folder = os.path.join(current_app.static_folder, 'qr_tickets')
    os.makedirs(folder, exist_ok=True)
    
    filename = f"{ticket_code}.png"
    filepath = os.path.join(folder, filename)
    canvas.save(filepath, "PNG")
    
    return f"qr_tickets/{filename}"

def verify_qr(ticket_code):
    from models.ticket_model import get_ticket_detail
    ticket = get_ticket_detail(ticket_code)
    if not ticket:
        return {'valid': False, 'message': 'Ticket not found'}
    if ticket['status'] == 'cancelled':
        return {'valid': False, 'message': 'Ticket has been cancelled'}
    if ticket['status'] == 'used':
        return {'valid': False, 'message': 'Ticket already scanned'}
    return {'valid': True, 'ticket': ticket}

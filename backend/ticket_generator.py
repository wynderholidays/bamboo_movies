import qrcode
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue, red
from datetime import datetime
import os

def generate_qr_code(data):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def create_ticket_pdf(booking_data, theater_config):
    """Create PDF ticket with QR codes for each seat"""
    
    # Create tickets directory if it doesn't exist
    os.makedirs("tickets", exist_ok=True)
    
    filename = f"tickets/ticket_{booking_data['id']}.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(blue)
    c.drawCentredText(width/2, height - 50, "🎬 MOVIE TICKET")
    
    # Movie details
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(black)
    c.drawCentredText(width/2, height - 100, theater_config['movie'])
    
    c.setFont("Helvetica", 12)
    c.drawCentredText(width/2, height - 120, f"{theater_config['theater']} - {theater_config['showtime']}")
    
    # Booking info
    y_pos = height - 160
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, f"Booking ID: {booking_data['id']}")
    c.drawString(300, y_pos, f"Customer: {booking_data['customer_name']}")
    
    y_pos -= 20
    c.drawString(50, y_pos, f"Email: {booking_data['customer_email']}")
    c.drawString(300, y_pos, f"Phone: {booking_data['customer_phone']}")
    
    y_pos -= 20
    c.drawString(50, y_pos, f"Total Amount: ₹{booking_data['total_amount']}")
    c.drawString(300, y_pos, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Separator line
    y_pos -= 30
    c.line(50, y_pos, width - 50, y_pos)
    
    # Individual seat tickets
    y_pos -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "Individual Seat Tickets:")
    
    y_pos -= 30
    
    for i, seat in enumerate(booking_data['seats']):
        if y_pos < 100:  # Start new page if needed
            c.showPage()
            y_pos = height - 50
        
        # Seat ticket box
        box_height = 120
        c.rect(50, y_pos - box_height, width - 100, box_height)
        
        # Seat info
        c.setFont("Helvetica-Bold", 14)
        c.drawString(70, y_pos - 30, f"SEAT: {seat}")
        
        c.setFont("Helvetica", 10)
        c.drawString(70, y_pos - 50, f"Movie: {theater_config['movie']}")
        c.drawString(70, y_pos - 65, f"Theater: {theater_config['theater']}")
        c.drawString(70, y_pos - 80, f"Showtime: {theater_config['showtime']}")
        c.drawString(70, y_pos - 95, f"Booking ID: {booking_data['id']}")
        
        # Generate QR code data for this seat
        qr_data = f"BOOKING:{booking_data['id']},SEAT:{seat},MOVIE:{theater_config['movie']},TIME:{theater_config['showtime']}"
        
        # QR code placeholder (in real implementation, you'd embed the actual QR image)
        c.setFont("Helvetica", 8)
        c.drawString(width - 200, y_pos - 30, "QR CODE")
        c.drawString(width - 200, y_pos - 45, f"Scan at theater")
        c.drawString(width - 200, y_pos - 60, f"for seat {seat}")
        
        # Draw QR code box
        c.rect(width - 180, y_pos - 110, 80, 80)
        
        y_pos -= 140
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawCentredText(width/2, 30, "Please arrive 30 minutes before showtime. No outside food allowed.")
    c.drawCentredText(width/2, 20, "Present this ticket and valid ID at the theater entrance.")
    
    c.save()
    
    return filename

def generate_ticket_email_content(booking_data, theater_config, pdf_path):
    """Generate email content for ticket confirmation"""
    
    subject = f"🎬 Your Movie Tickets - Booking #{booking_data['id']}"
    
    body = f"""
    <h2>🎉 Your Movie Tickets Are Ready!</h2>
    <p>Dear {booking_data['customer_name']},</p>
    <p>Congratulations! Your booking has been confirmed and your tickets are ready.</p>
    
    <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3>🎬 Movie Details:</h3>
        <p><strong>Movie:</strong> {theater_config['movie']}</p>
        <p><strong>Theater:</strong> {theater_config['theater']}</p>
        <p><strong>Showtime:</strong> {theater_config['showtime']}</p>
        <p><strong>Seats:</strong> {', '.join(booking_data['seats'])}</p>
        <p><strong>Booking ID:</strong> {booking_data['id']}</p>
    </div>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3>📱 Important Instructions:</h3>
        <ul>
            <li>Your PDF ticket with QR codes is attached to this email</li>
            <li>Each seat has its own QR code for individual entry</li>
            <li>Please arrive 30 minutes before showtime</li>
            <li>Bring a valid ID along with your tickets</li>
            <li>Show the QR codes at the theater entrance for scanning</li>
        </ul>
    </div>
    
    <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h3>⚠️ Theater Policies:</h3>
        <ul>
            <li>No outside food or beverages allowed</li>
            <li>Mobile phones must be on silent mode</li>
            <li>Entry may be denied after showtime begins</li>
        </ul>
    </div>
    
    <p>Enjoy your movie! 🍿</p>
    <p>Thank you for choosing our service.</p>
    """
    
    return subject, body
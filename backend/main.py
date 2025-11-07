from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime, timedelta
import uuid
import random
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
from logger_config import logger
import traceback
import jwt
import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

# Load environment variables from .env file
load_dotenv()
logger.info("Starting Movie Booking API...")


app = FastAPI()

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.now()
    logger.info(f"Request: {request.method} {request.url} - Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

# Add exception handler for better error logging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception handler caught: {exc}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Try to read request body for POST requests
    try:
        if request.method == "POST":
            body = await request.body()
            logger.error(f"Request body: {body.decode('utf-8') if body else 'Empty'}")
    except:
        pass
    
    return {"error": "Internal server error", "detail": str(exc)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://movies.bambooholiday.com",
        "http://movies.bambooholiday.com",
        "http://localhost:3000"  # For development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Serve React static files (move to end of file)
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Import database operations
from database import get_db_connection
from database import (
    create_booking, get_all_bookings, get_booking_by_id, update_booking_status,
    update_booking_payment_proof, get_booked_seats, store_otp, verify_otp,
    reserve_seats, get_reserved_seats, check_seat_availability, get_analytics,
    get_admin_settings, update_admin_settings, get_all_movies, create_movie,
    get_all_theaters, create_theater, get_all_showtimes, create_showtime, get_showtime_by_id
)
# from ticket_generator import create_ticket_pdf, generate_ticket_email_content

# Admin sessions (keep in memory for simplicity)
admin_sessions = set()



# AWS configuration
AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-3')
SES_FROM_EMAIL = os.getenv('SES_FROM_EMAIL', 'noreply@yourdomain.com')
S3_BUCKET = os.getenv('S3_BUCKET', 'bamboo-movies')

# Initialize AWS clients
try:
    # SES is always in us-east-1
    ses_client = boto3.client(
        'ses',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    # S3 uses the configured region
    s3_client = boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    logger.info(f"AWS services initialized - SES: us-east-1, S3: {AWS_REGION}")
except Exception as e:
    ses_client = None
    s3_client = None
    logger.warning(f"AWS not configured: {e}")

def send_email(to_email, subject, body, cc_email=None):
    if cc_email:
        logger.info(f"Attempting to send email to: {to_email} (CC: {cc_email})")
    else:
        logger.info(f"Attempting to send email to: {to_email}")
    if not ses_client:
        logger.warning(f"Demo mode - Email would be sent to {to_email}")
        return False
    
    try:
        # Improved email with proper headers and text version
        text_body = f"""
        {subject}
        
        Dear Customer,
        
        This is an automated message from Bamboo Holiday Movies.
        
        Please check the HTML version of this email for full details.
        
        Best regards,
        Bamboo Holiday Movies Team
        
        ---
        This is an automated message. Please do not reply to this email.
        """
        
        destination = {'ToAddresses': [to_email]}
        if cc_email:
            destination['CcAddresses'] = [cc_email]
        
        email_params = {
            'Source': SES_FROM_EMAIL,
            'Destination': destination,
            'Message': {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': body, 'Charset': 'UTF-8'},
                    'Text': {'Data': text_body, 'Charset': 'UTF-8'}
                }
            }
        }
        
        # Only add configuration set if it exists
        config_set = os.getenv('SES_CONFIGURATION_SET')
        if config_set:
            email_params['ConfigurationSetName'] = config_set
        
        response = ses_client.send_email(**email_params)
        logger.info(f"Email sent successfully to {to_email}. MessageId: {response['MessageId']}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"SES send error: {error_message}")
        return False
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False

# Security configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Admin credentials - Simple for local development
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')  # bcrypt hash
ADMIN_PLAIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Simple for local dev

# Security
security = HTTPBearer()
ADMIN_IPS = os.getenv('ADMIN_IPS', '').split(',') if os.getenv('ADMIN_IPS') else []

# Get showtime layout for booking
def get_showtime_layout(showtime_id):
    showtime = get_showtime_by_id(showtime_id)
    if showtime:
        return {
            "showtime_id": showtime['id'],
            "rows": showtime['rows'],
            "left_cols": showtime['left_cols'],
            "right_cols": showtime['right_cols'],
            "movie": showtime['movie_title'],
            "movie_poster": showtime.get('poster_url', ''),
            "theater": showtime['theater_name'],
            "address": showtime.get('address', ''),
            "show_date": str(showtime['show_date']),
            "showtime": str(showtime['show_time']),
            "price": showtime['price'],
            "non_selectable": showtime['non_selectable_seats'] or []
        }
    return None

class BookingRequest(BaseModel):
    showtime_id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    selected_seats: List[str]
    user_id: Optional[str] = None

class SeatReservation(BaseModel):
    showtime_id: int
    seats: List[str]
    user_id: str

class OTPRequest(BaseModel):
    phone: str

class OTPVerification(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    otp: str

class AdminLogin(BaseModel):
    username: str
    password: str

class PaymentProof(BaseModel):
    booking_id: int
    payment_method: str

class MovieCreate(BaseModel):
    title: str
    poster_url: str = ""
    duration_minutes: int = 120
    genre: str = ""
    rating: str = ""
    description: str = ""

class TheaterCreate(BaseModel):
    name: str
    address: str = ""
    rows: int = 11
    left_cols: int = 8
    right_cols: int = 6
    non_selectable_seats: List[str] = []

class ShowtimeCreate(BaseModel):
    movie_id: int
    theater_id: int
    show_date: str
    show_time: str
    price: int

class AdminSettingsUpdate(BaseModel):
    admin_name: str
    admin_email: str
    notification_enabled: bool

class BookingAction(BaseModel):
    status: str
    admin_remarks: Optional[str] = None

@app.get("/")
@app.get("/api/")
def read_root():
    return {"message": "Movie Booking API"}

@app.get("/showtimes")
@app.get("/api/showtimes")
def get_all_showtimes_endpoint():
    logger.info("GET /showtimes - Request received")
    try:
        showtimes = get_all_showtimes()
        logger.info(f"GET /showtimes - Returning {len(showtimes)} showtimes")
        return showtimes
    except Exception as e:
        logger.error(f"GET /showtimes - Error: {str(e)}")
        logger.error(f"GET /showtimes - Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/showtime/{showtime_id}")
@app.get("/api/showtime/{showtime_id}")
def get_showtime_info(showtime_id: int):
    showtime_layout = get_showtime_layout(showtime_id)
    if not showtime_layout:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Get seats by status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT seats, status FROM bookings 
        WHERE showtime_id = %s AND status IN ('pending_payment', 'pending_approval', 'approved', 'confirmed')
    """, (showtime_id,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    pending_payment_seats = []
    pending_approval_seats = []
    approved_seats = []
    confirmed_seats = []
    
    logger.info(f"Showtime {showtime_id} bookings found: {len(results)}")
    for result in results:
        logger.debug(f"  Seats: {result['seats']}, Status: {result['status']}")
        if result['status'] == 'pending_payment':
            pending_payment_seats.extend(result['seats'])
        elif result['status'] == 'pending_approval':
            pending_approval_seats.extend(result['seats'])
        elif result['status'] == 'approved':
            approved_seats.extend(result['seats'])
        elif result['status'] == 'confirmed':
            confirmed_seats.extend(result['seats'])
    
    logger.info(f"Confirmed seats for showtime {showtime_id}: {confirmed_seats}")
    reserved_seat_ids = get_reserved_seats(showtime_id)
    
    return {
        **showtime_layout,
        "pending_payment_seats": pending_payment_seats,
        "pending_approval_seats": pending_approval_seats,
        "approved_seats": approved_seats, 
        "confirmed_seats": confirmed_seats,
        "reserved_seats": reserved_seat_ids
    }

@app.post("/reserve-seats")
@app.post("/api/reserve-seats")
def reserve_seats_endpoint(reservation: SeatReservation, request: Request):
    # Anti-abuse: Check IP-based limits
    client_ip = request.headers.get('x-real-ip') or request.client.host
    
    # Check current reservations by this IP
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM seat_reservations 
        WHERE user_id LIKE %s AND expires_at > NOW()
    """, (f"{client_ip}_%",))
    result = cursor.fetchone()
    current_reservations = result['count'] if result else 0
    cursor.close()
    conn.close()
    
    # Limit: Max 4 seats reserved per IP
    if current_reservations >= 4:
        raise HTTPException(status_code=429, detail="Too many seats reserved. Please complete your booking first.")
    
    # Check if seats are available
    booked_seats = get_booked_seats(reservation.showtime_id)
    reserved_by_others = check_seat_availability(reservation.showtime_id, reservation.seats, reservation.user_id)
    
    unavailable_seats = []
    for seat in reservation.seats:
        if seat in booked_seats or seat in reserved_by_others:
            unavailable_seats.append(seat)
    
    if unavailable_seats:
        raise HTTPException(status_code=400, 
                          detail=f"Seats {', '.join(unavailable_seats)} are no longer available")
    
    # Reserve seats for 5 minutes with IP tracking
    expires_at = datetime.now() + timedelta(minutes=5)
    user_id_with_ip = f"{client_ip}_{reservation.user_id}"
    reserve_seats(reservation.showtime_id, reservation.seats, user_id_with_ip, expires_at)
    
    return {"message": "Seats reserved successfully", "expires_at": expires_at.isoformat()}

@app.post("/book")
@app.post("/api/book")
def create_booking_endpoint(booking: BookingRequest):
    logger.info(f"Creating booking for showtime {booking.showtime_id}, customer: {booking.customer_name}, seats: {booking.selected_seats}")
    
    try:
        # Check if seats are still available
        booked_seats = get_booked_seats(booking.showtime_id)
        logger.info(f"Currently booked seats for showtime {booking.showtime_id}: {booked_seats}")
        
        for seat in booking.selected_seats:
            if seat in booked_seats:
                logger.error(f"Seat {seat} is already booked")
                raise HTTPException(status_code=400, detail=f"Seat {seat} is already booked")
        
        showtime_layout = get_showtime_layout(booking.showtime_id)
        if not showtime_layout:
            logger.error(f"Showtime {booking.showtime_id} not found")
            raise HTTPException(status_code=404, detail="Showtime not found")
        
        total_amount = len(booking.selected_seats) * showtime_layout["price"]
        logger.info(f"Calculated total amount: {total_amount} for {len(booking.selected_seats)} seats at {showtime_layout['price']} each")
        
        # Create booking in database
        logger.info(f"=== CREATING BOOKING ===")
        logger.info(f"Customer name: '{booking.customer_name}'")
        logger.info(f"Customer email: '{booking.customer_email}'")
        logger.info(f"Customer phone: '{booking.customer_phone}'")
        logger.info(f"Selected seats: {booking.selected_seats}")
        logger.info(f"Total amount: {total_amount}")
        
        booking_id = create_booking(
            booking.showtime_id,
            booking.customer_name,
            booking.customer_email, 
            booking.customer_phone,
            booking.selected_seats,
            total_amount
        )
        
        logger.info(f"✓ Booking created successfully: ID {booking_id}, Amount: Rp {total_amount:,}")
        logger.info(f"=== BOOKING CREATION COMPLETE ===")
        
        return {
            "booking_id": booking_id,
            "total_amount": total_amount,
            "status": "pending_payment",
            "message": "Booking created. Please upload payment proof."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_booking_endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/upload-payment/{booking_id}")
@app.post("/api/upload-payment/{booking_id}")
async def upload_payment_proof(booking_id: int, file: UploadFile = File(...)):
    logger.info(f"Upload payment proof request for booking {booking_id}, file: {file.filename}")
    
    try:
        booking = get_booking_by_id(booking_id)
        if not booking:
            logger.error(f"Booking {booking_id} not found")
            raise HTTPException(status_code=404, detail="Booking not found")
        
        logger.info(f"Processing file upload for booking {booking_id}")
        
        # Upload to S3
        try:
            file_key = f"payment-proofs/{booking_id}_{file.filename}"
            content = await file.read()
            logger.info(f"File read successfully, size: {len(content)} bytes")
            
            if s3_client:
                logger.info(f"Uploading to S3 bucket: {S3_BUCKET}, key: {file_key}")
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=file_key,
                    Body=content,
                    ContentType=file.content_type or 'image/jpeg'
                )
                file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{file_key}"
                logger.info(f"File uploaded to S3 successfully: {file_url}")
            else:
                # Fallback to local storage for development
                logger.warning("S3 client not available, using local storage")
                os.makedirs("uploads", exist_ok=True)
                file_url = f"uploads/{booking_id}_{file.filename}"
                with open(file_url, "wb") as buffer:
                    buffer.write(content)
                logger.info(f"File saved locally: {file_url}")
        except Exception as upload_error:
            logger.error(f"File upload failed: {str(upload_error)}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(upload_error)}")
        
        # Update booking with payment proof
        logger.info(f"Updating booking {booking_id} with payment proof: {file_url}")
        update_booking_payment_proof(booking_id, file_url)
        
        # Generate OTP for email verification
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=5)
        logger.info(f"=== GENERATING OTP FOR BOOKING {booking_id} ===")
        logger.info(f"Customer email from booking: '{booking['customer_email']}'")
        logger.info(f"Generated OTP: '{otp}'")
        logger.info(f"OTP expires at: {expires_at}")
        
        # Store OTP in database
        logger.info(f"Storing OTP for email: '{booking['customer_email']}'")
        store_otp(booking['customer_email'], otp, booking_id, expires_at)
        logger.info(f"✓ OTP storage completed for email: '{booking['customer_email']}'")
        logger.info(f"=== OTP GENERATION COMPLETE ===")
        
        # Get detailed booking information for email
        showtime_layout = get_showtime_layout(booking['showtime_id'])
        
        # Send OTP email with detailed booking information
        subject = f"Payment Verification Required - Booking {booking_id}"
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Payment Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                <h2 style="color: #007bff; margin-top: 0;">Payment Verification Required</h2>
                <p>Dear {booking['customer_name']},</p>
                <p>Thank you for your payment. We have received your payment proof and need to verify it.</p>
            </div>
            
            <div style="background: #ffffff; border: 1px solid #dee2e6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #495057; margin-top: 0;">Booking Information</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Booking ID:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{booking_id}</td></tr>
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Movie:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['movie'] if showtime_layout else 'N/A'}</td></tr>
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Theater:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['theater'] if showtime_layout else 'N/A'}</td></tr>
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Date:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['show_date'] if showtime_layout else 'N/A'}</td></tr>
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Time:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['showtime'] if showtime_layout else 'N/A'}</td></tr>
                    <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Seats:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{', '.join(booking['seats'])}</td></tr>
                    <tr><td style="padding: 8px 0;"><strong>Amount:</strong></td><td style="padding: 8px 0;">Rp {booking['total_amount']:,}</td></tr>
                </table>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <h3 style="color: #856404; margin-top: 0;">Verification Code</h3>
                <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 4px; margin: 15px 0;">{otp}</div>
                <p style="color: #856404; margin-bottom: 0;">This code expires in 5 minutes</p>
            </div>
            
            <p>Please enter this verification code to complete your booking process.</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 30px; font-size: 12px; color: #6c757d;">
                <p style="margin: 0;">This is an automated message from Bamboo Holiday Movies. Please do not reply to this email.</p>
                <p style="margin: 5px 0 0 0;">If you did not make this booking, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        if send_email(booking['customer_email'], subject, body):
            logger.info(f"OTP email sent successfully to {booking['customer_email']}")
            return {"message": "Payment uploaded. Check email for verification OTP.", "requires_otp": True}
        else:
            logger.warning(f"Email sending failed")
            return {"message": "Payment uploaded. Check email for verification OTP.", "requires_otp": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_payment_proof: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/booking/{booking_id}")
@app.get("/api/booking/{booking_id}")
def get_booking(booking_id: int):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(username: str) -> str:
    """Create JWT token"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin JWT token"""
    try:
        payload = verify_jwt_token(credentials.credentials)
        if payload['username'] != ADMIN_USERNAME:
            raise HTTPException(status_code=401, detail="Invalid user")
        return payload
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication required")

@app.post("/admin/login")
@app.post("/api/admin/login")
def admin_login(credentials: AdminLogin):
    logger.info(f"Admin login attempt for username: {credentials.username}")
    
    # Verify credentials
    if credentials.username != ADMIN_USERNAME:
        logger.warning(f"Invalid username attempt: {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password (hash if available, plain as fallback)
    password_valid = False
    if ADMIN_PASSWORD_HASH:
        password_valid = verify_password(credentials.password, ADMIN_PASSWORD_HASH)
    else:
        password_valid = credentials.password == ADMIN_PLAIN_PASSWORD
    
    if not password_valid:
        logger.warning(f"Invalid password attempt for user: {credentials.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(credentials.username)
    logger.info(f"Admin login successful for: {credentials.username}")
    
    return {"access_token": token, "token_type": "bearer", "expires_in": JWT_EXPIRATION_HOURS * 3600}

@app.post("/admin/logout")
@app.post("/api/admin/logout")
def admin_logout(admin: dict = Depends(get_current_admin)):
    """Logout admin user"""
    logger.info(f"Admin logout: {admin['username']}")
    return {"message": "Logged out successfully"}

@app.get("/admin/me")
@app.get("/api/admin/me")
def get_admin_info(admin: dict = Depends(get_current_admin)):
    """Get current admin user info"""
    return {"username": admin['username'], "exp": admin['exp']}

@app.get("/bookings")
@app.get("/api/bookings")
def get_all_bookings_endpoint(status: str = None, admin: dict = Depends(get_current_admin)):
    if status:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, s.show_date, s.show_time, m.title as movie_title, t.name as theater_name
            FROM bookings b
            LEFT JOIN showtimes s ON b.showtime_id = s.id
            LEFT JOIN movies m ON s.movie_id = m.id
            LEFT JOIN theaters t ON s.theater_id = t.id
            WHERE b.status = %s
            ORDER BY b.created_at DESC
        """, (status,))
        bookings = cursor.fetchall()
        cursor.close()
        conn.close()
        return bookings
    return get_all_bookings()

@app.get("/payment-proof/{booking_id}")
def get_payment_proof(booking_id: int):
    booking = get_booking_by_id(booking_id)
    if not booking or not booking.get("payment_proof"):
        raise HTTPException(status_code=404, detail="Payment proof not found")
    
    file_url = booking["payment_proof"]
    
    # If S3 URL, fetch and serve the content
    if file_url.startswith("https://") and s3_client:
        try:
            # Extract S3 key from URL
            s3_key = file_url.split(f"{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/")[1]
            
            # Get object from S3
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
            content = response['Body'].read()
            content_type = response.get('ContentType', 'image/jpeg')
            
            from fastapi.responses import Response
            return Response(content=content, media_type=content_type)
        except Exception as e:
            logger.error(f"Error fetching S3 object: {e}")
            raise HTTPException(status_code=404, detail="Payment proof not accessible")
    else:
        # Local file fallback
        from fastapi.responses import FileResponse
        return FileResponse(file_url)

@app.post("/verify-payment-otp")
@app.post("/api/verify-payment-otp")
def verify_payment_otp(request: OTPVerification):
    logger.info(f"=== OTP VERIFICATION START ===")
    logger.info(f"Raw request data - Email: '{request.email}', Phone: '{request.phone}', OTP: '{request.otp}'")
    logger.info(f"Email is None: {request.email is None}, Email is empty: {request.email == ''}")
    logger.info(f"Phone is None: {request.phone is None}, Phone is empty: {request.phone == ''}")
    
    # Handle both email and phone for backward compatibility
    if request.email and request.email.strip():
        email = request.email.strip()
        logger.info(f"✓ Using email field: '{email}'")
    elif request.phone and request.phone.strip():
        phone_value = request.phone.strip()
        logger.info(f"Processing phone field: '{phone_value}'")
        
        # Check if phone field actually contains an email
        if '@' in phone_value:
            email = phone_value
            logger.info(f"✓ Phone field contains email: '{email}'")
        else:
            # Look up email by phone
            logger.info(f"Looking up email by phone: '{phone_value}'")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT customer_email FROM bookings WHERE customer_phone = %s ORDER BY created_at DESC LIMIT 1", (phone_value,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                logger.error(f"❌ No booking found for phone: '{phone_value}'")
                raise HTTPException(status_code=400, detail="No booking found for this phone number")
            email = result['customer_email']
            logger.info(f"✓ Found email by phone lookup: '{email}'")
    else:
        logger.error(f"❌ Both email and phone are empty or None")
        logger.error(f"Request email: '{request.email}' (type: {type(request.email)})")
        logger.error(f"Request phone: '{request.phone}' (type: {type(request.phone)})")
        raise HTTPException(status_code=400, detail="Either email or phone is required")
    
    logger.info(f"Attempting to verify OTP for email: '{email}' with OTP: '{request.otp}'")
    booking_id = verify_otp(email, request.otp)
    logger.info(f"OTP verification result - Booking ID: {booking_id}")
    
    if not booking_id:
        logger.error(f"❌ OTP verification failed for email: '{email}' with OTP: '{request.otp}'")
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    logger.info(f"✓ OTP verification successful for booking ID: {booking_id}")
    
    # Update booking to pending approval
    update_booking_status(booking_id, "pending_approval")
    
    # Get booking details for admin notification
    booking = get_booking_by_id(booking_id)
    showtime_layout = get_showtime_layout(booking['showtime_id']) if booking else None
    
    # Send admin notification
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_email FROM admin_settings ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        admin_email = result['admin_email'] if result else os.getenv('ADMIN_EMAIL', 'keralasamajam.indonesia@gmail.com')
        cursor.close()
        conn.close()
    except:
        admin_email = os.getenv('ADMIN_EMAIL', 'keralasamajam.indonesia@gmail.com')
    
    if booking and showtime_layout:
        admin_subject = f"Payment Verified - Booking #{booking_id} Needs Approval"
        admin_body = f"""
        <h2>🔔 Payment Verified - Action Required</h2>
        <p>A customer has verified their payment and the booking is now pending your approval.</p>
        
        <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>Booking Information:</h3>
            <p><strong>Booking ID:</strong> {booking_id}</p>
            <p><strong>Customer:</strong> {booking['customer_name']}</p>
            <p><strong>Email:</strong> {booking['customer_email']}</p>
            <p><strong>Phone:</strong> {booking['customer_phone']}</p>
            <p><strong>Movie:</strong> {showtime_layout['movie']}</p>
            <p><strong>Theater:</strong> {showtime_layout['theater']}</p>
            <p><strong>Date:</strong> {showtime_layout['show_date']}</p>
            <p><strong>Time:</strong> {showtime_layout['showtime']}</p>
            <p><strong>Seats:</strong> {', '.join(booking['seats'])}</p>
            <p><strong>Amount:</strong> Rp {booking['total_amount']:,}</p>
            <p><strong>Status:</strong> Pending Approval</p>
        </div>
        
        <p>Please review the payment proof and approve or reject this booking.</p>
        <p><a href="http://localhost:3000/admin" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Admin Panel</a></p>
        """
        
        send_email(admin_email, admin_subject, admin_body)
    
    return {"message": "Payment verified. Admin has been notified for approval."}

@app.put("/booking/{booking_id}/action")
@app.put("/api/booking/{booking_id}/action")
def update_booking_action_endpoint(booking_id: int, action: BookingAction, admin: dict = Depends(get_current_admin)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    valid_statuses = ["pending_payment", "pending_verification", "pending_approval", "approved", "confirmed", "cancelled", "admin_rejected"]
    if action.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    old_status = booking["status"]
    updated_booking = update_booking_status(booking_id, action.status, action.admin_remarks)
    status = action.status
    
    return {"message": f"Booking status updated from {old_status} to {status}"}

@app.put("/booking/{booking_id}/status")
@app.put("/api/booking/{booking_id}/status")
def update_booking_status_endpoint(booking_id: int, status: str, admin: dict = Depends(get_current_admin)):
    """Legacy endpoint for backward compatibility"""
    action = BookingAction(status=status)
    return update_booking_action_endpoint(booking_id, action, admin)

# Send email notification on status change helper
def send_status_change_email(booking_id, status, old_status):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return
    if status in ["approved", "confirmed", "cancelled", "admin_rejected"]:
        # Get showtime info for email
        showtime_layout = get_showtime_layout(booking['showtime_id']) if booking else None
        
        if status == "approved" and showtime_layout:
            subject = f"🎬 Booking Confirmed - #{booking_id}"
            body = f"""
            <h2>🎬 Booking Confirmed!</h2>
            <p>Dear {booking['customer_name']},</p>
            <p>Your movie booking has been approved and confirmed!</p>
            
            <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3>Booking Details:</h3>
                <p><strong>Booking ID:</strong> {booking_id}</p>
                <p><strong>Movie:</strong> {showtime_layout['movie']}</p>
                <p><strong>Theater:</strong> {showtime_layout['theater']}</p>
                <p><strong>Date:</strong> {showtime_layout['show_date']}</p>
                <p><strong>Time:</strong> {showtime_layout['showtime']}</p>
                <p><strong>Seats:</strong> {', '.join(booking['seats'])}</p>
                <p><strong>Total Amount:</strong> Rp {booking['total_amount']:,}</p>
            </div>
            
            <p>Your tickets are confirmed! Enjoy the movie! 🍿</p>
            """
        elif status == "admin_rejected":
            subject = f"❌ Booking Rejected - #{booking_id}"
            body = f"""
            <h2>Booking Rejected</h2>
            <p>Dear {booking['customer_name']},</p>
            <p>Unfortunately, your booking has been rejected by admin.</p>
            <p><strong>Booking ID:</strong> {booking_id}</p>
            <p><strong>Seats:</strong> {', '.join(booking['seats'])}</p>
            <p>The seats are now available for others to book.</p>
            <p>You can try booking again if needed.</p>
            """
        # Remove cancelled status handling since we use admin_rejected
        
        admin_email = os.getenv('ADMIN_EMAIL', 'justinmathewbiji@gmail.com')
        send_email(booking['customer_email'], subject, body, admin_email)

# Call email notification after status update
    send_status_change_email(booking_id, status, old_status)

@app.post("/booking/{booking_id}/resend-email")
@app.post("/api/booking/{booking_id}/resend-email")
def resend_confirmation_email(booking_id: int, admin: dict = Depends(get_current_admin)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != "approved":
        raise HTTPException(status_code=400, detail="Can only resend confirmation for approved bookings")
    
    # Get showtime info for email
    showtime_layout = get_showtime_layout(booking['showtime_id'])
    
    # Get admin email (same pattern as OTP verification)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_email FROM admin_settings ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        admin_email = result['admin_email'] if result else os.getenv('ADMIN_EMAIL', 'keralasamajam.indonesia@gmail.com')
        cursor.close()
        conn.close()
    except:
        admin_email = os.getenv('ADMIN_EMAIL', 'keralasamajam.indonesia@gmail.com')
    
    if not showtime_layout:
        raise HTTPException(status_code=404, detail="Showtime information not found")
    
    subject = f"Booking Confirmed - Reference {booking_id}"
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Booking Confirmed</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #155724; margin-top: 0;">Booking Confirmed</h2>
            <p>Dear {booking['customer_name']},</p>
            <p>Your movie booking has been confirmed.</p>
        </div>
        
        <div style="background: #ffffff; border: 1px solid #dee2e6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #495057; margin-top: 0;">Your Ticket Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Booking Reference:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{booking_id}</td></tr>
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Movie:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['movie']}</td></tr>
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Cinema:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['theater']}</td></tr>
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Show Date:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['show_date']}</td></tr>
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Show Time:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{showtime_layout['showtime']}</td></tr>
                <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Seat Numbers:</strong></td><td style="padding: 8px 0; border-bottom: 1px solid #eee;">{', '.join(booking['seats'])}</td></tr>
                <tr><td style="padding: 8px 0;"><strong>Total Paid:</strong></td><td style="padding: 8px 0;">Rp {booking['total_amount']:,}</td></tr>
            </table>
        </div>
        
        <p>Thank you for choosing Bamboo Holiday Movies. Enjoy your movie experience!</p>
    </body>
    </html>
    """
    
    logger.info(f"Resending confirmation email for booking {booking_id} to {booking['customer_email']} with admin CC: {admin_email}")
    
    if send_email(booking['customer_email'], subject, body, admin_email):
        return {"message": "Confirmation email resent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to resend confirmation email")

@app.get("/bookings/stats")
@app.get("/api/bookings/stats")
def get_booking_stats(admin: dict = Depends(get_current_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM bookings
        GROUP BY status
    """)
    stats = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return {stat['status']: stat['count'] for stat in stats}

@app.get("/analytics")
@app.get("/api/analytics")
def get_analytics_endpoint():
    analytics = get_analytics()
    
    # Calculate occupancy rate considering disabled seats
    confirmed_seats = analytics.get('confirmed_bookings', 0)
    
    # Get total available seats across all active showtimes (excluding disabled seats)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_shows,
            COALESCE(SUM(array_length(t.non_selectable_seats, 1)), 0) as total_disabled_seats
        FROM showtimes s
        JOIN theaters t ON s.theater_id = t.id
        WHERE s.is_active = TRUE
    """)
    result = cursor.fetchone()
    total_shows = result['total_shows'] if result else 0
    total_disabled_seats = result['total_disabled_seats'] if result else 0
    cursor.close()
    conn.close()
    
    # Calculate available seats (154 per theater minus disabled seats)
    seats_per_theater = 154
    total_available_seats = (total_shows * seats_per_theater) - total_disabled_seats
    occupancy_rate = (confirmed_seats / total_available_seats * 100) if total_available_seats > 0 else 0
    
    return {
        **analytics,
        "occupancy_rate": occupancy_rate
    }

@app.get("/download-ticket/{booking_id}")
def download_ticket(booking_id: int):
    """Download PDF ticket for confirmed booking"""
    raise HTTPException(status_code=501, detail="Ticket generation temporarily disabled")

# Admin management endpoints
@app.get("/admin/movies")
@app.get("/api/admin/movies")
def get_movies():
    return get_all_movies()

@app.get("/test")
def test_endpoint():
    return {"message": "Test endpoint working"}

@app.post("/admin/movies")
@app.post("/api/admin/movies")
def create_movie_endpoint(movie: MovieCreate):
    movie_id = create_movie(
        movie.title, movie.poster_url, movie.duration_minutes,
        movie.genre, movie.rating, movie.description
    )
    return {"message": "Movie created successfully", "id": movie_id}

@app.put("/admin/movies/{movie_id}")
def update_movie_endpoint(movie_id: int, movie: MovieCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE movies SET title = %s, poster_url = %s, duration_minutes = %s, 
        genre = %s, rating = %s, description = %s
        WHERE id = %s
    """, (movie.title, movie.poster_url, movie.duration_minutes, 
           movie.genre, movie.rating, movie.description, movie_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Movie updated successfully"}

@app.delete("/admin/movies/{movie_id}")
def delete_movie_endpoint(movie_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE movies SET is_active = FALSE WHERE id = %s", (movie_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Movie deleted successfully"}

@app.get("/admin/theaters")
@app.get("/api/admin/theaters")
def get_theaters():
    return get_all_theaters()

@app.post("/admin/theaters")
@app.post("/api/admin/theaters")
def create_theater_endpoint(theater: TheaterCreate):
    theater_id = create_theater(
        theater.name, theater.address, theater.rows,
        theater.left_cols, theater.right_cols, theater.non_selectable_seats
    )
    return {"message": "Theater created successfully", "id": theater_id}

@app.put("/admin/theaters/{theater_id}")
def update_theater(theater_id: int, theater: TheaterCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE theaters SET name = %s, address = %s, rows = %s, 
        left_cols = %s, right_cols = %s, non_selectable_seats = %s
        WHERE id = %s
    """, (theater.name, theater.address, theater.rows, 
           theater.left_cols, theater.right_cols, theater.non_selectable_seats, theater_id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Theater updated successfully"}

@app.delete("/admin/theaters/{theater_id}")
def delete_theater(theater_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE theaters SET is_active = FALSE WHERE id = %s", (theater_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Theater deleted successfully"}

@app.get("/admin/showtimes")
@app.get("/api/admin/showtimes")
def get_admin_showtimes():
    return get_all_showtimes()

@app.post("/admin/showtimes")
@app.post("/api/admin/showtimes")
def create_showtime_endpoint(showtime: ShowtimeCreate):
    showtime_id = create_showtime(
        showtime.movie_id, showtime.theater_id,
        showtime.show_date, showtime.show_time, showtime.price
    )
    return {"message": "Showtime created successfully", "id": showtime_id}

@app.delete("/admin/showtimes/{showtime_id}")
def delete_showtime(showtime_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE showtimes SET is_active = FALSE WHERE id = %s", (showtime_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Showtime deleted successfully"}

# Admin settings endpoints
@app.get("/admin/settings")
@app.get("/api/admin/settings")
def get_admin_settings_endpoint():
    """Get admin settings"""
    settings = get_admin_settings()
    
    if settings:
        return settings
    else:
        # Return default settings
        return {
            "admin_email": "keralasamajam.indonesia@gmail.com",
            "admin_name": "Admin",
            "notification_enabled": True
        }

@app.put("/admin/settings")
@app.put("/api/admin/settings")
def update_admin_settings_endpoint(settings: AdminSettingsUpdate):
    """Update admin settings"""
    update_admin_settings(
        settings.admin_name,
        settings.admin_email,
        settings.notification_enabled
    )
    
    return {"message": "Admin settings updated successfully"}

# Serve React static files at the end - only for production
# Comment this out for development to avoid conflicts with API routes
# if os.path.exists("static"):
#     app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
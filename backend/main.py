from fastapi import FastAPI, HTTPException, UploadFile, File
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

def send_email(to_email, subject, body):
    logger.info(f"Attempting to send email to: {to_email}")
    if not ses_client:
        logger.warning(f"Demo mode - Email would be sent to {to_email}")
        return False
    
    try:
        response = ses_client.send_email(
            Source=SES_FROM_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}
            }
        )
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

# Admin credentials - MUST be set in environment variables for production
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')  # bcrypt hash
ADMIN_PLAIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'BambooMovies2024!@#')  # fallback for dev

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

@app.get("/")
def read_root():
    return {"message": "Movie Booking API"}

@app.get("/showtimes")
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
def get_showtime_info(showtime_id: int):
    showtime_layout = get_showtime_layout(showtime_id)
    if not showtime_layout:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    # Get seats by status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT seats, status FROM bookings 
        WHERE showtime_id = %s AND status IN ('pending_approval', 'approved', 'confirmed')
    """, (showtime_id,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    pending_approval_seats = []
    approved_seats = []
    confirmed_seats = []
    
    logger.info(f"Showtime {showtime_id} bookings found: {len(results)}")
    for result in results:
        logger.debug(f"  Seats: {result['seats']}, Status: {result['status']}")
        if result['status'] == 'pending_approval':
            pending_approval_seats.extend(result['seats'])
        elif result['status'] == 'approved':
            approved_seats.extend(result['seats'])
        elif result['status'] == 'confirmed':
            confirmed_seats.extend(result['seats'])
    
    logger.info(f"Confirmed seats for showtime {showtime_id}: {confirmed_seats}")
    reserved_seat_ids = get_reserved_seats(showtime_id)
    
    return {
        **showtime_layout,
        "pending_approval_seats": pending_approval_seats,
        "approved_seats": approved_seats, 
        "confirmed_seats": confirmed_seats,
        "reserved_seats": reserved_seat_ids
    }

@app.post("/reserve-seats")
def reserve_seats_endpoint(reservation: SeatReservation):
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
    
    # Reserve seats for 10 minutes
    expires_at = datetime.now() + timedelta(minutes=10)
    reserve_seats(reservation.showtime_id, reservation.seats, reservation.user_id, expires_at)
    
    return {"message": "Seats reserved successfully", "expires_at": expires_at.isoformat()}

@app.post("/book")
def create_booking_endpoint(booking: BookingRequest):
    logger.info(f"Creating booking for showtime {booking.showtime_id}, customer: {booking.customer_name}, seats: {booking.selected_seats}")
    # Check if seats are still available
    booked_seats = get_booked_seats(booking.showtime_id)
    
    for seat in booking.selected_seats:
        if seat in booked_seats:
            raise HTTPException(status_code=400, detail=f"Seat {seat} is already booked")
    
    showtime_layout = get_showtime_layout(booking.showtime_id)
    if not showtime_layout:
        raise HTTPException(status_code=404, detail="Showtime not found")
    
    total_amount = len(booking.selected_seats) * showtime_layout["price"]
    
    # Create booking in database
    booking_id = create_booking(
        booking.showtime_id,
        booking.customer_name,
        booking.customer_email, 
        booking.customer_phone,
        booking.selected_seats,
        total_amount
    )
    
    logger.info(f"Booking created successfully: ID {booking_id}, Amount: Rp {total_amount:,}")
    
    return {
        "booking_id": booking_id,
        "total_amount": total_amount,
        "status": "pending_payment",
        "message": "Booking created. Please upload payment proof."
    }

@app.post("/upload-payment/{booking_id}")
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
        logger.info(f"Generated OTP for booking {booking_id}: {otp}")
        
        # Store OTP in database
        store_otp(booking['customer_email'], otp, booking_id, expires_at)
        logger.info(f"OTP stored for email: {booking['customer_email']}")
        
        # Get detailed booking information for email
        showtime_layout = get_showtime_layout(booking['showtime_id'])
        
        # Send OTP email with detailed booking information
        subject = f"Payment Verification - Booking #{booking_id}"
        body = f"""
        <h2>🎬 Payment Verification Required</h2>
        <p>Dear {booking['customer_name']},</p>
        <p>Your payment proof has been uploaded successfully for the following booking:</p>
        
        <div style="background: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3>📋 Booking Details:</h3>
            <p><strong>Booking ID:</strong> #{booking_id}</p>
            <p><strong>Movie:</strong> {showtime_layout['movie'] if showtime_layout else 'N/A'}</p>
            <p><strong>Theater:</strong> {showtime_layout['theater'] if showtime_layout else 'N/A'}</p>
            <p><strong>Address:</strong> {showtime_layout.get('address', 'N/A') if showtime_layout else 'N/A'}</p>
            <p><strong>Show Date:</strong> {showtime_layout['show_date'] if showtime_layout else 'N/A'}</p>
            <p><strong>Show Time:</strong> {showtime_layout['showtime'] if showtime_layout else 'N/A'}</p>
            <p><strong>Selected Seats:</strong> {', '.join(booking['seats'])}</p>
            <p><strong>Total Amount:</strong> Rp {booking['total_amount']:,}</p>
        </div>
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>🔐 Verification OTP:</strong> <span style="font-size: 24px; font-weight: bold; color: #007bff;">{otp}</span></p>
            <p><em>This OTP is valid for 5 minutes only.</em></p>
        </div>
        
        <p>Please enter this OTP to verify your payment and proceed with booking confirmation.</p>
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
def admin_logout(admin: dict = Depends(get_current_admin)):
    """Logout admin user"""
    logger.info(f"Admin logout: {admin['username']}")
    return {"message": "Logged out successfully"}

@app.get("/admin/me")
def get_admin_info(admin: dict = Depends(get_current_admin)):
    """Get current admin user info"""
    return {"username": admin['username'], "exp": admin['exp']}

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

@app.get("/bookings")
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
    
    # If S3 URL, redirect to S3
    if file_url.startswith("https://"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=file_url)
    else:
        # Local file fallback
        from fastapi.responses import FileResponse
        return FileResponse(file_url)

@app.post("/verify-payment-otp")
def verify_payment_otp(request: OTPVerification):
    logger.info(f"OTP verification request - Email: {request.email}, Phone: {request.phone}, OTP: {request.otp}")
    
    # Handle both email and phone for backward compatibility
    if request.email:
        email = request.email
        logger.info(f"Using email field: {email}")
    elif request.phone:
        # Check if phone field actually contains an email
        if '@' in request.phone:
            email = request.phone
            logger.info(f"Phone field contains email: {email}")
        else:
            # Look up email by phone
            logger.info(f"Looking up email by phone: {request.phone}")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT customer_email FROM bookings WHERE customer_phone = %s ORDER BY created_at DESC LIMIT 1", (request.phone,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                logger.error(f"No booking found for phone: {request.phone}")
                raise HTTPException(status_code=400, detail="No booking found for this phone number")
            email = result['customer_email']
            logger.info(f"Found email by phone lookup: {email}")
    else:
        raise HTTPException(status_code=400, detail="Either email or phone is required")
    
    booking_id = verify_otp(email, request.otp)
    
    if not booking_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
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
        admin_email = result['admin_email'] if result else os.getenv('ADMIN_EMAIL', 'admin@bambooholiday.com')
        cursor.close()
        conn.close()
    except:
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@bambooholiday.com')
    
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

@app.put("/booking/{booking_id}/status")
def update_booking_status_endpoint(booking_id: int, status: str, admin: dict = Depends(get_current_admin)):
    booking = get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    valid_statuses = ["pending_approval", "approved", "confirmed", "cancelled", "admin_rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    old_status = booking["status"]
    updated_booking = update_booking_status(booking_id, status)
    
    # Send email notification on status change
    if status in ["approved", "confirmed", "cancelled", "admin_rejected"]:
        # Get showtime info for email
        booking_detail = get_booking_by_id(booking_id)
        showtime_layout = get_showtime_layout(booking_detail['showtime_id']) if booking_detail else None
        
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
        
        send_email(booking['customer_email'], subject, body)
    
    return {"message": f"Booking status updated from {old_status} to {status}"}

@app.get("/bookings/stats")
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
def get_analytics_endpoint():
    analytics = get_analytics()
    
    # Calculate occupancy rate
    total_seats = 11 * (8 + 6)  # 11 rows * 14 seats
    bookings_data = get_all_bookings()
    occupied_seats = sum(len(b["seats"]) for b in bookings_data if b["status"] in ["confirmed", "approved"])
    occupancy_rate = (occupied_seats / total_seats) * 100
    
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
def get_movies():
    return get_all_movies()

@app.get("/test")
def test_endpoint():
    return {"message": "Test endpoint working"}

@app.post("/admin/movies")
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
def get_theaters():
    return get_all_theaters()

@app.post("/admin/theaters")
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
def get_admin_showtimes():
    return get_all_showtimes()

@app.post("/admin/showtimes")
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
def get_admin_settings_endpoint():
    """Get admin settings"""
    settings = get_admin_settings()
    
    if settings:
        return settings
    else:
        # Return default settings
        return {
            "admin_email": "admin@bambooholiday.com",
            "admin_name": "Admin",
            "notification_enabled": True
        }

@app.put("/admin/settings")
def update_admin_settings_endpoint(settings: AdminSettingsUpdate):
    """Update admin settings"""
    update_admin_settings(
        settings.admin_name,
        settings.admin_email,
        settings.notification_enabled
    )
    
    return {"message": "Admin settings updated successfully"}

# Serve React static files at the end
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# Booking operations
def create_booking(showtime_id, customer_name, customer_email, customer_phone, seats, total_amount):
    """Create new booking in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO bookings (showtime_id, customer_name, customer_email, customer_phone, seats, total_amount, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (showtime_id, customer_name, customer_email, customer_phone, seats, total_amount, 'pending_payment'))
    
    booking_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    
    return booking_id

def get_all_bookings():
    """Get all bookings from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC")
    bookings = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [dict(booking) for booking in bookings]

def get_booking_by_id(booking_id):
    """Get booking by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
    booking = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return dict(booking) if booking else None

def update_booking_status(booking_id, status):
    """Update booking status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE bookings SET status = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        RETURNING *
    """, (status, booking_id))
    
    booking = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return dict(booking) if booking else None

def update_booking_payment_proof(booking_id, file_path):
    """Update booking with payment proof"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE bookings SET payment_proof = %s, status = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE id = %s
        RETURNING *
    """, (file_path, 'pending_verification', booking_id))
    
    booking = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    
    return dict(booking) if booking else None

def get_booked_seats(showtime_id):
    """Get all booked seats for a specific showtime"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT seats FROM bookings 
        WHERE showtime_id = %s AND status IN ('pending_payment', 'pending_verification', 'pending_approval', 'approved', 'confirmed')
    """, (showtime_id,))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    booked_seats = []
    for result in results:
        booked_seats.extend(result['seats'])
    
    return booked_seats

# OTP operations
def store_otp(email, otp, booking_id, expires_at):
    """Store OTP in database"""
    import logging
    logger = logging.getLogger('movies-api')
    
    logger.info(f"=== STORING OTP ===")
    logger.info(f"Email: '{email}', OTP: '{otp}', Booking ID: {booking_id}, Expires: {expires_at}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete existing OTP for this email
    cursor.execute("DELETE FROM otp_storage WHERE email = %s", (email,))
    deleted_count = cursor.rowcount
    logger.info(f"Deleted {deleted_count} existing OTP records for email: '{email}'")
    
    # Insert new OTP
    cursor.execute("""
        INSERT INTO otp_storage (email, otp, booking_id, expires_at)
        VALUES (%s, %s, %s, %s)
    """, (email, otp, booking_id, expires_at))
    
    conn.commit()
    logger.info(f"✓ OTP stored successfully for email: '{email}'")
    
    # Verify it was stored
    cursor.execute("SELECT * FROM otp_storage WHERE email = %s", (email,))
    stored_otp = cursor.fetchone()
    if stored_otp:
        logger.info(f"✓ Verification: OTP found in database - email='{stored_otp['email']}', otp='{stored_otp['otp']}', booking_id={stored_otp['booking_id']}")
    else:
        logger.error(f"✗ Verification failed: OTP not found in database after insert")
    
    cursor.close()
    conn.close()
    logger.info(f"=== OTP STORAGE COMPLETE ===")

def verify_otp(email, otp):
    """Verify OTP and return booking_id if valid"""
    import logging
    logger = logging.getLogger('movies-api')
    
    logger.info(f"=== OTP DATABASE VERIFICATION ===")
    logger.info(f"Searching for email: '{email}' with OTP: '{otp}'")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, let's see what OTPs exist for this email
    cursor.execute("SELECT * FROM otp_storage WHERE email = %s", (email,))
    all_otps = cursor.fetchall()
    logger.info(f"Found {len(all_otps)} OTP records for email '{email}'")
    
    for i, otp_record in enumerate(all_otps):
        logger.info(f"OTP {i+1}: email='{otp_record['email']}', otp='{otp_record['otp']}', booking_id={otp_record['booking_id']}, expires_at={otp_record['expires_at']}")
        logger.info(f"OTP {i+1}: Current time vs expires_at = {datetime.now()} vs {otp_record['expires_at']}")
        logger.info(f"OTP {i+1}: Is expired? {otp_record['expires_at'] <= datetime.now()}")
    
    # Now try the actual verification
    cursor.execute("""
        SELECT booking_id, expires_at FROM otp_storage 
        WHERE email = %s AND otp = %s AND expires_at > CURRENT_TIMESTAMP
    """, (email, otp))
    
    result = cursor.fetchone()
    logger.info(f"OTP verification query result: {result}")
    
    if result:
        logger.info(f"✓ OTP verification successful! Booking ID: {result['booking_id']}")
        # Delete used OTP
        cursor.execute("DELETE FROM otp_storage WHERE email = %s", (email,))
        conn.commit()
        booking_id = result['booking_id']
        logger.info(f"✓ Deleted used OTP for email: '{email}'")
    else:
        logger.error(f"✗ OTP verification failed for email: '{email}' with OTP: '{otp}'")
        # Let's also check if there's an OTP with wrong code or expired
        cursor.execute("SELECT * FROM otp_storage WHERE email = %s", (email,))
        existing_otps = cursor.fetchall()
        if existing_otps:
            for existing in existing_otps:
                if existing['otp'] != otp:
                    logger.error(f"✗ Wrong OTP code. Expected: '{existing['otp']}', Got: '{otp}'")
                if existing['expires_at'] <= datetime.now():
                    logger.error(f"✗ OTP expired. Expires at: {existing['expires_at']}, Current: {datetime.now()}")
        else:
            logger.error(f"✗ No OTP found for email: '{email}'")
        booking_id = None
    
    cursor.close()
    conn.close()
    
    logger.info(f"=== OTP VERIFICATION END - Result: {booking_id} ===")
    return booking_id

# Seat reservation operations
def reserve_seats(showtime_id, seats, user_id, expires_at):
    """Reserve seats temporarily"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clean expired reservations
    cursor.execute("DELETE FROM seat_reservations WHERE expires_at < CURRENT_TIMESTAMP")
    
    # Remove existing reservations for this user
    cursor.execute("DELETE FROM seat_reservations WHERE user_id = %s", (user_id,))
    
    # Add new reservations
    for seat in seats:
        cursor.execute("""
            INSERT INTO seat_reservations (showtime_id, seat_id, user_id, expires_at)
            VALUES (%s, %s, %s, %s)
        """, (showtime_id, seat, user_id, expires_at))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_reserved_seats(showtime_id):
    """Get currently reserved seats for a specific showtime"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clean expired reservations first
    cursor.execute("DELETE FROM seat_reservations WHERE expires_at < CURRENT_TIMESTAMP")
    
    cursor.execute("SELECT seat_id FROM seat_reservations WHERE showtime_id = %s", (showtime_id,))
    results = cursor.fetchall()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return [result['seat_id'] for result in results]

def check_seat_availability(showtime_id, seats, user_id):
    """Check if seats are available for booking"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check reservations
    cursor.execute("""
        SELECT seat_id FROM seat_reservations 
        WHERE showtime_id = %s AND seat_id = ANY(%s) AND user_id != %s AND expires_at > CURRENT_TIMESTAMP
    """, (showtime_id, seats, user_id))
    
    reserved_by_others = [row['seat_id'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return reserved_by_others

# Analytics
def get_analytics():
    """Get booking analytics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bookings,
            SUM(CASE WHEN status IN ('confirmed', 'approved') THEN total_amount ELSE 0 END) as total_revenue,
            COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_bookings,
            COUNT(CASE WHEN status = 'pending_payment' THEN 1 END) as pending_bookings,
            COUNT(CASE WHEN status = 'pending_approval' THEN 1 END) as pending_approval,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_bookings
        FROM bookings
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return dict(result)

# Theater configuration
# Movies management
def get_all_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE is_active = TRUE ORDER BY title")
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(movie) for movie in movies]

def create_movie(title, poster_url, duration_minutes, genre, rating, description=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO movies (title, poster_url, duration_minutes, genre, rating, description)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (title, poster_url, duration_minutes, genre, rating, description))
    movie_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return movie_id

# Theaters management
def get_all_theaters():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM theaters WHERE is_active = TRUE ORDER BY name")
    theaters = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(theater) for theater in theaters]

def create_theater(name, address, rows, left_cols, right_cols, non_selectable_seats):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO theaters (name, address, rows, left_cols, right_cols, non_selectable_seats)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (name, address, rows, left_cols, right_cols, non_selectable_seats))
    theater_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return theater_id

# Showtimes management
def get_all_showtimes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, m.title as movie_title, m.poster_url, t.name as theater_name, t.address
        FROM showtimes s
        JOIN movies m ON s.movie_id = m.id
        JOIN theaters t ON s.theater_id = t.id
        WHERE s.is_active = TRUE
        ORDER BY s.show_date, s.show_time
    """)
    showtimes = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(showtime) for showtime in showtimes]

def create_showtime(movie_id, theater_id, show_date, show_time, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO showtimes (movie_id, theater_id, show_date, show_time, price)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (movie_id, theater_id, show_date, show_time, price))
    showtime_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return showtime_id

def get_showtime_by_id(showtime_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, m.title as movie_title, m.poster_url, 
               t.name as theater_name, t.address, t.rows, t.left_cols, t.right_cols, t.non_selectable_seats
        FROM showtimes s
        JOIN movies m ON s.movie_id = m.id
        JOIN theaters t ON s.theater_id = t.id
        WHERE s.id = %s
    """, (showtime_id,))
    showtime = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(showtime) if showtime else None

def get_admin_settings():
    """Get admin settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admin_settings ORDER BY id DESC LIMIT 1")
    settings = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return dict(settings) if settings else None

def update_admin_settings(admin_name, admin_email, notification_enabled):
    """Update admin settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if settings exist
    cursor.execute("SELECT id FROM admin_settings ORDER BY id DESC LIMIT 1")
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE admin_settings SET 
            admin_name = %s, admin_email = %s, notification_enabled = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (admin_name, admin_email, notification_enabled, existing['id']))
    else:
        cursor.execute("""
            INSERT INTO admin_settings (admin_name, admin_email, notification_enabled)
            VALUES (%s, %s, %s)
        """, (admin_name, admin_email, notification_enabled))
    
    conn.commit()
    cursor.close()
    conn.close()